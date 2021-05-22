import boto3, uuid, schedule, time, json, ast, picamera, os, smtplib
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timezone, timedelta
from math import trunc
from copy import deepcopy
from gpiozero import LED, Button, Buzzer, TonalBuzzer, AngularServo, Servo
from gpiozero.tones import Tone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Constants for AWS resources and photo storage
USERNAME = ''
MACHINE_CODE = '100'
MED_TABLE_NAME = 'Medication-5e4hsavprbbmrnct6wv2he3pcy-staging'
TIME_TABLE_NAME = 'TimeSlots-5e4hsavprbbmrnct6wv2he3pcy-staging'
VERIFICATION_TABLE_NAME = 'Verification-5e4hsavprbbmrnct6wv2he3pcy-staging'
DISP_TABLE_NAME = 'Dispense-5e4hsavprbbmrnct6wv2he3pcy-staging'
EMAIL_TABLE_NAME = 'usernameEmailMatcher-5e4hsavprbbmrnct6wv2he3pcy-staging'
MACHINE_CODE_TABLE_NAME = 'UsernameMachineMatcher-5e4hsavprbbmrnct6wv2he3pcy-staging'
VERIFICATION_BUCKET_NAME = 'finalmeddisp76f4f905914d42a8829a9b70cb8986e2222054-staging'
ACCESS_ID = 'AKIA2WX5HT4VPZYIT5FD'
SECRET = '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'
PHOTO_PATH = 'VerificationPhotos/'
PIPATH = os.path.dirname(__file__)

NOTIFICATION_EMAIL = 'rania.smart.medication.dispenser@gmail.com'
NOTIFICATION_EMAIL_PASS = 'baronpizza34$'

# Initializing connection with AWS resources
session = boto3.Session(
    aws_access_key_id=ACCESS_ID,
    aws_secret_access_key=SECRET
    )
db = session.resource('dynamodb')
s3 = session.resource('s3')

curr_meds = []
curr_times = {'slot1': '', 'slot2': '', 'slot3': ''}
old_times = {}
meds_for_each_time = [[],[],[]]

disp_jobs = []
disp_jobs_order = []
disp_jobs_status = {'slot1': '', 'slot2': '', 'slot3': ''}
disp_fails = []

email = ''

#Declaring GPIO
limit_switch = Button(14)
limit_bool = True
dispense_button = Button(15)
reset_button = Button(16)
servo = Servo(17)
servo.value = None
green_led = LED(27)
red_led = LED(22)
system_on_led = LED(26)
cam = picamera.PiCamera()
cam.vflip = True
cam.resolution = (480,640)
buzzer1 = Buzzer(18)
buzzer2 = Buzzer(23)

# Servo pos file init read
file = open(os.path.join(PIPATH, 'servo_pos.txt'), 'r+')
servo_pos = int(file.readline())

export_file = open(os.path.join(PIPATH, 'data_log.json'), 'a')


# Responsible for telling the servo when it has incremented to another cell.
# This function is binded to the 'limit_switch' variable.
def trigger():
    global limit_bool
    limit_bool = False
# Binding 'limit_switch' to 'trigger()'
limit_switch.when_pressed = trigger


# Solely used to handle startup aesthetics
def startup_sequence():
    # System on led
    system_on_led.on()

    # Startup sound
    buzzer1.beep(on_time=2,off_time=0,n=1)
    buzzer2.beep(on_time=2,off_time=0,n=1)

    # Startup led pattern
    for i in range(2):
        red_led.on()
        green_led.on()
        time.sleep(1)
        red_led.off()
        green_led.off()
        time.sleep(1)


# Increments the servo_pos variable and then 
def increment_servo_pos():
    global servo_pos
    servo_pos += 1
    if(servo_pos >= 23):
        servo_pos = 1
    file.seek(0)
    file.write(str(servo_pos))
    file.truncate()


# Increments the magazine carousel by one.
def next_cell():
    global limit_bool
    limit_bool = True
    while limit_bool:
        servo.value = -.6
    servo.value = None
    limit_bool = True
    increment_servo_pos()
    if servo_pos == 22:
        time.sleep(2)
        next_cell()


# Calls 'next_cell()' x amount of times
def next_x_cells(x):
    for i in range(x):
        next_cell()
    return schedule.CancelJob


# Returns the current time plus one second in the form of a string 'HH:MM:SS'
def curr_time_plus_one_sec():
    new_time = datetime.now() + timedelta(seconds=1)
    return new_time.strftime('%X')


# Used to schedule events for the presses of the reset button
def reset_button_handler():
    schedule.every().day.at(curr_time_plus_one_sec()).do(lambda: next_x_cells(22-servo_pos))

reset_button.when_held = reset_button_handler


# Exports a data entry into the data_log.json file 
# Specifically used for valid and invalid dispenses
def write_json_export(priority, dispense_missed, slot):
    export_data = {
        'timeStamp': {
                        'date': datetime.today().strftime('%m/%d/%y'),
                        'time': curr_times[slot]
                    },
        'deviceName':'Smart Medication Dispenser',
        'patientName': USERNAME,
        'priority': priority,
        'message':  {
                        'dispense_missed': dispense_missed,
                        'medications': meds_for_each_time[int(slot[4])-1]
                    }
    }
    json.dump(export_data, export_file, ensure_ascii=False, indent=4)


# Sends an email alert to the user for the pills that are ready to be dispensed
def send_email(med_selector):
    if(email == ''):
        print('No email provided for notifications')
        return
    msg = MIMEMultipart()
    msg['From'] = NOTIFICATION_EMAIL
    msg['To'] = email
    msg['Subject'] = 'Medication ready to dispense! [RANIA - Smart Medication Dispenser]'
    msg_contents = f'''
    The medications: {meds_for_each_time[med_selector]} are ready to dispense.
    Please go to your dispenser and press the red button on the front of the device.
    '''
    msg.attach(MIMEText(msg_contents, 'plain'))
    smtp_sess = smtplib.SMTP('smtp.gmail.com', 587)
    smtp_sess.starttls()
    smtp_sess.login(NOTIFICATION_EMAIL, NOTIFICATION_EMAIL_PASS)
    smtp_sess.sendmail(NOTIFICATION_EMAIL, email, msg.as_string())
    smtp_sess.quit()
    print(f'Notification sent to {email}')


# Fetches the username assoicated with the machine code of this dispenser
def update_username():
    global USERNAME
    USERNAME = ''
    table = db.Table(MACHINE_CODE_TABLE_NAME)
    result = table.scan(
        FilterExpression=Attr('machineCode').eq(MACHINE_CODE)
        )
    data = result['Items']
    USERNAME = data[0]['patientUsername']
    print(f'Using username: {USERNAME}')



# Fetches the email associated with the user
def update_email():
    global email
    email = ''
    table = db.Table(EMAIL_TABLE_NAME)
    result = table.scan(
        FilterExpression=Attr('patientUsername').eq(USERNAME)
        )
    if len(result['Items']) != 0:
        data = result['Items']
        email = data[0]['patientEmail']


# Fetches times that are used for each medication and stores them in curr_meds[]
def update_med_times():
    curr_meds.clear()
    table = db.Table(MED_TABLE_NAME)
    # result = db.list_tables()
    result = table.scan(
        FilterExpression=Attr('userid').eq(USERNAME)
        )
    data = result['Items']
    for i in data:
        curr_meds.append({'name': i['name'], 'slot1': i['slot1'], 'slot2': i['slot2'], 'slot3': i['slot3']})
        # print_med_tuple(i)


# Fetches the three designated dose times and stores them in curr_times{}
def update_dose_times():
    table = db.Table(TIME_TABLE_NAME)
    result = table.scan(
        FilterExpression=Attr('userid').eq(USERNAME)
    )
    data = result['Items']
    data = data[0]
    curr_times['slot1'] = data['slot1']
    curr_times['slot2'] = data['slot2']
    curr_times['slot3'] = data['slot3']


# Generates and inserts a tuple into the Verification table
def gen_verification_tuple(meds_taken, img_name):
    id = uuid.uuid4()
    # Dynamodb uses ISO 8601 format
    orig_datetime = datetime.now()
    iso_date = orig_datetime.isoformat()
    date = orig_datetime.strftime('%m/%d/%y')
    time = orig_datetime.strftime('%H:%M')
    table = db.Table(VERIFICATION_TABLE_NAME)
    table.put_item(
        Item={
            'id': str(id),
            'createdAt': f'{str(iso_date)}Z',
            'updatedAt': f'{str(iso_date)}Z',
            'description': f'The medication(s): {meds_taken} were successfully taken',
            'image': img_name,
            'userid': USERNAME,
            'title': f'User: {USERNAME} Date: {date} Time: {time}'
        }
    )


# Generates and inserts a tuple into the Dispense table
def gen_dispense_tuple(took, time_slot, meds_taken):
    id = uuid.uuid4()
    # Dynamodb uses ISO 8601 format
    orig_datetime = datetime.now()
    iso_date = orig_datetime.isoformat()
    date = orig_datetime.strftime('%m/%d/%y')
    table = db.Table(DISP_TABLE_NAME)
    table.put_item(
        Item={
            'id': str(id),
            'createdAt': f'{str(iso_date)}Z',
            'updatedAt': f'{str(iso_date)}Z',
            'discription': meds_taken,
            'date': date,
            'time': time_slot,
            'took': took,
            'userid': USERNAME,
        }
    )


# Inserts an image into the finalmeddisp bucket.
def insert_verification_img(path, s3name):
    s3.meta.client.upload_file(path, VERIFICATION_BUCKET_NAME, f'public/{s3name}')
    return time


# Returns a list contianing curr_meds organized into lists based on time.
def organize_meds_based_on_time():
    global meds_for_each_time
    meds_for_each_time.clear()
    meds_for_each_time = [[],[],[]]
    for i in curr_meds:
        if str(i['slot1']) == 'True':
            meds_for_each_time[0].append(i['name'])
        if str(i['slot2']) == 'True':
            meds_for_each_time[1].append(i['name'])
        if str(i['slot3']) == 'True':
            meds_for_each_time[2].append(i['name'])


# Adds 10 min to a string 24 hr format time.
def add_ten_to_time(time):
    dt = datetime.strptime(time, '%H:%M')
    return (dt + timedelta(minutes=10)).strftime('%H:%M')


# Returns 1 if there is at least one false in disp_job_status
# Returns 0 otherwise
def do_errors_exist():
    for i in disp_jobs_status:
        if disp_jobs_status[i] == False:
            return 1
    return 0

# Returns 1 if there is at least one true in disp_job_status
# Returns 0 otherwise
def valid_dispense_exist():
    for i in disp_jobs_status:
        if disp_jobs_status[i] == True:
            return 1
    return 0


# Calls the aws data functions and checks to see if there are new dispensing times.
# If there are new dispensing times it calls 'reschedule_all()'
def call_update_functions():
    global old_times
    old_times = deepcopy(curr_times)
    update_username()
    update_email()
    update_med_times()
    update_dose_times()
    organize_meds_based_on_time()
    print('Pulling user data from AWS')
    if compare_dict(old_times, curr_times) != 0:
        print('New dispense times detected')
        reschedule_all()


# Function that will occur during every dispensing time
def time_to_dispense(slot):
    disp_jobs_order.append(slot)
    disp_jobs_status[slot] = True
    buzzer1.beep(on_time=1,off_time=2,n=3)
    buzzer2.beep(on_time=1,off_time=2,n=3)
    green_led.on()
    send_email(int(slot[4])-1)
    print(f'Dispense time for {slot} has arrived')


# Function that will occur during every button press
def on_button_press():
    if len(disp_jobs_order) == 0:
        return
    else:
        popped_job = disp_jobs_order.pop(0)

        i = -1
        if popped_job == 'slot1': i = 0
        elif popped_job == 'slot2': i = 1
        elif popped_job == 'slot3': i = 2

        next_cell()
        if disp_jobs_status[popped_job] == False:
            disp_jobs_status[popped_job] = ''
            print(f'{popped_job} has been dispensed for removal')
            # Turn off led if there are no more missed dispsense times
            if do_errors_exist() != 1:
                red_led.off()
            elif len(disp_jobs_order) == 0:
                green_led.off()
                red_led.off()
        else:
            disp_jobs_status[popped_job] = ''

            # Turn off leds if 0 dispense times are queued
            if len(disp_jobs_order) == 0:
                green_led.off()
                red_led.off()

            print(f'Pills were dispensed on time for {popped_job}')
            img_name = datetime.now().replace(tzinfo=timezone.utc).timestamp()
            img_name = str(trunc(img_name))
            img_name += '.jpg'
            cam.capture(os.path.join(PIPATH, f'{PHOTO_PATH}{img_name}'))
            insert_verification_img(os.path.join(PIPATH, f'{PHOTO_PATH}{img_name}'), img_name)
            gen_verification_tuple(meds_for_each_time[i], img_name)
            gen_dispense_tuple('True', curr_times[popped_job], meds_for_each_time[i])
            write_json_export('3', False, popped_job)

            # Delete the local copy of the file
            if os.path.exists(os.path.join(PIPATH, f'{PHOTO_PATH}{img_name}')):
                os.remove(os.path.join(PIPATH, f'{PHOTO_PATH}{img_name}'))

            # Cancel the dispense fail job since dispense was successful
            schedule.cancel_job(disp_fails.pop(0))
    return schedule.CancelJob


# Schedules an event which will run on_button_press() one sec after the current time.
# This scheduled event is canceled after its first run.
def button_press_handler():
    schedule.every().day.at(curr_time_plus_one_sec()).do(on_button_press)
# button_press_handler is bound to the dispsense_button
dispense_button.when_pressed = button_press_handler


# Schedules all of the events (jobs) which will mark a dispense failure (10 min after each dispense time)
def schedule_fails():
    # Clear old fail tasks
    for i in disp_fails:
        schedule.cancel_job(i)
    disp_fails.clear()

    # Reschedule the fail tasks
    disp_fails.append(schedule.every().day.at(add_ten_to_time(curr_times['slot1'])).do(lambda: dispense_fail('slot1')))
    disp_fails.append(schedule.every().day.at(add_ten_to_time(curr_times['slot2'])).do(lambda: dispense_fail('slot2')))
    disp_fails.append(schedule.every().day.at(add_ten_to_time(curr_times['slot3'])).do(lambda: dispense_fail('slot3')))
    print(f'Fail times added: {add_ten_to_time(curr_times["slot1"])}, {add_ten_to_time(curr_times["slot2"])}, {add_ten_to_time(curr_times["slot3"])}')


# Function that runs when the dispense fail task is triggered.
def dispense_fail(slot):
    gen_dispense_tuple('False', curr_times[slot], meds_for_each_time[int(slot[4])-1])
    write_json_export('1', True, slot)
    disp_jobs_status[slot] = False
    red_led.on()
    # If there are no longer any dispensing times that haven't expired, turn off the led.
    if valid_dispense_exist() != 1:
        green_led.off()
    # Cancel the dispense fail job since it is no longer needed
    schedule.cancel_job(disp_fails.pop(0))
    print(f'Dispense time for {slot} has been missed')


# Completely wipes and rebuilds all tasks (jobs).
# This is useful when a dispense time has changed.
def reschedule_all():
    schedule.clear()
    disp_jobs.clear()
    disp_jobs_order.clear()
    print('All jobs cleared')
    # Call update_med_times() and update_dose_times() every 10 min
    schedule.every(10).minutes.do(call_update_functions)
    print('Update job added')

    disp_jobs.append(schedule.every().day.at(curr_times['slot1']).do(lambda: time_to_dispense('slot1')))
    disp_jobs.append(schedule.every().day.at(curr_times['slot2']).do(lambda: time_to_dispense('slot2')))
    disp_jobs.append(schedule.every().day.at(curr_times['slot3']).do(lambda: time_to_dispense('slot3')))
    print(f'Dispense jobs added: {curr_times["slot1"]}, {curr_times["slot2"]}, {curr_times["slot3"]}')

    # Schedule tasks that if not stopped will report a dispense failure to the db
    schedule.every().day.at('02:00').do(schedule_fails)
    print('Dispense fail creation job added')
    schedule_fails()


# Compares two dictionaries. Returns 0 if equal. -1 if not equal.
def compare_dict(dict1, dict2):
    for i in dict1:
        if i not in dict2:
            return -1
        elif dict1[i] != dict2[i]:
            return -1
    for i in dict2:
        if i not in dict1:
            return -1
        elif dict1[i] != dict2[i]:
            return -1
    return 0


# Used for testing purposes only
def print_med_tuple(tuple):
    print(f'[{tuple["name"]}, slot1: {tuple["slot1"]}, slot2: {tuple["slot2"]}, slot3: {tuple["slot3"]}]')


def main():
    call_update_functions()
    startup_sequence()

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    main()

/* eslint-disable */
// this is an auto generated file. This will be overwritten

export const getMedication = /* GraphQL */ `
  query GetMedication($id: ID!) {
    getMedication(id: $id) {
      id
      name
      quantity
      start
      end
      slot1
      slot2
      slot3
      userid
      createdAt
      updatedAt
    }
  }
`;
export const listMedications = /* GraphQL */ `
  query ListMedications(
    $filter: ModelMedicationFilterInput
    $limit: Int
    $nextToken: String
  ) {
    listMedications(filter: $filter, limit: $limit, nextToken: $nextToken) {
      items {
        id
        name
        quantity
        start
        end
        slot1
        slot2
        slot3
        userid
        createdAt
        updatedAt
      }
      nextToken
    }
  }
`;
export const getCaregiverPatientMatcher = /* GraphQL */ `
  query GetCaregiverPatientMatcher($id: ID!) {
    getCaregiverPatientMatcher(id: $id) {
      id
      patientUsername
      caregiverUsername
      createdAt
      updatedAt
    }
  }
`;
export const listCaregiverPatientMatchers = /* GraphQL */ `
  query ListCaregiverPatientMatchers(
    $filter: ModelCaregiverPatientMatcherFilterInput
    $limit: Int
    $nextToken: String
  ) {
    listCaregiverPatientMatchers(
      filter: $filter
      limit: $limit
      nextToken: $nextToken
    ) {
      items {
        id
        patientUsername
        caregiverUsername
        createdAt
        updatedAt
      }
      nextToken
    }
  }
`;
export const getDispenseTimeSlots = /* GraphQL */ `
  query GetDispenseTimeSlots($id: ID!) {
    getDispenseTimeSlots(id: $id) {
      id
      timeSlot1
      timeSlot2
      timeSlot3
      createdAt
      updatedAt
    }
  }
`;
export const listDispenseTimeSlotss = /* GraphQL */ `
  query ListDispenseTimeSlotss(
    $filter: ModeldispenseTimeSlotsFilterInput
    $limit: Int
    $nextToken: String
  ) {
    listDispenseTimeSlotss(
      filter: $filter
      limit: $limit
      nextToken: $nextToken
    ) {
      items {
        id
        timeSlot1
        timeSlot2
        timeSlot3
        createdAt
        updatedAt
      }
      nextToken
    }
  }
`;
export const getVerification = /* GraphQL */ `
  query GetVerification($id: ID!) {
    getVerification(id: $id) {
      id
      title
      description
      image
      userid
      createdAt
      updatedAt
    }
  }
`;
export const listVerifications = /* GraphQL */ `
  query ListVerifications(
    $filter: ModelVerificationFilterInput
    $limit: Int
    $nextToken: String
  ) {
    listVerifications(filter: $filter, limit: $limit, nextToken: $nextToken) {
      items {
        id
        title
        description
        image
        userid
        createdAt
        updatedAt
      }
      nextToken
    }
  }
`;
export const getDispense = /* GraphQL */ `
  query GetDispense($id: ID!) {
    getDispense(id: $id) {
      id
      date
      time
      took
      userid
      createdAt
      updatedAt
    }
  }
`;
export const listDispenses = /* GraphQL */ `
  query ListDispenses(
    $filter: ModelDispenseFilterInput
    $limit: Int
    $nextToken: String
  ) {
    listDispenses(filter: $filter, limit: $limit, nextToken: $nextToken) {
      items {
        id
        date
        time
        took
        userid
        createdAt
        updatedAt
      }
      nextToken
    }
  }
`;
export const getConsumptionHistoryTable = /* GraphQL */ `
  query GetConsumptionHistoryTable($id: ID!) {
    getConsumptionHistoryTable(id: $id) {
      id
      date
      userid
      createdAt
      updatedAt
    }
  }
`;
export const listConsumptionHistoryTables = /* GraphQL */ `
  query ListConsumptionHistoryTables(
    $filter: ModelConsumptionHistoryTableFilterInput
    $limit: Int
    $nextToken: String
  ) {
    listConsumptionHistoryTables(
      filter: $filter
      limit: $limit
      nextToken: $nextToken
    ) {
      items {
        id
        date
        userid
        createdAt
        updatedAt
      }
      nextToken
    }
  }
`;
export const getTimeSlots = /* GraphQL */ `
  query GetTimeSlots($id: ID!) {
    getTimeSlots(id: $id) {
      id
      userid
      slot1
      slot2
      slot3
      createdAt
      updatedAt
    }
  }
`;
export const listTimeSlotss = /* GraphQL */ `
  query ListTimeSlotss(
    $filter: ModelTimeSlotsFilterInput
    $limit: Int
    $nextToken: String
  ) {
    listTimeSlotss(filter: $filter, limit: $limit, nextToken: $nextToken) {
      items {
        id
        userid
        slot1
        slot2
        slot3
        createdAt
        updatedAt
      }
      nextToken
    }
  }
`;

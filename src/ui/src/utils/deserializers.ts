import { RecordMatch } from "@/models/recordMatch";

/* eslint-disable @typescript-eslint/no-explicit-any */
export function deserializeToRecordMatch(
  jsonResponse: Record<string, any>,
): RecordMatch {
  const recordMatch: RecordMatch = {
    ...jsonResponse,
    incoming_record: {
      ...jsonResponse.incoming_record,
      birth_date: new Date(jsonResponse.incoming_record.birth_date),
      received_on: new Date(jsonResponse.incoming_record.received_on),
    },
    potential_match: jsonResponse.potential_match.map(
      (matchGroup: Record<string, string | any>) => ({
        ...matchGroup,
        patients: matchGroup.patients.map(
          (patient: Record<string, string | number | Date>) => ({
            ...patient,
            birth_date: new Date(patient.birth_date),
          }),
        ),
      }),
    ),
  } as RecordMatch;

  return recordMatch;
}
/* eslint-enable @typescript-eslint/no-explicit-any */

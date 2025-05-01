import { DataStream } from "./dataStream";
import { Patient } from "./patient";

export interface IncomingRecord extends Patient {
  data_stream: DataStream;
  received_on: Date;
}

export interface PotentialMatch {
  person_id: string;
  link_score: number;
  patients: Patient[];
}

export interface RecordMatch {
  linked: null | string;
  incoming_record: IncomingRecord;
  potential_match: PotentialMatch[];
}

import { DataStream } from "./dataStream";

export interface IncomingData {
  patient_id: string;
  first_name: string;
  last_name: string;
  mrn: string;
  birth_date: Date;
  address: {
    line: string;
    city: string;
    state: string;
    postal_code: string;
  };
}

export interface PotentialMatch extends IncomingData {
  person_id: string;
}

export interface Record {
  id: number;
  first_name: string;
  last_name: string;
  birth_date: Date;
  received_on: Date;
  data_stream: DataStream;
  link_score: number;
  linked: null | string;
  incoming_data?: IncomingData;
  potential_match?: PotentialMatch;
}

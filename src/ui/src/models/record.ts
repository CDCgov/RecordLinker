import { DataStream } from "./dataStream";
import { Patient } from "./patient";

export interface Record {
  id: string;
  patient: Patient;
  receivedOn: Date;
  dataStream: DataStream;
  linkScore: number;
}

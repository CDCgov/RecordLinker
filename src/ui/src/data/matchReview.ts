import { Record } from "@/models/record";

const recordMatchMock = {
  id: 123,
  first_name: "John",
  last_name: "Doe",
  birth_date: new Date("01/07/1993"),
  received_on: new Date("04/22/2021"),
  data_stream: {
    system: "System system",
    type: "ELR",
  },
  link_score: 0.9,
  linked: null,
  incoming_data: {
    patient_id: "234",
    first_name: "Jane",
    last_name: "Doe",
    mrn: "1234",
    birth_date: new Date("01/07/1993"),
    address: {
      line: "209 Easy St.",
      city: "Witchita",
      state: "KS",
      postal_code: "67223",
    },
  },
  potential_match: {
    person_id: "3502",
    patient_id: "234",
    first_name: "Jan",
    last_name: "Doe",
    mrn: "1234",
    birth_date: new Date("01/07/1993"),
    address: {
      line: "209 Easy St.",
      city: "Witchita",
      state: "KS",
      postal_code: "67223",
    },
  },
};

export async function getRecordMatch(id: string | null): Promise<Record> {
  console.log("id:", id);
  // return (await fetch(`${API_URL}/demo/record/${id}`)).json();
  // return null;
  // return Promise.reject(new Error("oooops"));
  return Promise.resolve(recordMatchMock);
}

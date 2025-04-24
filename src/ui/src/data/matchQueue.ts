import { Record as RLRecord } from "@/models/record";

export async function getUnmatchedRecords(): Promise<RLRecord[]> {
  // return (await fetch(`${API_URL}/demo/record`)).json();
  // return [];
  // return Promise.reject(new Error("oooops"));
  return Promise.resolve([
    {
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
    },
    {
      id: 124,
      first_name: "Jane",
      last_name: "Doe",
      birth_date: new Date("01/07/1993"),
      received_on: new Date("04/22/2021"),
      data_stream: {
        system: "System system",
        type: "ELR",
      },
      link_score: 0.9,
      linked: null,
    },
  ]);
}

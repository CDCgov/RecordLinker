import { Record as RLRecord } from "@/models/record";

export async function getUnreviewedRecords(): Promise<RLRecord[]> {
  //  return (await fetch(`${API_URL}/demo/record`)).json();
  //return [];
  //  return Promise.reject(new Error("oooops"));
  return Promise.resolve([
    {
      id: "123",
      patient: {
        firstName: "John",
        LastName: "Doe",
        dob: new Date("04/13/1989"),
      },
      receivedOn: new Date(),
      dataStream: {
        name: "System system",
        type: "ELR",
      },
      linkScore: 0.98,
    },
    {
      id: "124",
      patient: {
        firstName: "Jane",
        LastName: "Doe",
        dob: new Date("04/15/1989"),
      },
      receivedOn: new Date(),
      dataStream: {
        name: "System system",
        type: "ELR",
      },
      linkScore: 0.86,
    },
  ]);
}

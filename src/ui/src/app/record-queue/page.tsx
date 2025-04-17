import ServerError from "@/components/serverError/serverError";
import EmptyQueue from "./emptyQueue";
import RecordTable from "@/components/recordTable/recordTable";
import { Record } from "@/models/record";

const records: Record[] = [
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
];

const CaseQueue: React.FC = () => {
  const view: string = "table";

  return (
    <div className="page-container--xl page-container--full-height padding-top-5 padding-bottom-10">
      <h1 className="font-alt-xl margin-bottom-0">Record match queue</h1>
      <p className="subheading margin-bottom-4">
        Based on your algorithm configuration rules, RecordLinker found no
        automatic matches for the patient records listed below. Please review
        each record for field similarity to make a manual match decision.
      </p>
      {view == "table" && <RecordTable items={records} withReviewLink />}
      {view == "error" && <ServerError />}
      {view == "empty" && <EmptyQueue />}
    </div>
  );
};

export default CaseQueue;

import ServerError from "@/components/serverError/serverError";
import EmptyQueue from "./emptyQueue";
import RecordTable from "@/components/recordTable/recordTable";

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
      {view == "table" && <RecordTable items={[]} withReviewLink />}
      {view == "error" && <ServerError />}
      {view == "empty" && <EmptyQueue />}
    </div>
  );
};

export default CaseQueue;

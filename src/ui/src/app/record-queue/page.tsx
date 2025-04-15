import ServerError from "@/components/serverError/serverError";
import EmptyQueue from "./emptyQueue";

const CaseQueue: React.FC = () => {
  const view: string = "empty";

  return (
    <div className="page-container--xl page-container--full-height padding-top-5 padding-bottom-10">
      <h1 className="font-alt-xl margin-bottom-0">Record match queue</h1>
      <p className="subheading margin-bottom-3">
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam sed
        condimentum mauris.
      </p>
      {view == "error" && <ServerError />}
      {view == "empty" && <EmptyQueue />}
    </div>
  );
};

export default CaseQueue;

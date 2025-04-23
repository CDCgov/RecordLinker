import BackToLink from "@/components/backToLink/BackToLink";
import { PAGES } from "@/utils/constants";
import RecordView from "./recordView";

const RecordReview: React.FC = () => {
  return (
    <div className="page-container--lg page-container--full-height padding-top-5 padding-bottom-10">
      <BackToLink
        href={PAGES.RECORD_QUEUE}
        text="Return to record match queue"
      />
      <h1 className="font-alt-xl margin-bottom-0 margin-top-3">
        Record match review
      </h1>
      <p className="subheading margin-bottom-3">
        Compare the incoming record with the potential match in the queue to
        determine if they refer to the same individual.
      </p>
      <RecordView />
      <p className="text-italic margin-top-2">
        Linking a record will append a Person ID to the incoming record,
        effectively linking it to the potential match.
      </p>
    </div>
  );
};

export const metadata = {
  title: "Record linker | Match review",
};

export default RecordReview;

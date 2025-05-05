import { Suspense } from "react";
import BackToLink from "@/components/backToLink/backToLink";
import { PAGES } from "@/utils/constants";
import RecordView from "./recordView";

const MatchReview: React.FC = () => {
  return (
    <div className="page-container--lg page-container--full-height padding-top-5 padding-bottom-10">
      <BackToLink href={PAGES.RECORD_QUEUE} text="Return to match queue" />
      <h1 className="font-alt-xl margin-bottom-0 margin-top-3">Match review</h1>
      <p className="subheading margin-bottom-3">
        Compare the incoming record with the potential match in the queue to
        determine if they refer to the same individual.
      </p>
      <Suspense>
        <RecordView />
      </Suspense>
      <p className="text-italic margin-top-2">
        Linking confirms a match and applies the Person ID from the potential
        match to the incoming record.
      </p>
    </div>
  );
};

export const metadata = {
  title: "Record linker | Match review",
};

export default MatchReview;

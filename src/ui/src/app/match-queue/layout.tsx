import ResetDemoButton from "@/app/match-queue/ResetDemoButton";

const MatchQueueLayout: React.FC<React.PropsWithChildren> = ({ children }) => {
  return (
    <div className="page-container page-container--xl page-container--full-height padding-top-5 padding-bottom-10">
      <h1 className="font-alt-xl margin-bottom-0">Record match queue</h1>
      <div className="display-flex flex-align-center margin-bottom-4">
        <p className="subheading margin-right-10">
          Based on your algorithm configuration rules, Record Linker found no
          automatic matches for the patient records listed below. Please review
          each record for field similarity to make a manual match decision.
        </p>
        <ResetDemoButton />
      </div>

      {children}
    </div>
  );
};

export const metadata = {
  title: "Record linker | Match queue",
};

export default MatchQueueLayout;

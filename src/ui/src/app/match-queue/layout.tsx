const RecordQueueLayout: React.FC<React.PropsWithChildren> = ({ children }) => {
  return (
    <div className="page-container--xl page-container--full-height padding-top-5 padding-bottom-10">
      <h1 className="font-alt-xl margin-bottom-0">Record match queue</h1>
      <p className="subheading margin-bottom-4">
        Based on your algorithm configuration rules, Record Linker found no
        automatic matches for the patient records listed below. Please review
        each record for field similarity to make a manual match decision.
      </p>
      {children}
    </div>
  );
};

export const metadata = {
  title: "Record linker | Match queue",
};

export default RecordQueueLayout;

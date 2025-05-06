const MatchQueueLayout: React.FC<React.PropsWithChildren> = ({ children }) => {
  return (
    <div className="page-container page-container--xl page-container--full-height padding-top-5 padding-bottom-10">
      <h1 className="font-alt-xl margin-bottom-0">Match queue</h1>
      <p className="subheading margin-bottom-4">
        Based on your algorithm configuration rules, Record Linker automatically
        matched a subset of records. The remaining records below are possible
        matches that need manual review.
      </p>
      {children}
    </div>
  );
};

export const metadata = {
  title: "Record linker | Match queue",
};

export default MatchQueueLayout;

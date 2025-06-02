"use client";

import { useEffect, useState } from "react";
import ServerError from "@/components/serverError/serverError";
import RecordTable from "@/components/recordTable/recordTable";
import { RecordMatch } from "@/models/recordMatch";
import { getUnmatchedRecords } from "@/data/matchQueue";
import EmptyFallback from "@/components/emptyFallback/emptyFallback";

const MatchQueue: React.FC = () => {
  const [recordList, setRecordList] = useState<RecordMatch[] | undefined>();
  const [serverError, setServerError] = useState(false);

  /**
   * Initialize data
   */
  async function retrieveUnmatchedRecords() {
    try {
      const records = await getUnmatchedRecords();
      setRecordList(records);
    } catch (e) {
      console.error(e);
      setServerError(true);
    }
  }

  useEffect(() => {
    retrieveUnmatchedRecords();
  }, []);

  /**
   * HTML
   */
  if (serverError) {
    return <ServerError />;
  } else if (recordList && recordList?.length > 0) {
    return (
      <div className="page-container--x-scroll">
        <RecordTable items={recordList} withReviewLink withSortIndicator />
      </div>
    );
  } else if (recordList && recordList?.length === 0) {
    return (
      <EmptyFallback
        message={
          <>
            No cases left to review.
            <br />
            Reset queue to repopulate cases.
          </>
        }
      />
    );
  }

  return null;
};

export default MatchQueue;

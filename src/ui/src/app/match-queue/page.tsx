"use client";

import { useEffect, useState } from "react";
import ServerError from "@/components/serverError/serverError";
import EmptyQueue from "./emptyQueue";
import RecordTable from "@/components/recordTable/recordTable";
import { Record } from "@/models/record";
import { getUnmatchedRecords } from "@/data/matchQueue";

const MatchQueue: React.FC = () => {
  const [recordList, setRecordList] = useState<Record[] | undefined>();
  const [serverError, setServerError] = useState(false);

  /**
   * Initialize data
   */
  async function retrieveUnmatchedRecords() {
    try {
      const records = await getUnmatchedRecords();
      setRecordList(records);
    } catch (_) {
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
    return <RecordTable items={recordList} withReviewLink withSortIndicator />;
  } else if (recordList && recordList?.length === 0) {
    return <EmptyQueue />;
  }

  return null;
};

export default MatchQueue;

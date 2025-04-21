"use client";

import { useEffect, useState } from "react";
import ServerError from "@/components/serverError/serverError";
import EmptyQueue from "./emptyQueue";
import RecordTable from "@/components/recordTable/recordTable";
import { Record } from "@/models/record";
import { getUnreviewedRecords } from "@/data/recordQueue";

const UnreviewedRecordQueue: React.FC = () => {
  const [recordList, setRecordList] = useState<Record[] | undefined>();
  const [serverError, setServerError] = useState(false);

  async function retrieveUnreviewedRecords() {
    try {
      const records = await getUnreviewedRecords();
      setRecordList(records);
    } catch (_) {
      setServerError(true);
    }
  }

  useEffect(() => {
    retrieveUnreviewedRecords();
  }, []);

  if (serverError) {
    return <ServerError />;
  } else if (recordList && recordList?.length > 0) {
    return <RecordTable items={recordList} withReviewLink />;
  } else if (recordList && recordList?.length === 0) {
    return <EmptyQueue />;
  }

  return null;
};

export default UnreviewedRecordQueue;

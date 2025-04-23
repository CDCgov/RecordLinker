"use client";

import RecordTable from "@/components/recordTable/recordTable";
import { LinkIcon, LinkOffIcon } from "@/components/Icons/icons";
import { Button } from "@trussworks/react-uswds";
import { Record } from "@/models/record";
import RecordCompare from "./recordCompare";
import { useEffect, useState } from "react";
import ServerError from "@/components/serverError/serverError";
import { getRecordMatch } from "@/data/matchReview";
import { useSearchParams } from "next/navigation";

const patient: unknown = [
  {
    id: "123",
    patient: {
      firstName: "John",
      lastName: "Doe",
      dob: new Date("04/13/1989"),
    },
    receivedOn: new Date(),
    dataStream: {
      name: "System system",
      type: "ELR",
    },
    linkScore: 0.98,
  },
];

const RecordView: React.FC = () => {
  const searchParams = useSearchParams();
  const recordId = searchParams.get("id");

  const [recordMathInfo, setRecordMathInfo] = useState<
    unknown | null | undefined
  >();
  const [serverError, setServerError] = useState(false);

  async function retrieveRecordMatchInfo() {
    try {
      const recordInfo = await getRecordMatch(recordId);
      setRecordMathInfo(recordInfo);
    } catch (_) {
      setServerError(true);
    }
  }

  useEffect(() => {
    retrieveRecordMatchInfo();
  }, []);

  if (serverError) {
    return <ServerError />;
  } else if (recordMathInfo) {
    return (
      <>
        <RecordTable items={patient as Record[]} />
        <RecordCompare />
        <div className="margin-top-3">
          <Button className="margin-right-105">
            Link record <LinkIcon size={3} />
          </Button>
          <Button>
            Do not link record <LinkOffIcon size={3} />
          </Button>
        </div>
      </>
    );
  }

  return null;
};

export default RecordView;

"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import RecordTable from "@/components/recordTable/recordTable";
import { LinkIcon, LinkOffIcon } from "@/components/Icons/icons";
import { Button } from "@trussworks/react-uswds";
import { IncomingData, PotentialMatch, Record } from "@/models/record";
import ServerError from "@/components/serverError/serverError";
import { getRecordMatch } from "@/data/matchReview";
import RecordCompare, { FieldComparisonValues } from "./recordCompare";

function formatFieldValue(
  value: PotentialMatch[keyof PotentialMatch] | undefined,
): string {
  if (value instanceof Date) {
    return value.toLocaleDateString();
  } else if (value) {
    return value.toString();
  }

  return "";
}

function breakRecordIntoFields(record: Record): FieldComparisonValues[] {
  let fields: FieldComparisonValues[] = [];
  const complexFields = ["address"];

  if (record.potential_match && record.incoming_data) {
    // simple fields
    fields = Object.keys(record.potential_match)
      .filter((label: string) => !complexFields.includes(label))
      .map((label: string, i: number) => {
        return {
          key: i,
          label: label,
          incomingValue: formatFieldValue(
            record.incoming_data?.[label as keyof IncomingData],
          ),
          potentialValue: formatFieldValue(
            record.potential_match?.[label as keyof PotentialMatch],
          ),
        } as FieldComparisonValues;
      });

    // complex fields
    fields.push({
      key: fields.length,
      label: "Address 1",
      incomingValue: `${record.incoming_data?.address?.city}, ${record.incoming_data?.address?.state} ${record.incoming_data?.address?.postal_code}`,
      potentialValue: `${record.potential_match?.address?.city}, ${record.potential_match?.address?.state} ${record.potential_match?.address?.postal_code}`,
    });

    fields.push({
      key: fields.length,
      label: "Address 2",
      incomingValue: record.incoming_data?.address?.line,
      potentialValue: record.potential_match?.address?.line,
    });
  }

  return fields;
}

const RecordView: React.FC = () => {
  const searchParams = useSearchParams();
  const recordId = searchParams.get("id");

  const [selectedRecord, setSelectedRecord] = useState<Record | undefined>();
  const [serverError, setServerError] = useState(false);

  /**
   * Initialize data
   */
  async function retrieveRecordMatchInfo() {
    try {
      const recordInfo: Record = await getRecordMatch(recordId);
      setSelectedRecord(recordInfo);
    } catch (_) {
      setServerError(true);
    }
  }

  useEffect(() => {
    retrieveRecordMatchInfo();
  }, []);

  /**
   * HTML
   */
  if (serverError) {
    return <ServerError />;
  } else if (selectedRecord) {
    return (
      <>
        <RecordTable items={[selectedRecord]} />
        <RecordCompare
          comparisonFields={breakRecordIntoFields(selectedRecord)}
        />
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

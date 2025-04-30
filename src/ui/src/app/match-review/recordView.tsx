"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import RecordTable from "@/components/recordTable/recordTable";
import { LinkIcon, LinkOffIcon } from "@/components/icons/icons";
import { Button } from "@trussworks/react-uswds";
import {
  IncomingRecord,
  PotentialMatch,
  RecordMatch,
} from "@/models/recordMatch";
import ServerError from "@/components/serverError/serverError";
import { getRecordMatch } from "@/data/matchReview";
import RecordCompare, { FieldComparisonValues } from "./recordCompare";
import { Patient } from "@/models/patient";
import EmptyFallback from "@/components/emptyFallback/emptyFallback";

function formatFieldValue(value: Patient[keyof Patient] | undefined): string {
  if (value instanceof Date) {
    return value.toLocaleDateString();
  } else if (value) {
    return value.toString();
  }

  return "";
}

function breakRecordIntoFields(
  incomingRecord: IncomingRecord,
  potentialMatch: PotentialMatch,
): FieldComparisonValues[] {
  const potentialPerson = potentialMatch.patients?.[0];

  let fields: FieldComparisonValues[] = [];
  const simpleFields = [
    "patient_id",
    "first_name",
    "last_name",
    "mrn",
    "birth_date",
    "email",
  ];

  if (incomingRecord && potentialPerson) {
    // Person ID
    fields.push({
      label: "person_id",
      incomingValue: "",
      potentialValue: potentialMatch.person_id,
    });

    // simple fields
    fields = fields.concat(
      Object.keys(potentialMatch.patients[0])
        .filter((label: string) => simpleFields.includes(label))
        .map((label: string) => {
          return {
            label: label,
            incomingValue: formatFieldValue(
              incomingRecord[label as keyof Patient],
            ),
            potentialValue: formatFieldValue(
              potentialPerson[label as keyof Patient],
            ),
          } as FieldComparisonValues;
        }),
    );

    // complex fields
    fields.push({
      label: "Address",
      incomingValue: incomingRecord.address?.line?.[0],
      potentialValue: potentialPerson.address?.line?.[0],
    });

    fields.push({
      label: "City, State, Zip",
      incomingValue: `${incomingRecord.address?.city}, ${incomingRecord.address?.state} ${incomingRecord.address?.postal_code}`,
      potentialValue: `${potentialPerson.address?.city}, ${potentialPerson.address?.state} ${potentialPerson.address?.postal_code}`,
    });
  }

  return fields;
}

const RecordView: React.FC = () => {
  const searchParams = useSearchParams();
  const recordId = searchParams.get("id");

  const [selectedRecord, setSelectedRecord] = useState<
    RecordMatch | undefined
  >();
  const [serverError, setServerError] = useState<
    undefined | "server" | "not_found"
  >();

  /**
   * Initialize data
   */
  async function retrieveRecordMatchInfo() {
    try {
      const recordInfo: RecordMatch = await getRecordMatch(recordId);
      setSelectedRecord(recordInfo);
    } catch (e) {
      console.error(e);
      if (e == "Error: 404") {
        setServerError("not_found");
      } else {
        setServerError("server");
      }
    }
  }

  useEffect(() => {
    retrieveRecordMatchInfo();
  }, []);

  /**
   * HTML
   */
  if (serverError == "server") {
    return <ServerError />;
  } else if (serverError == "not_found") {
    return <EmptyFallback message="Record not found." />;
  } else if (selectedRecord) {
    return (
      <>
        <RecordTable items={[selectedRecord]} />
        <RecordCompare
          comparisonFields={breakRecordIntoFields(
            selectedRecord.incoming_record,
            selectedRecord.potential_match?.[0],
          )}
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

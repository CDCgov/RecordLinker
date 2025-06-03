"use client";

import { useEffect, useState } from "react";
import { useSearchParams, redirect } from "next/navigation";
import RecordTable from "@/components/recordTable/recordTable";
import { LinkIcon, LinkOffIcon } from "@/components/icons/icons";
import { Button } from "@trussworks/react-uswds";
import {
  IncomingRecord,
  PotentialMatch,
  RecordMatch,
} from "@/models/recordMatch";
import ServerError from "@/components/serverError/serverError";
import {
  getRecordMatch,
  linkRecordAndMatch,
  unlinkRecordAndMatch,
} from "@/data/matchReview";
import RecordCompare, { FieldComparisonValues } from "./recordCompare";
import { Patient } from "@/models/patient";
import EmptyFallback from "@/components/emptyFallback/emptyFallback";
import { AppError, PAGE_ERRORS } from "@/utils/errors";
import { showToast, ToastType } from "@/components/toast/toast";
import { PAGES } from "@/utils/constants";
import MatchReviewStyles from "./matchReview.module.scss";

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
  const [pageError, setPageError] = useState<undefined | PAGE_ERRORS>();

  /**
   * Initialize data
   */
  async function retrieveRecordMatchInfo() {
    try {
      const recordInfo: RecordMatch = await getRecordMatch(recordId);
      setSelectedRecord(recordInfo);
    } catch (e) {
      console.error(e);
      if (e instanceof AppError && (e.httpCode == 404 || e.httpCode == 422)) {
        setPageError(PAGE_ERRORS.RESOURCE_NOT_FOUND);
      } else {
        setPageError(PAGE_ERRORS.SERVER_ERROR);
      }
    }
  }

  useEffect(() => {
    retrieveRecordMatchInfo();
  }, []);

  /**
   * Event handlers
   */
  async function linkRecord() {
    try {
      await linkRecordAndMatch(recordId);

      showToast(
        ToastType.SUCCESS,
        "The record has been reviewed and cleared from your queue.",
      );
    } catch (e) {
      console.error(e);
      showToast(
        ToastType.ERROR,
        "We were unable to process your request. Please try again.",
      );
    } finally {
      redirect(PAGES.RECORD_QUEUE);
    }
  }

  async function unlinkRecord() {
    try {
      await unlinkRecordAndMatch(recordId);

      showToast(
        ToastType.SUCCESS,
        "The record has been reviewed and cleared from your queue.",
      );
    } catch (e) {
      console.error(e);
      showToast(
        ToastType.ERROR,
        "We were unable to process your request. Please try again.",
      );
    } finally {
      redirect(PAGES.RECORD_QUEUE);
    }
  }

  /**
   * HTML
   */
  if (pageError == PAGE_ERRORS.SERVER_ERROR) {
    return <ServerError />;
  } else if (pageError == PAGE_ERRORS.RESOURCE_NOT_FOUND) {
    return (
      <EmptyFallback
        message={recordId ? "Record not found." : "Invalid record."}
      />
    );
  } else if (selectedRecord) {
    return (
      <>
        <div className="page-container--x-scroll">
          <RecordTable items={[selectedRecord]} />
          <RecordCompare
            comparisonFields={breakRecordIntoFields(
              selectedRecord.incoming_record,
              selectedRecord.potential_match?.[0],
            )}
          />
        </div>
        <div className="margin-top-3">
          <Button className="margin-right-105" onClick={linkRecord}>
            Link record <LinkIcon size={3} />
          </Button>
          <Button
            className={MatchReviewStyles.doNotLink}
            onClick={unlinkRecord}
          >
            Do not link record <LinkOffIcon size={3} />
          </Button>
        </div>
      </>
    );
  }

  return null;
};

export default RecordView;

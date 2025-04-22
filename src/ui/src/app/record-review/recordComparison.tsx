"use client";

import { JSX } from "react";
import RecordTable from "@/components/recordTable/recordTable";
import classNames from "classnames";
import { LinkIcon, LinkOffIcon } from "@/components/Icons/icons";
import { Button } from "@trussworks/react-uswds";
import { Record } from "@/models/record";
import styles from "./recordReview.module.scss";

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

function getComparisonRow(
  idx: number,
  label: string,
  incomingValue: string,
  matchingValue: string,
): JSX.Element {
  return (
    <div key={idx} role="row" className={classNames("grid-row", "flex-row")}>
      <div
        role="rowlabel"
        className={classNames(
          "flex-2",
          "text-semibold",
          "text-accent-cool-dark",
          "padding-y-1",
        )}
      >
        {label}
      </div>
      <div
        role="gridcell"
        className={classNames(
          "flex-4",
          "border-x",
          "border-accent-cool-light",
          "margin-left-2",
          "padding-x-105",
          "padding-y-1",
          idx % 2 ? "bg-accent-cool-lighter" : "bg-white",
        )}
      >
        {incomingValue}
      </div>
      <div
        role="gridcell"
        className={classNames(
          "flex-4",
          "border-x",
          "border-accent-cool-light",
          "margin-left-2",
          "padding-x-105",
          "padding-y-1",
          idx % 2 ? "bg-accent-cool-lighter" : "bg-white",
        )}
      >
        {matchingValue}
      </div>
    </div>
  );
}

function getComparisonView() {
  // ToDo I need to retrieve the data

  return (
    <div
      role="grid"
      className={classNames(
        "margin-top-3",
        "padding-x-5",
        "padding-y-3",
        "border-color-light-blue",
        "border-y-1px",
        styles.comparisonView,
      )}
    >
      <div role="row" className={classNames("grid-row", "flex-row")}>
        <div role="columnlabel" className={classNames("flex-2")}></div>
        <div
          role="columnlabel"
          className={classNames(
            "flex-4",
            "text-center",
            "font-sans-md",
            "text-base-darker",
            "text-bold",
            "padding-bottom-105",
          )}
        >
          Incoming record
        </div>
        <div
          role="columnlabel"
          className={classNames(
            "flex-4",
            "text-center",
            "font-sans-md",
            "text-bold",
            "text-base-darker",
            "padding-bottom-105",
          )}
        >
          Potential match
        </div>
      </div>
      {getComparisonRow(0, "Person ID", "", "3502")}
      {getComparisonRow(1, "Patient ID", "234", "3502")}
      {getComparisonRow(2, "First Name", "Jane", "Jan")}
      {getComparisonRow(3, "Last Name", "Doe", "Doe")}
    </div>
  );
}

const RecordComparison: React.FC = () => {
  return (
    <>
      <RecordTable items={patient as Record[]} />
      {getComparisonView()}
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
};

export default RecordComparison;

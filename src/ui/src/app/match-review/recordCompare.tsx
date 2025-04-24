import classNames from "classnames";
import styles from "./recordReview.module.scss";
import { JSX } from "react";

export interface FieldComparisonValues {
  key: number;
  label: string;
  incomingValue: string;
  potentialValue: string;
}

interface RecordCompareProps {
  comparisonFields: FieldComparisonValues[];
}

const valueCellClasses = (idx: number) => [
  "flex-4",
  "border-x",
  "border-accent-cool-light",
  "margin-left-2",
  "padding-x-105",
  "padding-y-1",
  "text-medium",
  idx % 2 ? "bg-accent-cool-lighter" : "bg-white",
];

const readableLabel: Record<string, string> = {
  person_id: "Person ID",
  patient_id: "Patient ID",
  birth_date: "DOB",
  mrn: "MRN",
  ssn: "SSN",
};

function convert2ReadableLabel(label: string) {
  try {
    if (readableLabel[label]) {
      return readableLabel[label];
    }
    return (label.charAt(0).toUpperCase() + label.slice(1)).replaceAll(
      "_",
      " ",
    );
  } catch (_) {
    return label;
  }
}

function getComparisonRow({
  key,
  label,
  incomingValue,
  potentialValue,
}: FieldComparisonValues): JSX.Element {
  const valuesDiffer: boolean =
    !!incomingValue && incomingValue !== potentialValue;

  return (
    <div key={key} role="row" className={classNames("grid-row", "flex-row")}>
      <div
        role="rowheader"
        className={classNames(
          "flex-2",
          "text-semibold",
          "text-accent-cool-dark",
          "padding-y-1",
        )}
      >
        {convert2ReadableLabel(label)}
      </div>
      <div
        role="gridcell"
        className={classNames(
          valueCellClasses(key),
          valuesDiffer && "text-accent-warm-dark text-bold",
        )}
      >
        {incomingValue}
        {valuesDiffer && (
          <span className="usa-sr-only">
            different incoming value highlighted
          </span>
        )}
      </div>
      <div
        role="gridcell"
        className={classNames(
          valueCellClasses(key),
          valuesDiffer && "text-bold",
        )}
      >
        {potentialValue}
        {valuesDiffer && (
          <span className="usa-sr-only">
            different matching value highlighted
          </span>
        )}
      </div>
    </div>
  );
}

const RecordCompare: React.FC<RecordCompareProps> = ({ comparisonFields }) => {
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
        <div className={classNames("flex-2")}></div>
        <div
          role="columnheader"
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
          role="columnheader"
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
      {comparisonFields.map((field: FieldComparisonValues) =>
        getComparisonRow(field),
      )}
    </div>
  );
};

export default RecordCompare;

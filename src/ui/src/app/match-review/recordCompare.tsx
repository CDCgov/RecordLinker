import classNames from "classnames";
import styles from "./recordReview.module.scss";
import { JSX } from "react";

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

function getComparisonRow(
  idx: number,
  label: string,
  incomingValue: string,
  potentialValue: string,
): JSX.Element {
  const valuesDiffer: boolean =
    !!incomingValue && incomingValue !== potentialValue;

  return (
    <div key={idx} role="row" className={classNames("grid-row", "flex-row")}>
      <div
        role="rowheader"
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
          valueCellClasses(idx),
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
          valueCellClasses(idx),
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

const RecordCompare: React.FC = () => {
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
      {getComparisonRow(0, "Person ID", "", "3502")}
      {getComparisonRow(1, "Patient ID", "234", "3502")}
      {getComparisonRow(2, "First name", "Jane", "Jan")}
      {getComparisonRow(3, "Last name", "Doe", "Doe")}
    </div>
  );
};

export default RecordCompare;

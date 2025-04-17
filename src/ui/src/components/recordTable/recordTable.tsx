import { Table } from "@trussworks/react-uswds";
import { Record } from "@/models/record";
import Link from "next/link";
import { JSX } from "react";

export interface RecordTableProps {
  items: Record[];
  withReviewLink?: boolean;
}

function getLinkScoreEl(linkScore: number): JSX.Element {
  if (linkScore > 0.9) {
    return (
      <>
        <span className="text-semibold text-good">{linkScore}</span>{" "}
        <span className="usa-sr-only">good</span>
      </>
    );
  } else if (linkScore > 0.8) {
    return (
      <>
        <span className="text-semibold text-okay">{linkScore}</span>{" "}
        <span className="usa-sr-only">okay</span>
      </>
    );
  } else {
    return (
      <>
        <span className="text-semibold text-bad">{linkScore}</span>{" "}
        <span className="usa-sr-only">bad</span>
      </>
    );
  }
}

function getTableRow(record: Record, withReviewLink: boolean): JSX.Element {
  return (
    <tr key={record.id}>
      <td>
        <span className="text-bold">
          {record.patient.LastName}, {record.patient.firstName}
        </span>
        <br />
        <span className="text-base">DOB: 2/21/1976</span>
      </td>
      <td>
        <span>4/28/2024</span>
        <br />
        <span className="text-base">10:57 AM</span>
      </td>
      <td>
        <span>{record.dataStream.name}</span>
        <br />
        <span className="text-base">{record.dataStream.type}</span>
      </td>
      <td width={160} className="text-center">
        {getLinkScoreEl(record.linkScore)}
      </td>
      {withReviewLink && (
        <td width={58} className="text-center">
          <Link className="usa-link" href={`/record-review/${record.id}`}>
            Review
          </Link>
        </td>
      )}
    </tr>
  );
}

const RecordTable: React.FC<RecordTableProps> = ({
  items,
  withReviewLink = false,
}) => {
  return (
    <Table fullWidth className="usa-table--record-linker">
      <thead>
        <tr>
          <th>Patient</th>
          <th>
            <span className="descending-order">Received on</span>
          </th>
          <th>Data stream</th>
          <th>Link Score</th>
          {withReviewLink && <th>Actions</th>}
        </tr>
      </thead>
      <tbody>
        {items.map((record: Record) => getTableRow(record, withReviewLink))}
      </tbody>
    </Table>
  );
};

export default RecordTable;

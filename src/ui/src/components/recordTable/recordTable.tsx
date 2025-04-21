import { Table } from "@trussworks/react-uswds";
import { Record } from "@/models/record";
import Link from "next/link";
import { JSX } from "react";
import { PAGES } from "@/utils/constants";

export interface RecordTableProps {
  items: Record[];
  withReviewLink?: boolean;
}

function getTableRow(record: Record, withReviewLink: boolean): JSX.Element {
  return (
    <tr key={record.id}>
      <td>
        <span className="text-bold text-base-darker">
          {record.patient.lastName}, {record.patient.firstName}
        </span>
        <br />
        <span className="text-base">
          DOB: {record.patient.dob.toLocaleDateString()}
        </span>
      </td>
      <td>
        <span>{record.receivedOn.toLocaleDateString()}</span>
        <br />
        <span className="text-base">
          {record.receivedOn.toLocaleTimeString([], {
            hour: "numeric",
            minute: "2-digit",
            hour12: true,
          })}
        </span>
      </td>
      <td>
        <span>{record.dataStream.name}</span>
        <br />
        <span className="text-base">{record.dataStream.type}</span>
      </td>
      <td width={160} className="text-center">
        <span className="text-bold text-base-darker">{record.linkScore}</span>
      </td>
      {withReviewLink && (
        <td width={58} className="text-center">
          <Link
            className="usa-link"
            href={`${PAGES.RECORD_REVIEW}/${record.id}`}
          >
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

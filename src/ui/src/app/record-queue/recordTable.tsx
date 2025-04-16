import { Table } from "@trussworks/react-uswds";
import { Record } from "@/models/record";
import Link from "next/link";
import { JSX } from "react";

export interface RecordTableProps {
  items: Record[];
}

function getTableRow(record: Record): JSX.Element {
  return (
    <tr>
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
      <td width={146} className="text-center">
        <span className="text-semibold text-good">{record.linkScore}</span>
      </td>
      <td width={58} className="text-center">
        <Link className="usa-link" href={`/record-review/${record.id}`}>
          Review
        </Link>
      </td>
    </tr>
  );
}

const RecordTable: React.FC<RecordTableProps> = ({ items }) => {
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
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {items.map((record: Record) => getTableRow(record))}
        <tr>
          <td>
            <span className="text-bold">Simpson, Jon</span>
            <br />
            <span className="text-base">DOB: 2/21/1976</span>
          </td>
          <td>
            <span>4/28/2024</span>
            <br />
            <span className="text-base">10:57 AM</span>
          </td>
          <td>
            <span>Disease Surveillance System</span>
            <br />
            <span className="text-base">ELR</span>
          </td>
          <td width={146} className="text-center">
            <span className="text-semibold text-good">.92</span>
          </td>
          <td width={58} className="text-center">
            <Link className="usa-link" href="/record-review/123">
              Review
            </Link>
          </td>
        </tr>
      </tbody>
    </Table>
  );
};

export default RecordTable;

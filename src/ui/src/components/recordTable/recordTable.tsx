import { Table } from "@trussworks/react-uswds";
import { RecordMatch } from "@/models/recordMatch";
import Link from "next/link";
import { JSX } from "react";
import { PAGES } from "@/utils/constants";
import InfoTooltip from "../infoTooltip/infoTooltip";

const linkScoreDesc = `Refers to a weighted statistic between 0 and 1
that measures how well an incoming patient
record matches a group of linked records, defined
under a single Person ID. It represents match
quality, not probability, since match thresholds
are user-defined based on a jurisdiction's desired
balance between automation and manual review.`;

export interface RecordTableProps {
  items: RecordMatch[];
  withReviewLink?: boolean;
  withSortIndicator?: boolean;
}

function getTableRow(
  record: RecordMatch,
  withReviewLink: boolean,
): JSX.Element {
  return (
    <tr key={record.incoming_record?.patient_id}>
      <td>
        <span className="text-bold text-base-darker">
          {record.incoming_record?.last_name},{" "}
          {record.incoming_record?.first_name}
        </span>
        <br />
        <span className="text-base">
          DOB: {record.incoming_record?.birth_date?.toLocaleDateString()}
        </span>
      </td>
      <td>
        <span>{record.incoming_record?.received_on?.toLocaleDateString()}</span>
        <br />
        <span className="text-base">
          {record.incoming_record?.received_on?.toLocaleTimeString([], {
            hour: "numeric",
            minute: "2-digit",
            hour12: true,
          })}
        </span>
      </td>
      <td>
        <span>{record.incoming_record?.data_stream.system}</span>
        <br />
        <span className="text-base">
          {record.incoming_record?.data_stream?.type}
        </span>
      </td>
      <td width={185} className="text-center">
        <span className="text-bold text-base-darker">
          {record.potential_match?.[0].link_score
            .toFixed(2)
            .toString()
            .replace(/^0./g, ".")}
        </span>
      </td>
      {withReviewLink && (
        <td width={58} className="text-center">
          <Link
            className="usa-link"
            href={`${PAGES.RECORD_REVIEW}?id=${record.incoming_record?.patient_id}`}
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
  withSortIndicator = false,
}) => {
  return (
    <Table fullWidth className="usa-table--record-linker">
      <thead>
        <tr>
          <th>Patient</th>
          <th>
            <span className={withSortIndicator ? "descending-order" : ""}>
              Received on
            </span>
          </th>
          <th>Data stream</th>
          <th>
            <InfoTooltip text={linkScoreDesc}>Link Score</InfoTooltip>
          </th>
          {withReviewLink && <th>Actions</th>}
        </tr>
      </thead>
      <tbody>
        {items.map((record: RecordMatch) =>
          getTableRow(record, withReviewLink),
        )}
      </tbody>
    </Table>
  );
};

export default RecordTable;

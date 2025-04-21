"use client";

import RecordTable from "@/components/recordTable/recordTable";
import classNames from "classnames";
import { LinkIcon, LinkOffIcon } from "@/components/Icons/icons";
import { Button } from "@trussworks/react-uswds";
import { Patient } from "@/models/patient";

function getComparisonView(incomingPatient: Patient, potentialMatch: Patient) {
  // ToDo I need to retrieve the data

  return (
    <div className={classNames("border-color-light-blue", "border-y-1px")}>
      <div></div>
      <div></div>
      <div></div>
    </div>
  );
}

const RecordComparison: React.FC = () => {
  return (
    <>
      <RecordTable
        items={[
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
        ]}
      />
      {getComparisonView({} as Patient, {} as Patient)}
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

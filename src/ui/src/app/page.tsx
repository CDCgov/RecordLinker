import Link from "next/link";
import classNames from "classnames";
import Image from "next/image";
import style from "./home.module.scss";
import {
  ProcessList,
  ProcessListHeading,
  ProcessListItem,
} from "@trussworks/react-uswds";
import { PAGES } from "@/utils/constants";
import CaptionedImage from "@/components/captionedImage/captionedImage";

const Home: React.FC = () => {
  return (
    <>
      <div className={style.hero}>
        <div
          className={classNames(
            "page-container",
            "page-container--lg",
            "padding-y-10",
            "grid-row",
            "flex-row",
            "flex-align-center",
            "flex-justify",
            style.section,
          )}
        >
          <div className="grid-col-7">
            <h1 className="font-alt-xl margin-bottom-2 margin-top-0">
              Control how patient records are matched and merged
            </h1>
            <p>
              Record Linker offers a best-in-class algorithm that allows your
              jurisdiction to link incomplete and disparate patient records —
              both within and across public health systems — giving you more
              complete and accurate patient health profiles.
            </p>
            <Link
              className="usa-button padding-x-7 margin-top-2"
              href={PAGES.RECORD_QUEUE}
            >
              Launch Demo
            </Link>
          </div>
          <Image
            src="/images/record-linker-diagram-1.svg"
            width={300}
            height={300}
            alt="multiple health data sources convey into a single one"
          />
        </div>
      </div>
      <div
        className={classNames(
          "page-container",
          "page-container--lg",
          "padding-top-7",
          style.section,
        )}
      >
        <h2>What is it?</h2>
        <p className="margin-top-1 margin-bottom-6">
          Record Linker is an open-source tool that uses a configurable,
          multi-phase algorithm to efficiently link and deduplicate patient
          records across public health systems and jurisdictions. Compared to
          existing record linkage tools, our solution offers a high degree of
          transparency, customization, and precision, allowing your jurisdiction
          to control exactly how patient records are matched and merged.
        </p>
        <h2>How does it work?</h2>
        <p className="margin-top-1">
          With the Record Linker demo, public health staff can look under the
          hood to see how our algorithm matches and scores patient records,
          highlighting edge cases that show the logic behind each Link Score.
        </p>
        <br />
        <p className="text-bold">
          Record Linker analyzes patient records using a four-phase linkage
          process:{" "}
        </p>
        <ProcessList className="margin-top-1 margin-bottom-2">
          <ProcessListItem>
            <ProcessListHeading type="h3" className="font-sans-md">
              Blocking phase
            </ProcessListHeading>
            <p>
              Uses coarse field-matching parameters to identify “roughly
              similar” records from the database. For example, it can retrieve
              all records where the first name starts with “John” and the last
              name starts with “Smit.” This narrows down the set of potential
              matches, keeping the process efficient.
            </p>
          </ProcessListItem>
          <ProcessListItem>
            <ProcessListHeading type="h3" className="font-sans-md">
              Evaluation phase
            </ProcessListHeading>
            <p>
              Uses fine-grained fuzzy matching to assess how closely related the
              blocked matches are, based on different attributes than those used
              for blocking. Each record receives a Link Score reflecting how
              closely its values align.
            </p>
          </ProcessListItem>
          <ProcessListItem>
            <ProcessListHeading type="h3" className="font-sans-md">
              Pass phase
            </ProcessListHeading>
            <p>
              Repeats the blocking and evaluation steps as needed to catch
              matches that might be missed in a single run, accounting for
              missing fields or changes over time (e.g., a person moving and
              updating their address).
            </p>
          </ProcessListItem>
          <ProcessListItem>
            <ProcessListHeading type="h3" className="font-sans-md">
              Aggregation phase
            </ProcessListHeading>
            <p>
              Combines scores from the evaluation phase and sorts the results to
              determine the most likely patient match.
            </p>
          </ProcessListItem>
        </ProcessList>
        <CaptionedImage
          width={792}
          height={372}
          src="/images/record-linker-process-min.png"
          alt="record linker algorithm steps explained"
          caption={
            <>
              Record Linker process diagram &mdash;{" "}
              <a
                href="/files/record_linker_process_diagram.pdf"
                download
                className="usa-link"
              >
                download a diagram
              </a>{" "}
              with additional details.
            </>
          }
        />
        <h2 className="margin-top-8">Where we&apos;re going </h2>
        <p className="margin-top-1 margin-bottom-4">
          Record Linker is currently at the product validation stage. Our team
          is working with users at several public health jurisdictions to
          develop a standalone Master Patient Index that enables patient
          matching across internal tools (e.g., disease surveillance, vital
          records, and immunization information systems), thereby improving
          interoperability between these datasets.
        </p>
        <CaptionedImage
          width={470}
          height={371}
          className="margin-bottom-5"
          src="/images/record-linker-data-flow-min.png"
          alt="multiple health data sources convey into a single one"
          caption="Record Linker can match records across internal public health tools."
        />
      </div>
      <div
        className={classNames(
          "page-container",
          "page-container--lg",
          "padding-top-4",
          "padding-bottom-6",
          "border-top-1px",
          "border-color-light-blue",
          "grid-row",
          "flex-column",
          "flex-align-center",
          style.section,
          style.footnotes,
        )}
      >
        <h2>Explore Record Linker</h2>
        <p className="text-center text-thin">
          Try out our demo using sample data.
        </p>
        <Link
          className="usa-button padding-x-7 margin-top-2"
          href={PAGES.RECORD_QUEUE}
        >
          Launch Demo
        </Link>
      </div>
    </>
  );
};

export const metadata = {
  title: "Record linker | Home",
};

export default Home;

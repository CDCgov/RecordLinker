import Link from "next/link";
import Image from "next/image";
import classNames from "classnames";
import style from "./home.module.scss";
import {
  ProcessList,
  ProcessListHeading,
  ProcessListItem,
} from "@trussworks/react-uswds";
import { PAGES } from "@/utils/constants";

const Home: React.FC = () => {
  return (
    <>
      <div className={style.hero}>
        <div
          className={classNames(
            "page-container--lg",
            "padding-y-10",
            "grid-row",
            "flex-row",
            "flex-align-center",
            "flex-justify",
            style.section,
          )}
        >
          <div className="grid-col-6">
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
          "page-container--lg",
          "padding-top-7",
          "padding-x-6",
          style.section,
        )}
      >
        <h2>What is it?</h2>
        <p className="margin-top-1">
          Nunc hendrerit efficitur lorem ut molestie. Suspendisse eleifend eros
          mi, congue varius nibh sagittis sed. Phasellus quis ex non odio
          sollicitudin convallis. Pellentesque libero nulla, fermentum non erat
          at, vulputate facilisis nisl. Nam vitae pulvinar massa, vitae
          vulputate sapien. Sed nec urna nec felis dictum luctus. Pellentesque
          iaculis nisl nisi, at auctor mauris auctor id. Class aptent taciti
          sociosqu ad litora torquent per conubia nostra, per inceptos
          himenaeos. Vivamus posuere vitae dui eget auctor. Aenean massa sapien,
          placerat ac ipsum non, lobortis maximus dui. Suspendisse at tincidunt
          sapien.
        </p>
        <Image
          className="margin-y-5"
          width={710}
          height={310}
          src="/images/record-linker-diagram-2.png"
          alt="multiple health data sources convey into a single one"
        />
        <h2>How does it work?</h2>
        <p className="margin-top-1">
          Nunc hendrerit efficitur lorem ut molestie. Suspendisse eleifend eros
          mi, congue varius nibh sagittis sed. Phasellus quis ex non odio
          sollicitudin convallis. Pellentesque libero nulla, fermentum non erat
          at, vulputate facilisis nisl. Nam vitae pulvinar massa, vitae
          vulputate sapien. Sed nec urna nec felis dictum luctus. Pellentesque
          iaculis nisl nisi, at auctor mauris auctor id. Class aptent taciti
          sociosqu ad litora torquent per conubia nostra, per inceptos
          himenaeos. Vivamus posuere vitae dui eget auctor. Aenean massa sapien,
          placerat ac ipsum non, lobortis maximus dui. Suspendisse at tincidunt
          sapien.
        </p>

        <ProcessList className="margin-y-3">
          <ProcessListItem>
            <ProcessListHeading type="h3">Frame the problem</ProcessListHeading>
            <p>
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam sed
              condimentum mauris.
            </p>
          </ProcessListItem>
          <ProcessListItem>
            <ProcessListHeading type="h3">
              Determine data sources
            </ProcessListHeading>
            <p>
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam sed
              condimentum mauris.
            </p>
          </ProcessListItem>
          <ProcessListItem>
            <ProcessListHeading type="h3">
              Configure the algorithm
            </ProcessListHeading>
            <p>
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam sed
              condimentum mauris.
            </p>
          </ProcessListItem>
          <ProcessListItem>
            <ProcessListHeading type="h3">
              Test (and adjust as needed)
            </ProcessListHeading>
            <p>
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam sed
              condimentum mauris.
            </p>
          </ProcessListItem>
        </ProcessList>
      </div>
      <div
        className={classNames(
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
        <h2>Footer header title lorem ipsum</h2>
        <p className="text-center text-thin">
          Check out the Record Linker demo to try
          <br />
          out features using sample data.
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

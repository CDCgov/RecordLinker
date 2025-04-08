import Link from "next/link";
import Image from "next/image";
import style from "./page.module.scss";

export default function Home() {
  return (
    <>
      <div className={`${style.overview}`}>
        <div
          className={`page-container--lg padding-y-10 grid-row flex-row flex-align-center flex-justify ${style.section}`}
        >
          <div className={`grid-col-6`}>
            <h1 className="font-alt-xl margin-bottom-3">Lorem ipsum title</h1>
            <p>
              Short overview description of Record Linker, Lorem ipsum dolor sit
              amet, consectetur adipiscing elit. Etiam sed condimentum mauris.
              Duis a felis nec mi convallis feugiat. Suspendisse commodo tellus
              vitae sodales euismod. Cras vitae tellus dolor.
            </p>
            <Link
              className="usa-button padding-x-7 margin-top-2"
              href={"/wizard"}
            >
              Launch Demo
            </Link>
          </div>
          <Image
            src="/record-linker-diagram-1.svg"
            width={300}
            height={300}
            alt="multiple health data sources convey into a single one"
          />
        </div>
      </div>
      <div
        className={`page-container--lg padding-y-7 padding-x-6 ${style.section}`}
      >
        <h2 className="font-sans-xl">What is it?</h2>
        <p className="margin-top-2">
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
        <img
          className="margin-y-5"
          src="/record-linker-diagram-2.png"
          alt="multiple health data sources convey into a single one"
        />
        <h2>How does it work?</h2>
        <p className="margin-top-2">
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
      </div>
      <div
        className={`page-container--lg padding-top-4 padding-bottom-6 border-top-1px grid-row flex-column flex-align-center ${style.section} ${style.footnotes}`}
        style={{ gap: "15px" }}
      >
        <h2>Footer header title lorem ipsum</h2>
        <p className="font-body-md text-center text-thin">
          Check out the Record Linker demo to try
          <br />
          out features using sample data.
        </p>
        <Link className="usa-button padding-x-7 margin-top-2" href={"/wizard"}>
          Launch Demo
        </Link>
      </div>
    </>
  );
}

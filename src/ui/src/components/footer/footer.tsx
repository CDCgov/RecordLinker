import Image from "next/image";
import styles from "./footer.module.scss";
import classNames from "classnames";

const Footer: React.FC = () => {
  return (
    <footer className={classNames(styles.footer)}>
      <div
        className={classNames(
          "page-container",
          "page-container--xxl",
          "padding-y-3",
          "grid-row",
          "flex-row",
          "flex-align-center",
          "flex-justify",
        )}
      >
        <a href="https://www.cdc.gov/">
          <Image
            src="/images/cdc-logo.svg"
            height={47}
            width={200}
            alt="CDC U.S. centers for disease control and prevention"
          />
        </a>
        <p className="text-white">
          For more information about this solution, send us an email at{" "}
          <a className="text-white text-bold" href="mailto:dibbs@cdc.gov">
            dibbs@cdc.gov
          </a>
        </p>
      </div>
    </footer>
  );
};

export default Footer;

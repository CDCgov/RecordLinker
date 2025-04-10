import Image from "next/image";
import styles from "./footer.module.scss";
import classNames from "classnames";

const Footer: React.FC = () => {
  return (
    <footer
      className={classNames(
        "padding-x-10",
        "padding-y-3",
        "grid-row",
        "flex-row",
        "flex-align-center",
        "flex-justify",
        styles.footer,
      )}
    >
      <Image
        src="/cdc-logo.svg"
        height={47}
        width={200}
        alt="CDC logo. U.S. centers for disease control and prevention"
      />
      <p className="text-white">
        For more information about this solution, send us an email at{" "}
        <a className="text-white text-bold" href="mailto:dibbs@cdc.gov">
          dibbs@cdc.gov
        </a>
      </p>
    </footer>
  );
};

export default Footer;

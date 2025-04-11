import Image from "next/image";
import styles from "./header.module.scss";
import Link from "next/link";
import classNames from "classnames";

const Header: React.FC = () => {
  return (
    <header className={`padding-x-10 padding-y-4 ${styles.header}`}>
      <Link
        href="/"
        className={classNames(
          "text-no-underline",
          "font-serif-xl",
          "text-white",
          "grid-row",
          "flex-row",
          "flex-align-center",
        )}
      >
        <Image
          src="/record-linker-logo.svg"
          width={30}
          height={30}
          alt="record linker logo"
          className="margin-right-105 "
        />
        Record Linker - Demo Site
      </Link>
    </header>
  );
};

export default Header;

import Image from "next/image";
import styles from "./header.module.scss";

const Header: React.FC = () => {
  return (
    <header className={`padding-x-10 padding-y-3 ${styles.header}`}>
      <Image
        src="/record-linker-logo.svg"
        width={30}
        height={30}
        alt="record linker logo"
      />
      <span className={`font-serif-xl margin-left-105 text-white `}>
        Record Linker - Demo Site
      </span>
    </header>
  );
};

export default Header;

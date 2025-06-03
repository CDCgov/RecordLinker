import { Suspense } from "react";
import Image from "next/image";
import styles from "./header.module.scss";
import Link from "next/link";
import classNames from "classnames";
import Menu from "@/components/menu/menu";
import { PAGES } from "@/utils/constants";

const Header: React.FC = () => {
  return (
    <header className={` ${styles.header}`}>
      <div className="page-container page-container--xxl grid-row flex-row flex-justify padding-y-4">
        <Link
          href={PAGES.LANDING}
          className={classNames(
            "text-no-underline",
            "font-serif-xl",
            "text-white",
            "grid-row",
            "flex-row",
            "flex-align-center",
            styles.logo,
          )}
        >
          <Image
            src="/images/record-linker-logo.svg"
            width={30}
            height={30}
            alt="record linker logo"
            className="margin-right-105 "
          />
          DIBBs Record Linker - Demo Site
        </Link>
        <Suspense>
          <Menu />
        </Suspense>
      </div>
    </header>
  );
};

export default Header;

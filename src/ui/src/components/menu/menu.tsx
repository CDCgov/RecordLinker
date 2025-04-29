"use client";

import classNames from "classnames";
import { usePathname } from "next/navigation";
import { PAGES } from "@/utils/constants";
import { LaunchIcon } from "../icons/icons";
import styles from "./menu.module.scss";

const Menu: React.FC = () => {
  const pathname = usePathname();

  return (
    <nav className={classNames("grid-row", "flex-row", "flex-align-center")}>
      {pathname !== PAGES.LANDING && (
        <a
          href="/files/config-preview.pdf"
          target="_blank"
          rel="noopener noreferrer"
          className={classNames(
            "text-white",
            "text-semibold",
            "text-no-underline",
            styles.algoConfigLink,
          )}
        >
          Preview algorithm configuration
          <LaunchIcon size={1} className="text-sub margin-left-1" />
        </a>
      )}
    </nav>
  );
};

export default Menu;

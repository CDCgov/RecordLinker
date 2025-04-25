"use client";

import { usePathname } from "next/navigation";
import { LaunchIcon } from "../icons/icons";
import { PAGES } from "@/utils/constants";

const Menu: React.FC = () => {
  const pathname = usePathname();

  return (
    <nav>
      {pathname !== PAGES.LANDING && (
        <a
          href="/files/config-preview.pdf"
          target="_blank"
          rel="noopener noreferrer"
          className="text-white text-semibold text-no-underline"
        >
          <span className="font-sans-sm">Preview algorithm configuration</span>
          <LaunchIcon size={1} className="text-middle margin-left-1" />
        </a>
      )}
    </nav>
  );
};

export default Menu;

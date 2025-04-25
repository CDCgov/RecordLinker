import Link from "next/link";
import classNames from "classnames";
import { BackArrowIcon } from "../icons/icons";
import style from "./backToLink.module.scss";

export interface BackToLinkProps {
  text: string;
  href: string;
}

const BackToLink: React.FC<BackToLinkProps> = ({ text = "Back", href }) => {
  return (
    <Link
      href={href}
      className={classNames(
        "usa-link",
        "text-no-underline",
        "font-sans-sm",
        "text-bold",
        "grid-row",
        "flex-row",
        "flex-align-center",
        style.backToLink,
      )}
    >
      <BackArrowIcon size={3} className="margin-right-1" />
      {text}
    </Link>
  );
};

export default BackToLink;

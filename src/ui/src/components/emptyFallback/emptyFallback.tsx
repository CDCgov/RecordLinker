import classNames from "classnames";
import Image from "next/image";
import styles from "./emptyFallback.module.scss";

export interface EmptyFallbackProps {
  message: React.ReactNode;
}

const EmptyFallback: React.FC<EmptyFallbackProps> = ({ message }) => {
  return (
    <div
      className={classNames(
        "padding-y-10",
        "grid-row",
        "flex-column",
        "flex-align-center",
      )}
    >
      <Image src="/images/empty-folder.png" width={300} height={300} alt="" />
      <p
        className={classNames(
          "text-base-dark",
          "margin-top-2",
          "margin-bottom-3",
          "text-center",
          styles.message,
        )}
      >
        {message}
      </p>
    </div>
  );
};

export default EmptyFallback;

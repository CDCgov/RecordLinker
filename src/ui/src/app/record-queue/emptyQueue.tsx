import classNames from "classnames";
import Image from "next/image";

const EmptyQueue: React.FC = () => {
  return (
    <div
      className={classNames(
        "padding-y-10",
        "grid-row",
        "flex-column",
        "flex-align-center",
      )}
    >
      <Image src="/images/empty-folder-1.png" width={300} height={300} alt="" />
      <p
        className={classNames(
          "font-body-lg",
          "text-base-dark",
          "margin-top-2",
          "margin-bottom-3",
        )}
      >
        No cases left to review
      </p>
    </div>
  );
};

export default EmptyQueue;

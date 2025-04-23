import classNames from "classnames";
import styles from "./serverError.module.scss";
import { InfoIcon } from "../Icons/icons";

const ServerError: React.FC = () => {
  return (
    <div
      className={classNames(
        "grid-row",
        "flex-row",
        "flex-justify-center",
        styles.serverError,
      )}
    >
      <div>
        <h2 className="font-alt-xl text-secondary-darker margin-bottom-1">
          <InfoIcon className="text-sub" size={5} /> Internal server error
        </h2>
        <p className="text-semibold margin-left-05 margin-bottom-2">
          There&apos;s an issue with the DIBBs server
        </p>
        <div className={classNames("padding-205", styles.instructions)}>
          <p className="text-bold margin-bottom-2">Please try the following:</p>
          <ul className="margin-left-3">
            <li>
              <span className="text-bold">Refresh the page:</span> Sometimes, a
              simple refresh can solve the problem.
            </li>
            <li>
              <span className="text-bold">Check back later:</span> We&apos;re
              working hard to fix the issue.
            </li>
            <li>
              <span className="text-bold">Contact support:</span> If the problem
              persists, please reach out to your administrator.
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ServerError;

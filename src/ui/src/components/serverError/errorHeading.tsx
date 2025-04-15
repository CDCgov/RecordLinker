"use client";
import { Icon } from "@trussworks/react-uswds";

const ErrorHeading: React.FC<React.PropsWithChildren> = ({ children }) => {
  return (
    <h2 className="text-secondary-darker">
      <Icon.Info /> {children}
    </h2>
  );
};

export default ErrorHeading;

"use client";
import { Icon } from "@trussworks/react-uswds";

const ErrorHeading: React.FC<React.PropsWithChildren> = ({ children }) => {
  return (
    <h2 className="font-alt-xl text-secondary-darker margin-bottom-1">
      <Icon.Info className="text-sub" size={5} /> {children}
    </h2>
  );
};

export default ErrorHeading;

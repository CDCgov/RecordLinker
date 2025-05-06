import { Alert } from "@trussworks/react-uswds";
import { toast, ToastOptions } from "react-toastify";

export enum ToastType {
  SUCCESS = "success",
  ERROR = "error",
  WARNING = "warning",
  INFO = "info",
}

const TOAST_AUTO_CLOSE_MS = 5000;

interface CustomToastProps {
  type: ToastType;
  heading?: React.ReactNode;
  content: React.ReactNode;
}

const CustomToast: React.FC<CustomToastProps> = ({
  heading,
  type,
  content,
}: CustomToastProps) => {
  return (
    <Alert
      className="width-full radius-md margin-top-0 font-sans-md"
      type={type}
      heading={heading}
      headingLevel={"h2"}
    >
      {content}
    </Alert>
  );
};

export function showToast(
  type: ToastType,
  content: React.ReactNode,
  heading: React.ReactNode = undefined,
  options?: ToastOptions<CustomToastProps>,
) {
  toast<CustomToastProps>(
    <CustomToast type={type} content={content} heading={heading} />,
    {
      ...options,
      type: type,
      autoClose: TOAST_AUTO_CLOSE_MS,
    },
  );
}

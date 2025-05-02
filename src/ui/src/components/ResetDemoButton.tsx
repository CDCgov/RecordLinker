"use client";

import { API_URL } from "@/utils/constants";
import { Button } from "@trussworks/react-uswds";

const ResetDemoButton: React.FC<React.PropsWithChildren> = ({}) => {
  const handleResetDemo = async () => {
    const response = await fetch(`${API_URL}/demo/reset`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });
    if (response.ok) {
      window.location.reload();
    } else {
      console.error("Failed to reset demo data");
    }
    false;
  };
  return (
    <Button
      type="button"
      outline
      className="margin-left-2"
      style={{ whiteSpace: "nowrap" }}
      onClick={handleResetDemo}
    >
      Reset match queue
    </Button>
  );
};

export default ResetDemoButton;

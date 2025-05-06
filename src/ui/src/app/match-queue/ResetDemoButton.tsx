"use client";

import { Button } from "@trussworks/react-uswds";
import { resetDemoData } from "@/data/matchQueue";

const ResetDemoButton: React.FC = () => {
  const handleResetDemo = async () => {
    const response = await resetDemoData();
    if (response.ok) {
      window.location.reload();
    } else {
      console.error("Failed to reset demo data");
    }
  };
  return (
    <Button
      type="button"
      outline
      className="margin-left-2 text-no-wrap"
      onClick={handleResetDemo}
    >
      Reset match queue
    </Button>
  );
};

export default ResetDemoButton;

"use client";

import { Button } from "@trussworks/react-uswds";
import { resetDemoData } from "@/data/matchQueue";
import { showToast, ToastType } from "@/components/toast/toast";

const ResetDemoButton: React.FC = () => {
  const handleResetDemo = async () => {
    try {
      await resetDemoData();
      window.location.reload();
    } catch (e) {
      console.error(e);
      showToast(
        ToastType.ERROR,
        "We were unable to process your request. Please try again.",
      );
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

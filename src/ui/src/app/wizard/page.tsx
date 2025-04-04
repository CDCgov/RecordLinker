"use client";

import { Textarea } from "@trussworks/react-uswds";
import { useEffect, useState } from "react";
import { getAlgoDibbsDefault } from "@/data/algorithm";

const Wizard: React.FC = () => {
  const [content, setContent] = useState("");

  async function retrieveDibbsDefault() {
    const dibbsAlgo = await getAlgoDibbsDefault();
    setContent(JSON.stringify(dibbsAlgo));
  }

  useEffect(() => {
    retrieveDibbsDefault();
  }, []);

  return (
    <>
      <h1>Wizard placeholder!</h1>
      <Textarea defaultValue={content} />
    </>
  );
};

export default Wizard;

"use client";

import {
  Button,
  Textarea,
  Link,
  Checkbox,
  Radio,
} from "@trussworks/react-uswds";
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
    <div className="page-container--lg">
      <h1>Wizard placeholder!</h1>
      <Button>test btn</Button>
      <br />
      <Link href="#">test link</Link>
      <Checkbox
        id="checkbox"
        name="checkbox"
        label="My Checkbox"
        labelDescription="This is optional text that can be used to describe the label in more detail."
        tile
      />
      <Radio
        id="input-radio"
        name="input-radio"
        label="My Radio Button"
        labelDescription="This is optional text that can be used to describe the label in more detail."
        tile
      />
      {/*<Textarea defaultValue={content} />*/}
    </div>
  );
};

export default Wizard;

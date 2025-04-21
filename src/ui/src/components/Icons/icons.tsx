"use client";

import { ComponentProps } from "react";
import { Icon } from "@trussworks/react-uswds";

type RecordLinkerIconProp = ComponentProps<"svg"> & { size: number };

export const InfoIcon: React.FC<RecordLinkerIconProp> = (props) => (
  <Icon.Info {...props} />
);

export const BackArrowIcon: React.FC<RecordLinkerIconProp> = (props) => (
  <Icon.ArrowBack {...props} />
);

export const LinkIcon: React.FC<RecordLinkerIconProp> = (props) => (
  <Icon.Link {...props} />
);

export const LinkOffIcon: React.FC<RecordLinkerIconProp> = (props) => (
  <Icon.LinkOff {...props} />
);

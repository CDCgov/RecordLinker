import { Tooltip } from "@trussworks/react-uswds";
import { InfoOutlineIcon } from "../Icons/icons";
import { JSX } from "react";
import React from "react";

export interface InfoTooltipProps extends React.PropsWithChildren {
  text: string;
}

const InfoTooltip: React.FC<InfoTooltipProps> = ({ children, text }) => {
  type InfoIconWrapperProps = React.PropsWithChildren<{
    className?: string;
  }> &
    JSX.IntrinsicElements["div"] &
    React.RefAttributes<HTMLDivElement>;

  const InfoIconWrapperForwardRef: React.ForwardRefRenderFunction<
    HTMLDivElement,
    InfoIconWrapperProps
  > = ({ className, children, ...tooltipProps }: InfoIconWrapperProps, ref) => (
    <div ref={ref} className={className} {...tooltipProps}>
      {children}
      <span className="text-primary-light display-inline-bock text-middle margin-left-05">
        <InfoOutlineIcon size={1} />
      </span>
    </div>
  );

  const InfoIconWrapper = React.forwardRef(InfoIconWrapperForwardRef);

  return (
    <Tooltip<InfoIconWrapperProps> label={text} asCustom={InfoIconWrapper}>
      {children}
    </Tooltip>
  );
};

export default InfoTooltip;

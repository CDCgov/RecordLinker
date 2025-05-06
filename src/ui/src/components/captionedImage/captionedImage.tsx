import { ReactNode } from "react";
import Image from "next/image";
import classNames from "classnames";

type ImageProps = Omit<React.ComponentProps<typeof Image>, "className">;

export interface CaptionedImageProps extends ImageProps {
  caption: ReactNode;
  className?: string;
}

const CaptionedImage: React.FC<CaptionedImageProps> = (props) => {
  const { caption, className, ...imgProps } = props;
  return (
    <div className={classNames("grid-row", "flex-justify-center", className)}>
      <Image {...imgProps} />
      <p className="text-center text-italic margin-top-205">{caption}</p>
    </div>
  );
};

export default CaptionedImage;

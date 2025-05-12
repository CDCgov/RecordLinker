import { ReactNode } from "react";
import Image from "next/image";
import classNames from "classnames";
import captionedImageStyle from "./captionedImage.module.scss";

type ImageProps = Omit<React.ComponentProps<typeof Image>, "className">;

export interface CaptionedImageProps extends ImageProps {
  caption: ReactNode;
  className?: string;
}

const CaptionedImage: React.FC<CaptionedImageProps> = (props) => {
  const { caption, className, alt, ...imgProps } = props;
  return (
    <div
      className={classNames(
        "grid-row",
        "flex-justify-center",
        className,
        captionedImageStyle.wrapper,
      )}
    >
      <Image alt={alt} {...imgProps} />
      <p className="text-center text-italic text-base-dark margin-top-205">
        {caption}
      </p>
    </div>
  );
};

export default CaptionedImage;

import { DetailedHTMLProps, ImgHTMLAttributes } from "react";

type ImageProps =  DetailedHTMLProps<ImgHTMLAttributes<HTMLImageElement>, HTMLImageElement>;

const Image: React.FC<ImageProps> = (props)=>{
    const source = `${process.env.NEXT_PUBLIC_IMG_PATH || ''}${props.src}`;

    return(
        <img {...props} src={source} />
    )
};

export default Image;
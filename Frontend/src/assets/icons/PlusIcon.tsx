import { FC } from "react";
import { IconProps } from "./interface";

export const PlusIcon: FC<IconProps> = ({ className, ...props }) => {
  return (
    <svg
      fill="none"
      strokeWidth="2"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      xmlns="http://www.w3.org/2000/svg"
      className={`lucide lucide-plus-icon lucide-plus ${className ?? ""}`}
      {...props}
    >
      <path d="M5 12h14"/>
      <path d="M12 5v14"/>
    </svg>
  );
};

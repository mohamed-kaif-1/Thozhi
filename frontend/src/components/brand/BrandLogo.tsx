import React from "react";
import Image from "next/image";
import { cn } from "@/lib/utils";

export type LogoVariant = "full" | "horizontal" | "icon" | "symbol" | "app-icon" | "mono";
export type LogoTheme = "dark" | "light" | "mono";

export interface BrandLogoProps {
  variant?: LogoVariant;
  theme?: LogoTheme;
  className?: string;
  width?: number;
  height?: number;
  alt?: string;
  priority?: boolean;
}

export const BrandLogo: React.FC<BrandLogoProps> = ({
  variant = "horizontal",
  theme = "dark",
  className,
  width,
  height,
  alt = "THOZHI — AI Personal Planning Assistant",
  priority = false,
}) => {
  // Determine correct asset path based on variant and theme
  let src = "/brand/thozhi-logo.png";
  let defaultWidth = 160;
  let defaultHeight = 44;

  if (variant === "icon" || variant === "symbol") {
    src = "/brand/thozhi-icon.png";
    defaultWidth = 40;
    defaultHeight = 40;
  } else if (variant === "app-icon") {
    src = "/brand/thozhi-app-icon.png";
    defaultWidth = 40;
    defaultHeight = 40;
  } else if (variant === "mono") {
    src = "/brand/thozhi-logo-mono.png";
    defaultWidth = 160;
    defaultHeight = 240;
  } else if (variant === "full") {
    src = theme === "light" ? "/brand/thozhi-logo-light.png" : "/brand/thozhi-logo.png";
    defaultWidth = 160;
    defaultHeight = 240;
  } else if (variant === "horizontal") {
    src =
      theme === "light"
        ? "/brand/thozhi-logo-horizontal-light.png"
        : "/brand/thozhi-logo-horizontal.png";
    defaultWidth = 160;
    defaultHeight = 44;
  }

  return (
    <div className={cn("relative inline-flex items-center justify-center flex-shrink-0", className)}>
      <Image
        src={src}
        alt={alt}
        width={width || defaultWidth}
        height={height || defaultHeight}
        priority={priority}
        className="w-full h-full object-contain pointer-events-none select-none"
      />
    </div>
  );
};

export default BrandLogo;


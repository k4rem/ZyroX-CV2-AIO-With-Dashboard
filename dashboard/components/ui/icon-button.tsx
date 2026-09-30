"use client";

import * as React from "react";
import { Button, type ButtonProps } from "@/components/ui/button";
import { Tooltip } from "@/components/ui/tooltip";

export interface IconButtonProps extends Omit<ButtonProps, "children" | "asChild"> {
  /** Required: becomes both aria-label and the tooltip (DS §11, §28). */
  label: string;
  children: React.ReactNode;
  tooltipSide?: "top" | "bottom" | "start" | "end";
  tooltipDisabled?: boolean;
}

export const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ label, children, variant = "ghost", size = "icon", tooltipSide = "bottom", tooltipDisabled, ...props }, ref) => (
    <Tooltip content={label} side={tooltipSide} disabled={tooltipDisabled}>
      <Button ref={ref} variant={variant} size={size} aria-label={label} type="button" {...props}>
        {children}
      </Button>
    </Tooltip>
  ),
);
IconButton.displayName = "IconButton";

"use client";

import React from "react";
import { TheSVGIcon, TheSVGIconProps, TheSVGIconName } from "./TheSVGIcon";

export type IconName = TheSVGIconName;
export type IconProps = TheSVGIconProps;

/**
 * Standard Icon Component for AgentBreaker.
 * Re-exports TheSVGIcon ensuring TheSVG.org UI icons are the default everywhere.
 */
export const Icon: React.FC<TheSVGIconProps> = (props) => {
  return <TheSVGIcon {...props} />;
};

export { TheSVGIcon };

"use client";

import { ReactNode } from "react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { LuInfo } from "react-icons/lu";

interface InfoTooltipProps {
  content: ReactNode;
  children?: ReactNode;
  side?: "top" | "right" | "bottom" | "left";
}

export function InfoTooltip({ content, children, side = "top" }: InfoTooltipProps) {
  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          {children ? (
            children
          ) : (
            <button
              type="button"
              className="text-shell-muted/70 transition hover:text-shell-fg focus:outline-none"
              aria-label="Information"
            >
              <LuInfo size={14} />
            </button>
          )}
        </TooltipTrigger>
        <TooltipContent
          side={side}
          className="max-w-[250px] bg-shell-2 shadow-xl ring-1 ring-white/10 text-shell-fg"
        >
          <p className="text-xs leading-relaxed">{content}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

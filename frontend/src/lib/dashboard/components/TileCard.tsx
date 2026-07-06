import { LuEllipsis } from "react-icons/lu";
import type { IconType } from "react-icons";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { InfoTooltip } from "./InfoTooltip";

/**
 * White tile shell used across the dashboard. All inner white cards
 * (Team Administration, Most Active Teams, stat tiles) use this.
 */
export function TileCard({
  title,
  subtitle,
  tooltip,
  icon: Icon,
  action = "more",
  className,
  children,
}: {
  title?: string;
  subtitle?: string;
  tooltip?: ReactNode;
  icon?: IconType;
  action?: "more" | "icon" | "none";
  className?: string;
  children: ReactNode;
}) {
  return (
    <div
      className={cn(
        "flex h-full flex-col rounded-3xl bg-tile p-5 text-tile-fg shadow-sm",
        className,
      )}
    >
      {(title || Icon) && (
        <header className="flex items-start justify-between gap-2">
          <div>
            {title && (
              <h3 className="flex items-center gap-1.5 text-sm font-semibold leading-tight text-tile-fg">
                {title}
                {tooltip && <InfoTooltip content={tooltip} />}
              </h3>
            )}
            {subtitle && <p className="mt-1 text-[11px] text-tile-muted">{subtitle}</p>}
          </div>
          {action === "more" && (
            <button
              type="button"
              aria-label="More"
              className="grid h-6 w-6 place-items-center rounded-full text-tile-muted hover:bg-black/5"
            >
              <LuEllipsis size={14} />
            </button>
          )}
          {action === "icon" && Icon && (
            <div className="grid h-6 w-6 place-items-center rounded-full bg-black/90 text-white">
              <Icon size={12} />
            </div>
          )}
        </header>
      )}
      <div className="flex-1">{children}</div>
    </div>
  );
}

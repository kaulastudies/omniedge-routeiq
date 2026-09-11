import Link from "next/link";
import { usePathname } from "next/navigation";
import { useDashboard } from "../store";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const { nav } = useDashboard();
  const pathname = usePathname();

  return (
    <nav className="flex flex-col items-center gap-2 py-2">
      {nav.map((item) => {
        const Icon = item.icon;

        // Overview is root, anything else maps to its ID
        const targetPath = item.id === "overview" ? "/" : `/${item.id}`;
        const active = pathname === targetPath;

        return (
          <Link
            key={item.id}
            href={targetPath}
            aria-label={item.label}
            aria-current={active ? "page" : undefined}
            className={cn(
              "grid h-10 w-10 place-items-center rounded-xl transition-all",
              active
                ? "bg-white/95 text-shell-2 shadow-lg shadow-black/10"
                : "text-shell-fg/70 hover:text-shell-fg hover:bg-white/10",
            )}
          >
            <Icon size={18} />
          </Link>
        );
      })}
    </nav>
  );
}

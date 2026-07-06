"use client";

import * as React from "react";
import { LuMoon, LuSun } from "react-icons/lu";
import { useTheme } from "next-themes";

export function ModeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <button
      onClick={() => setTheme(theme === "light" ? "dark" : "light")}
      type="button"
      className="grid h-10 w-10 place-items-center rounded-xl bg-white/10 text-shell-fg/80 ring-1 ring-white/10 transition hover:bg-white/20 hover:text-shell-fg"
      aria-label="Toggle theme"
    >
      <LuSun className="h-5 w-5 dark:hidden" />
      <LuMoon className="hidden h-5 w-5 dark:block" />
    </button>
  );
}

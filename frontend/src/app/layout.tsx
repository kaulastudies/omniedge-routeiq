import "@/styles.css";
import { type ReactNode } from "react";
import type { Metadata } from "next";

import { ThemeProvider } from "@/components/ui/theme-provider";

export const metadata: Metadata = {
  title: "OmniEdge RouteIQ Dashboard",
  description: "Monitor and simulate AI routing intelligence in real-time.",
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          disableTransitionOnChange
        >
          <div id="root">{children}</div>
        </ThemeProvider>
      </body>
    </html>
  );
}

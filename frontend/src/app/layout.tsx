import "@/styles.css";
import { type ReactNode } from "react";
import type { Metadata } from "next";

import { ThemeProvider } from "@/components/ui/theme-provider";
import { Toaster } from "sonner";

export const metadata: Metadata = {
  title: "OmniEdge RouteIQ Dashboard",
  description: "Monitor and simulate AI routing intelligence in real-time.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="class" defaultTheme="dark" disableTransitionOnChange>
          <div id="root">{children}</div>
          <Toaster richColors closeButton position="top-center" />
        </ThemeProvider>
      </body>
    </html>
  );
}

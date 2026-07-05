import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OmniEdge RouteIQ | Command Nexus",
  description:
    "Hybrid AI routing layer for local inference, cloud escalation, fallback reliability, token savings, and audit trails.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

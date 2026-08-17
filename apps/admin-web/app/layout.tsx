import type { Metadata, Viewport } from "next";

import { ClientAppShell } from "@/components/ClientAppShell";

import "./globals.css";

export const metadata: Metadata = {
  title: "Commerce Engine — Admin",
  description: "Platform and tenant administration",
  manifest: "/manifest.webmanifest",
};

export const viewport: Viewport = {
  themeColor: "#12101a",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ClientAppShell>{children}</ClientAppShell>
      </body>
    </html>
  );
}

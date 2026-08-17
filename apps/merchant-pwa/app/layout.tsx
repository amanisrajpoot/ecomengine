import type { Metadata, Viewport } from "next";

import { ClientAppShell } from "@/components/ClientAppShell";

import "./globals.css";

export const metadata: Metadata = {
  title: "Commerce Engine — Merchant PWA",
  description: "Merchant operations for Commerce Engine",
  manifest: "/manifest.webmanifest",
};

export const viewport: Viewport = {
  themeColor: "#1a1410",
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

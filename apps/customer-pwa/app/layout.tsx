import type { Metadata, Viewport } from "next";

import { ClientAppShell } from "@/components/ClientAppShell";

import "./globals.css";

export const metadata: Metadata = {
  title: "Commerce Engine — Customer PWA",
  description: "Customer shopping experience for Commerce Engine",
  manifest: "/manifest.webmanifest",
};

export const viewport: Viewport = {
  themeColor: "#0f1c14",
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

import { Sora, Fraunces } from "next/font/google";
import type { Metadata, Viewport } from "next";

import { AppShell } from "../components/AppShell";
import "./globals.css";

const sora = Sora({ subsets: ["latin"], variable: "--font-sans" });
const fraunces = Fraunces({ subsets: ["latin"], variable: "--font-display" });

export const metadata: Metadata = {
  title: "Commerce — Merchant",
  description: "Accept orders, prepare, and mark ready for pickup",
  manifest: "/manifest.webmanifest",
};

export const viewport: Viewport = {
  themeColor: "#1a1408",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sora.variable} ${fraunces.variable}`}>
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}

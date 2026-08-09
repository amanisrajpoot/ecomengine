import { Sora, Fraunces } from "next/font/google";
import type { Metadata, Viewport } from "next";

import { AppShell } from "../components/AppShell";
import "./globals.css";

const sora = Sora({ subsets: ["latin"], variable: "--font-sans" });
const fraunces = Fraunces({ subsets: ["latin"], variable: "--font-display" });

export const metadata: Metadata = {
  title: "Commerce — Admin",
  description: "Platform operations and order debugger",
};

export const viewport: Viewport = {
  themeColor: "#120f18",
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

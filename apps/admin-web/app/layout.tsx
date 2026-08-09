import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Commerce Engine — Admin Web",
  description: "Commerce Engine Admin Web scaffold",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

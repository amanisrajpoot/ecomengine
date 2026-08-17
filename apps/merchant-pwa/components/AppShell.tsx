"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { session } from "@/lib/session";

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const businessId = session.getActiveBusinessId();

  const navItems = [
    { href: "/", label: "Home" },
    { href: "/businesses", label: "Stores" },
    ...(businessId
      ? [
          { href: `/business/${businessId}`, label: "Dashboard" },
          { href: `/business/${businessId}/orders`, label: "Orders" },
          { href: `/business/${businessId}/catalog`, label: "Catalog" },
        ]
      : []),
    { href: "/settings", label: "Settings" },
  ];

  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col">
      <header className="sticky top-0 z-10 border-b border-amber-800/40 bg-[#1a1410]/95 backdrop-blur">
        <div className="flex items-center justify-between px-4 py-3">
          <Link href="/" className="text-sm font-semibold tracking-wide text-amber-200">
            Merchant
          </Link>
          <nav className="flex flex-wrap gap-1">
            {navItems.map((item) => {
              const active =
                item.href === "/"
                  ? pathname === "/"
                  : pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors ${
                    active
                      ? "bg-amber-500/20 text-amber-100"
                      : "text-amber-300/70 hover:text-amber-100"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>
      <main className="flex-1 px-4 py-6">{children}</main>
    </div>
  );
}

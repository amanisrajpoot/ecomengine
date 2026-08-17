"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const navItems = [
  { href: "/", label: "Home" },
  { href: "/tenants", label: "Tenants" },
  { href: "/orders", label: "Orders" },
  { href: "/settlements", label: "Settlements" },
  { href: "/users/roles", label: "Roles" },
  { href: "/settings", label: "Settings" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="mx-auto flex min-h-screen max-w-4xl flex-col">
      <header className="sticky top-0 z-10 border-b border-violet-800/40 bg-[#12101a]/95 backdrop-blur">
        <div className="flex items-center justify-between px-4 py-3">
          <Link href="/" className="text-sm font-semibold tracking-wide text-violet-200">
            Admin
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
                      ? "bg-violet-500/20 text-violet-100"
                      : "text-violet-300/70 hover:text-violet-100"
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

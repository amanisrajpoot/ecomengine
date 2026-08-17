"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import { session } from "@/lib/session";

const HIDE_NAV = ["/login", "/register"];

const navItems = [
  { href: "/", label: "Home", icon: "🏠" },
  { href: "/jobs", label: "Jobs", icon: "🛵", match: (p: string) => p === "/jobs" || p.startsWith("/jobs/") },
  { href: "/onboarding", label: "Profile", icon: "👤" },
  { href: "/settings", label: "Settings", icon: "⚙️" },
];

function navActive(pathname: string, item: typeof navItems[number]): boolean {
  if (item.match) return item.match(pathname);
  if (item.href === "/") return pathname === "/";
  return pathname === item.href || pathname.startsWith(`${item.href}/`);
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [signedIn, setSignedIn] = useState(false);
  const showNav = !HIDE_NAV.some((p) => pathname.startsWith(p));

  useEffect(() => {
    setSignedIn(Boolean(session.getAccessToken()));
  }, [pathname]);

  return (
    <div className="mx-auto flex min-h-screen max-w-lg flex-col bg-[var(--bg)]">
      {showNav ? (
        <header className="sticky top-0 z-10 bg-[var(--brand)] text-white shadow-md">
          <div className="flex items-center justify-between px-4 py-3">
            <Link href="/" className="text-lg font-bold tracking-tight">
              Rider
            </Link>
            <div className="flex items-center gap-2 text-xs">
              {signedIn ? (
                <span className="rounded-full bg-white/15 px-3 py-1">On duty</span>
              ) : (
                <Link
                  href="/login"
                  className="rounded-full bg-white px-3 py-1 font-semibold text-[var(--brand)]"
                >
                  Sign in
                </Link>
              )}
            </div>
          </div>
        </header>
      ) : null}

      <main className={`flex-1 px-4 py-4 ${showNav ? "pb-nav" : ""}`}>{children}</main>

      {showNav ? (
        <nav
          className="fixed bottom-0 left-0 right-0 z-20 border-t border-gray-200 bg-white/95 backdrop-blur safe-pb"
          aria-label="Main"
        >
          <div className="mx-auto flex max-w-lg justify-around px-1 py-2">
            {navItems.map((item) => {
              const active = navActive(pathname, item);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex flex-col items-center gap-0.5 rounded-lg px-2 py-1.5 text-[10px] font-medium min-w-[3.5rem] ${
                    active ? "text-[var(--brand)]" : "text-gray-500"
                  }`}
                >
                  <span className="text-lg leading-none">{item.icon}</span>
                  {item.label}
                </Link>
              );
            })}
          </div>
        </nav>
      ) : null}
    </div>
  );
}

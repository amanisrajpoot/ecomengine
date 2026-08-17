"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import { session } from "@/lib/session";

import { CartPeek } from "./CartPeek";

const HIDE_NAV = ["/login", "/register"];

const navItems = [
  { href: "/", label: "Home", icon: "🏠" },
  { href: "/businesses", label: "Explore", icon: "🔍", match: (p: string) => p === "/businesses" || p.startsWith("/business/") },
  { href: "/orders", label: "Orders", icon: "📋" },
  { href: "/settings", label: "Account", icon: "👤" },
];

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
              Commerce
            </Link>
            <div className="flex items-center gap-2 text-xs">
              {signedIn ? (
                <Link href="/courier" className="rounded-full bg-white/15 px-3 py-1 hover:bg-white/25">
                  Courier
                </Link>
              ) : (
                <Link href="/login" className="rounded-full bg-white px-3 py-1 font-semibold text-[var(--brand)]">
                  Sign in
                </Link>
              )}
            </div>
          </div>
        </header>
      ) : null}

      <main className={`flex-1 px-4 py-4 ${showNav ? "pb-nav" : ""}`}>{children}</main>

      {showNav ? <CartPeek /> : null}

      {showNav ? (
        <nav
          className="fixed bottom-0 left-0 right-0 z-20 border-t border-gray-200 bg-white/95 backdrop-blur safe-pb"
          aria-label="Main"
        >
          <div className="mx-auto flex max-w-lg justify-around px-2 py-2">
            {navItems.map((item) => {
              const active = item.match
                ? item.match(pathname)
                : item.href === "/"
                  ? pathname === "/"
                  : pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex flex-col items-center gap-0.5 rounded-lg px-3 py-1.5 text-[10px] font-medium ${
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

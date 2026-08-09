"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { NavNotificationBadge, ToastProvider } from "@commerce/ui";

import { api, clearSession, getBusinessId, getToken } from "../lib/session";

const NOTIFICATIONS_SEEN_KEY = "ce.merchant.notifications.lastSeen";

const links = [
  { href: "/", label: "Home" },
  { href: "/orders", label: "Orders" },
  { href: "/catalog", label: "Catalog" },
  { href: "/inventory", label: "Inventory" },
  { href: "/ledger", label: "Ledger" },
  { href: "/settlements", label: "Settlements" },
  { href: "/settings", label: "Settings" },
  { href: "/notifications", label: "Alerts" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [authed, setAuthed] = useState(false);
  const [businessId, setBusinessId] = useState<string | null>(null);

  useEffect(() => {
    setAuthed(Boolean(getToken()));
    setBusinessId(getBusinessId());
  }, [pathname]);

  return (
    <ToastProvider>
      <div className="min-h-screen">
        <header className="sticky top-0 z-20 border-b border-amber-200/10 bg-[#1a1408]/85 backdrop-blur-md">
          <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-5 py-3">
            <Link href="/" className="font-display text-xl tracking-tight text-amber-50">
              Merchant
            </Link>
            <nav className="flex flex-wrap items-center gap-1 text-sm">
              {links.map((link) => {
                const active =
                  link.href === "/"
                    ? pathname === "/"
                    : pathname === link.href || pathname.startsWith(`${link.href}/`);
                const isAlerts = link.href === "/notifications";
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`relative rounded-lg px-2.5 py-1.5 transition ${
                      active
                        ? "bg-amber-400/15 text-amber-50"
                        : "text-amber-100/60 hover:text-amber-50"
                    }`}
                  >
                    {link.label}
                    {isAlerts && authed ? (
                      <NavNotificationBadge
                        enabled={authed}
                        storageKey={NOTIFICATIONS_SEEN_KEY}
                        loadNotifications={() => api().listNotifications({ limit: 100 })}
                        className="!bg-amber-400 !text-amber-950"
                      />
                    ) : null}
                  </Link>
                );
              })}
              {authed ? (
                <button
                  type="button"
                  className="ml-1 rounded-lg px-2.5 py-1.5 text-amber-100/60 hover:text-amber-50"
                  onClick={() => {
                    clearSession();
                    setAuthed(false);
                    router.push("/login");
                  }}
                >
                  Sign out
                </button>
              ) : (
                <Link
                  href="/login"
                  className="ml-1 rounded-lg bg-amber-500 px-2.5 py-1.5 font-medium text-amber-950"
                >
                  Sign in
                </Link>
              )}
            </nav>
          </div>
          {businessId ? (
            <p className="mx-auto max-w-5xl px-5 pb-2 text-xs text-amber-100/45">
              Business · {businessId.slice(0, 8)}…
            </p>
          ) : null}
        </header>
        {children}
      </div>
    </ToastProvider>
  );
}

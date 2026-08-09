"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { NavNotificationBadge, ToastProvider } from "@commerce/ui";

import { api, clearSession, getToken } from "../lib/session";

const NOTIFICATIONS_SEEN_KEY = "ce.rider.notifications.lastSeen";

const links = [
  { href: "/", label: "Home" },
  { href: "/deliveries", label: "Jobs" },
  { href: "/notifications", label: "Alerts" },
  { href: "/settlements", label: "Earnings" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    setAuthed(Boolean(getToken()));
  }, [pathname]);

  return (
    <ToastProvider>
      <div className="min-h-screen">
        <header className="sticky top-0 z-20 border-b border-sky-200/10 bg-[#0a1218]/85 backdrop-blur-md">
          <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-5 py-3">
            <Link href="/" className="font-display text-xl tracking-tight text-sky-50">
              Rider
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
                        ? "bg-sky-400/15 text-sky-50"
                        : "text-sky-100/60 hover:text-sky-50"
                    }`}
                  >
                    {link.label}
                    {isAlerts && authed ? (
                      <NavNotificationBadge
                        enabled={authed}
                        storageKey={NOTIFICATIONS_SEEN_KEY}
                        loadNotifications={() => api().listNotifications({ limit: 100 })}
                        className="!bg-sky-400 !text-sky-950"
                      />
                    ) : null}
                  </Link>
                );
              })}
              {authed ? (
                <button
                  type="button"
                  className="ml-1 rounded-lg px-2.5 py-1.5 text-sky-100/60 hover:text-sky-50"
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
                  className="ml-1 rounded-lg bg-sky-500 px-2.5 py-1.5 font-medium text-sky-950"
                >
                  Sign in
                </Link>
              )}
            </nav>
          </div>
        </header>
        {children}
      </div>
    </ToastProvider>
  );
}

"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { NavNotificationBadge, ToastProvider } from "@commerce/ui";

import { api, clearSession, getTenantId, getToken } from "../lib/session";

const NOTIFICATIONS_SEEN_KEY = "ce.admin.notifications.lastSeen";

const links = [
  { href: "/", label: "Home" },
  { href: "/dispatch", label: "Dispatch" },
  { href: "/ledger", label: "Ledger" },
  { href: "/settlements", label: "Settlements" },
  { href: "/notifications", label: "Notifications" },
  { href: "/ondc", label: "ONDC" },
  { href: "/tenants", label: "Tenants" },
  { href: "/orders", label: "Orders" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [authed, setAuthed] = useState(false);
  const [tenantId, setTenantId] = useState<string | null>(null);

  useEffect(() => {
    setAuthed(Boolean(getToken()));
    setTenantId(getTenantId());
  }, [pathname]);

  return (
    <ToastProvider>
      <div className="min-h-screen">
        <header className="sticky top-0 z-20 border-b border-violet-200/10 bg-[#120f18]/90 backdrop-blur-md">
          <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-3">
            <Link href="/" className="font-display text-xl tracking-tight text-violet-50">
              Admin
            </Link>
            <nav className="flex flex-wrap items-center gap-1 text-sm">
              {links.map((link) => {
                const active =
                  link.href === "/"
                    ? pathname === "/"
                    : pathname === link.href || pathname.startsWith(`${link.href}/`);
                const isNotifications = link.href === "/notifications";
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`relative rounded-lg px-2.5 py-1.5 transition ${
                      active
                        ? "bg-violet-400/15 text-violet-50"
                        : "text-violet-100/60 hover:text-violet-50"
                    }`}
                  >
                    {link.label}
                    {isNotifications && authed && tenantId ? (
                      <NavNotificationBadge
                        enabled={authed && Boolean(tenantId)}
                        storageKey={NOTIFICATIONS_SEEN_KEY}
                        loadNotifications={() => api().listNotifications({ limit: 100 })}
                        className="!bg-violet-400 !text-violet-50"
                      />
                    ) : null}
                  </Link>
                );
              })}
              {authed ? (
                <button
                  type="button"
                  className="ml-1 rounded-lg px-2.5 py-1.5 text-violet-100/60 hover:text-violet-50"
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
                  className="ml-1 rounded-lg bg-violet-500 px-2.5 py-1.5 font-medium text-violet-50"
                >
                  Sign in
                </Link>
              )}
            </nav>
          </div>
          {tenantId ? (
            <p className="mx-auto max-w-6xl px-5 pb-2 text-xs text-violet-100/45">
              Tenant context · {tenantId}
            </p>
          ) : null}
        </header>
        {children}
      </div>
    </ToastProvider>
  );
}

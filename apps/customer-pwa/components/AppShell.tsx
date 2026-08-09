"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { clearSession, getToken } from "../lib/session";

const links = [
  { href: "/", label: "Home" },
  { href: "/browse", label: "Browse" },
  { href: "/courier", label: "Courier" },
  { href: "/cart", label: "Cart" },
  { href: "/orders", label: "Orders" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    setAuthed(Boolean(getToken()));
  }, [pathname]);

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-emerald-200/10 bg-[#0f1c14]/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-5 py-3">
          <Link href="/" className="font-display text-xl tracking-tight text-emerald-50">
            Commerce
          </Link>
          <nav className="flex flex-wrap items-center gap-1 text-sm">
            {links.map((link) => {
              const active = pathname === link.href || pathname.startsWith(`${link.href}/`);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`rounded-lg px-2.5 py-1.5 transition ${
                    active
                      ? "bg-emerald-400/15 text-emerald-50"
                      : "text-emerald-100/60 hover:text-emerald-50"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
            {authed ? (
              <button
                type="button"
                className="ml-1 rounded-lg px-2.5 py-1.5 text-emerald-100/60 hover:text-emerald-50"
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
                className="ml-1 rounded-lg bg-emerald-500 px-2.5 py-1.5 font-medium text-emerald-950"
              >
                Sign in
              </Link>
            )}
          </nav>
        </div>
      </header>
      {children}
    </div>
  );
}

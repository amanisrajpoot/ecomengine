"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { api, clearSession, getSessionCart, getToken } from "../lib/session";

const links = [
  { href: "/", label: "Home" },
  { href: "/browse", label: "Browse" },
  { href: "/courier", label: "Courier" },
  { href: "/cart", label: "Cart" },
  { href: "/orders", label: "Orders" },
  { href: "/notifications", label: "Alerts" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [authed, setAuthed] = useState(false);
  const [cartCount, setCartCount] = useState(0);

  useEffect(() => {
    setAuthed(Boolean(getToken()));
    const session = getSessionCart();
    if (!session?.cartId || !getToken()) {
      setCartCount(session?.itemCount ?? 0);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const cart = await api().getCart(session.cartId);
        if (cancelled) return;
        const count = cart.items.reduce((sum, item) => sum + item.quantity, 0);
        setCartCount(count);
      } catch {
        if (!cancelled) setCartCount(session.itemCount ?? 0);
      }
    })();
    return () => {
      cancelled = true;
    };
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
              const active =
                link.href === "/"
                  ? pathname === "/"
                  : pathname === link.href || pathname.startsWith(`${link.href}/`);
              const isCart = link.href === "/cart";
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`relative rounded-lg px-2.5 py-1.5 transition ${
                    active
                      ? "bg-emerald-400/15 text-emerald-50"
                      : "text-emerald-100/60 hover:text-emerald-50"
                  }`}
                >
                  {link.label}
                  {isCart && cartCount > 0 ? (
                    <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-emerald-400 px-1 text-[10px] font-bold text-emerald-950">
                      {cartCount > 9 ? "9+" : cartCount}
                    </span>
                  ) : null}
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
                  setCartCount(0);
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

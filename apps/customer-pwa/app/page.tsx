import Link from "next/link";

import { Button } from "@commerce/ui";

export default function HomePage() {
  return (
    <div className="space-y-8 py-4">
      <div className="space-y-3">
        <p className="text-sm uppercase tracking-[0.2em] text-emerald-300/80">Commerce Engine</p>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">Customer</h1>
        <p className="max-w-xl text-lg text-emerald-50/75">
          Browse stores, build a cart, pay with COD, and track orders — wired to the live API via{" "}
          <code className="text-emerald-200">@commerce/api-client</code>.
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <Link href="/businesses">
          <Button>Browse businesses</Button>
        </Link>
        <Link href="/login">
          <Button variant="secondary">Sign in</Button>
        </Link>
        <Link href="/settings">
          <Button variant="ghost">Settings</Button>
        </Link>
      </div>

      <div className="rounded-xl border border-emerald-800/30 bg-emerald-950/30 p-4 text-sm text-emerald-200/80">
        <p className="font-medium text-emerald-100">First-time setup</p>
        <ol className="mt-2 list-inside list-decimal space-y-1">
          <li>Set your tenant ID in Settings (from admin or integration tests).</li>
          <li>Register or sign in as a customer.</li>
          <li>Open a business catalog and add items to your cart.</li>
        </ol>
      </div>
    </div>
  );
}

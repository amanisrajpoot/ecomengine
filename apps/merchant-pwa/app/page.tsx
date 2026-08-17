import Link from "next/link";

import { Button } from "@commerce/ui";

export default function HomePage() {
  return (
    <div className="space-y-8 py-4">
      <div className="space-y-3">
        <p className="text-sm uppercase tracking-[0.2em] text-amber-300/80">Commerce Engine</p>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">Merchant</h1>
        <p className="max-w-xl text-lg text-amber-50/75">
          Manage stores, fulfill orders, and update catalog — wired to{" "}
          <code className="text-amber-200">@commerce/api-client</code>.
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <Link href="/businesses">
          <Button>My stores</Button>
        </Link>
        <Link href="/login">
          <Button variant="secondary">Sign in</Button>
        </Link>
        <Link href="/settings">
          <Button variant="ghost">Settings</Button>
        </Link>
      </div>

      <div className="rounded-xl border border-amber-800/30 bg-amber-950/30 p-4 text-sm text-amber-200/80">
        <p className="font-medium text-amber-100">Merchant workflow</p>
        <ol className="mt-2 list-inside list-decimal space-y-1">
          <li>Set tenant ID and sign in (or register).</li>
          <li>Create a store or open an existing one.</li>
          <li>Accept and progress orders; add products and variants.</li>
        </ol>
      </div>
    </div>
  );
}

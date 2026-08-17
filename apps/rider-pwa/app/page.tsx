import Link from "next/link";

import { Button } from "@commerce/ui";

export default function HomePage() {
  return (
    <div className="space-y-8 py-4">
      <div className="space-y-3">
        <p className="text-sm uppercase tracking-[0.2em] text-sky-300/80">Commerce Engine</p>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">Rider</h1>
        <p className="max-w-xl text-lg text-sky-50/75">
          Accept assigned deliveries, complete stops with POD, and advance order status — via{" "}
          <code className="text-sky-200">@commerce/api-client</code>.
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <Link href="/jobs">
          <Button>Active jobs</Button>
        </Link>
        <Link href="/onboarding">
          <Button variant="secondary">Partner profile</Button>
        </Link>
        <Link href="/login">
          <Button variant="ghost">Sign in</Button>
        </Link>
      </div>

      <div className="rounded-xl border border-sky-800/30 bg-sky-950/30 p-4 text-sm text-sky-200/80">
        <p className="font-medium text-sky-100">Setup</p>
        <ol className="mt-2 list-inside list-decimal space-y-1">
          <li>Admin assigns <code>DELIVERY_PARTNER</code> role to your user.</li>
          <li>Create partner profile, register vehicle, go online.</li>
          <li>When assigned a delivery, open Jobs to complete stops.</li>
        </ol>
      </div>
    </div>
  );
}

import Link from "next/link";

import { Button } from "@commerce/ui";

export default function HomePage() {
  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-white p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-widest text-blue-600">Commerce Engine</p>
        <h1 className="mt-2 text-2xl font-bold text-gray-900">Delivery partner</h1>
        <p className="mt-2 text-sm text-gray-500">
          Accept assigned jobs, complete stops with proof of delivery, and advance order status on the go.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link href="/jobs">
            <Button variant="brand" className="bg-[var(--brand)] hover:bg-[var(--brand-dark)]">
              Active jobs
            </Button>
          </Link>
          <Link href="/onboarding">
            <Button
              variant="secondary"
              className="border-gray-300 bg-gray-100 text-gray-800 hover:bg-gray-200"
            >
              Partner profile
            </Button>
          </Link>
        </div>
      </div>

      <div className="rounded-2xl border border-dashed border-gray-200 bg-white p-5 text-sm text-gray-600">
        <p className="font-semibold text-gray-900">Getting started</p>
        <ol className="mt-3 list-inside list-decimal space-y-2">
          <li>Admin assigns <code className="text-xs">DELIVERY_PARTNER</code> role to your account.</li>
          <li>Create partner profile, register a vehicle, and go online.</li>
          <li>When assigned a delivery, open Jobs to complete each stop.</li>
        </ol>
      </div>
    </div>
  );
}

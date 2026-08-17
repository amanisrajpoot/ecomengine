import Link from "next/link";

import { Button } from "@commerce/ui";

export default function HomePage() {
  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-white p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-widest text-orange-600">Commerce Engine</p>
        <h1 className="mt-2 text-2xl font-bold text-gray-900">Partner hub</h1>
        <p className="mt-2 text-sm text-gray-500">
          Accept orders, run your kitchen display, and manage menu items — wired to your tenant API.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link href="/businesses">
            <Button variant="brand">My stores</Button>
          </Link>
          <Link href="/login">
            <Button variant="secondary" className="border-gray-300 bg-gray-100 text-gray-800 hover:bg-gray-200">
              Sign in
            </Button>
          </Link>
        </div>
      </div>

      <div className="rounded-2xl border border-dashed border-gray-200 bg-white p-5 text-sm text-gray-600">
        <p className="font-semibold text-gray-900">Quick start</p>
        <ol className="mt-3 list-inside list-decimal space-y-2">
          <li>Set tenant ID in Settings and sign in.</li>
          <li>Open a store or create a new one.</li>
          <li>Use the Orders tab to accept and progress live orders.</li>
        </ol>
      </div>
    </div>
  );
}

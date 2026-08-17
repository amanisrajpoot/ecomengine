import Link from "next/link";

import { Button } from "@commerce/ui";

export default function HomePage() {
  return (
    <div className="space-y-8 py-4">
      <div className="space-y-3">
        <p className="text-sm uppercase tracking-[0.2em] text-violet-300/80">Commerce Engine</p>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">Admin</h1>
        <p className="max-w-xl text-lg text-violet-50/75">
          Tenant ops, order debugger, settlements, and role management — wired to the live API.
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <Link href="/orders">
          <Button>Order debugger</Button>
        </Link>
        <Link href="/tenants">
          <Button variant="secondary">Tenants</Button>
        </Link>
        <Link href="/login">
          <Button variant="ghost">Sign in</Button>
        </Link>
      </div>

      <div className="rounded-xl border border-violet-800/30 bg-violet-950/30 p-4 text-sm text-violet-200/80">
        <p className="font-medium text-violet-100">Bootstrap admin</p>
        <p className="mt-2">
          Default super admin: <code>admin@example.com</code> / <code>ChangeMe123!</code> (no tenant
          header). Set tenant in Settings for tenant-scoped order views.
        </p>
      </div>
    </div>
  );
}

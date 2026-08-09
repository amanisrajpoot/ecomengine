"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { getToken } from "../../lib/session";

export default function SettingsPage() {
  const router = useRouter();

  useEffect(() => {
    if (!getToken()) router.replace("/login");
  }, [router]);

  if (!getToken()) return null;

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <p className="font-display text-4xl text-amber-50">Settings</p>
      <p className="mt-2 text-sm text-amber-100/55">
        Business profile, locations, and operating hours.
      </p>

      <ul className="mt-8 flex flex-col gap-3">
        <li>
          <Link
            href="/settings/business"
            className="block rounded-2xl border border-amber-200/10 bg-amber-950/25 px-4 py-4 transition hover:border-amber-300/25"
          >
            <p className="font-medium text-amber-50">Business profile</p>
            <p className="mt-1 text-sm text-amber-100/50">
              Name, contact, prep time, pause/resume store
            </p>
          </Link>
        </li>
        <li>
          <Link
            href="/settings/locations"
            className="block rounded-2xl border border-amber-200/10 bg-amber-950/25 px-4 py-4 transition hover:border-amber-300/25"
          >
            <p className="font-medium text-amber-50">Locations</p>
            <p className="mt-1 text-sm text-amber-100/50">
              Addresses, geo coordinates, weekly hours
            </p>
          </Link>
        </li>
      </ul>
    </main>
  );
}

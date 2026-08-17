"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";

export function ClientAppShell({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div className="mx-auto max-w-3xl px-4 py-6">{children}</div>;
  }

  return <AppShell>{children}</AppShell>;
}

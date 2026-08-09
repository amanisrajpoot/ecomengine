"use client";

import { useState } from "react";

function JsonBlock({
  title,
  data,
  defaultOpen = false,
}: {
  title: string;
  data: unknown;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const empty = data == null || (Array.isArray(data) && data.length === 0);
  const count = Array.isArray(data) ? data.length : data ? 1 : 0;

  return (
    <section className="rounded-2xl border border-violet-200/10 bg-violet-950/20">
      <button
        type="button"
        className="flex w-full items-center justify-between px-4 py-3 text-left"
        onClick={() => setOpen((v) => !v)}
      >
        <h2 className="text-sm font-medium uppercase tracking-wide text-violet-200/50">
          {title}
          {!empty ? (
            <span className="ml-2 normal-case text-violet-100/40">({count})</span>
          ) : null}
        </h2>
        <span className="text-violet-200/50">{open ? "−" : "+"}</span>
      </button>
      {open ? (
        <div className="border-t border-violet-200/10 px-4 pb-4">
          {empty ? (
            <p className="mt-2 text-sm text-violet-100/40">—</p>
          ) : (
            <pre className="mt-3 max-h-80 overflow-auto text-xs leading-relaxed text-violet-100/75">
              {JSON.stringify(data, null, 2)}
            </pre>
          )}
        </div>
      ) : null}
    </section>
  );
}

export { JsonBlock };

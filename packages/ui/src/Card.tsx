import type { ReactNode } from "react";

export type CardProps = {
  title?: string;
  children: ReactNode;
  className?: string;
};

export function Card({ title, children, className = "" }: CardProps) {
  return (
    <section
      className={`rounded-xl border border-emerald-700/30 bg-emerald-950/40 p-4 shadow-lg shadow-black/20 ${className}`}
    >
      {title ? (
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-emerald-300/80">
          {title}
        </h2>
      ) : null}
      {children}
    </section>
  );
}

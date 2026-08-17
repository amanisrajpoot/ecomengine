import type { ReactNode } from "react";

export type CardVariant = "default" | "light";

export type CardProps = {
  title?: string;
  children: ReactNode;
  variant?: CardVariant;
  className?: string;
};

const variantClass: Record<CardVariant, string> = {
  default: "border-emerald-700/30 bg-emerald-950/40 shadow-lg shadow-black/20",
  light: "border-gray-200 bg-white shadow-sm",
};

const titleClass: Record<CardVariant, string> = {
  default: "text-emerald-300/80",
  light: "text-gray-500",
};

export function Card({ title, children, variant = "default", className = "" }: CardProps) {
  return (
    <section className={`rounded-xl border p-4 ${variantClass[variant]} ${className}`}>
      {title ? (
        <h2 className={`mb-3 text-sm font-semibold uppercase tracking-wide ${titleClass[variant]}`}>
          {title}
        </h2>
      ) : null}
      {children}
    </section>
  );
}

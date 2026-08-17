import type { ReactNode } from "react";

export type BadgeProps = {
  children: ReactNode;
  variant?: "default" | "accent" | "muted";
  className?: string;
};

const variants = {
  default: "bg-gray-100 text-gray-700",
  accent: "bg-orange-100 text-orange-700",
  muted: "bg-gray-50 text-gray-500",
};

export function Badge({ children, variant = "default", className = "" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${variants[variant]} ${className}`}
    >
      {children}
    </span>
  );
}

import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost" | "soft";
  children: ReactNode;
};

export function Button({
  variant = "primary",
  className = "",
  children,
  ...props
}: ButtonProps) {
  const styles =
    variant === "primary"
      ? "bg-emerald-500 text-emerald-950 hover:bg-emerald-400"
      : variant === "soft"
        ? "bg-emerald-400/15 text-emerald-50 hover:bg-emerald-400/25"
        : "bg-transparent text-emerald-50/90 hover:bg-white/5";
  return (
    <button
      className={`inline-flex items-center justify-center rounded-xl px-4 py-2.5 text-sm font-medium transition duration-200 disabled:opacity-50 ${styles} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

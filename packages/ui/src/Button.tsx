import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "brand";

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  children: ReactNode;
};

const variantClass: Record<ButtonVariant, string> = {
  primary:
    "bg-emerald-500 text-emerald-950 hover:bg-emerald-400 disabled:bg-emerald-800/40 disabled:text-emerald-100/50",
  secondary:
    "bg-emerald-900/60 text-emerald-50 hover:bg-emerald-800/80 border border-emerald-600/40",
  ghost: "bg-transparent text-emerald-100 hover:bg-emerald-900/40",
  brand:
    "bg-orange-500 text-white hover:bg-orange-600 disabled:bg-orange-200 disabled:text-orange-50",
};

export function Button({
  variant = "primary",
  className = "",
  children,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={`inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed ${variantClass[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

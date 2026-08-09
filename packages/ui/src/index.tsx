import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";

export function formatPaise(paise: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(paise / 100);
}

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

type FieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
};

export function TextField({ label, className = "", id, ...props }: FieldProps) {
  const fieldId = id ?? props.name ?? label.toLowerCase().replace(/\s+/g, "-");
  return (
    <label className="flex flex-col gap-1.5 text-sm text-emerald-50/80">
      <span>{label}</span>
      <input
        id={fieldId}
        className={`rounded-xl border border-emerald-200/15 bg-emerald-950/40 px-3 py-2.5 text-emerald-50 outline-none ring-emerald-400/40 placeholder:text-emerald-100/35 focus:ring-2 ${className}`}
        {...props}
      />
    </label>
  );
}

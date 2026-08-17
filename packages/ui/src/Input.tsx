import type { InputHTMLAttributes } from "react";

export type InputVariant = "default" | "light";

export type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  variant?: InputVariant;
};

const labelClass: Record<InputVariant, string> = {
  default: "text-emerald-200/80",
  light: "text-gray-600",
};

const inputClass: Record<InputVariant, string> = {
  default:
    "border-emerald-700/40 bg-emerald-950/60 text-emerald-50 placeholder:text-emerald-400/40 focus:border-emerald-500 focus:ring-emerald-500/50",
  light:
    "border-gray-300 bg-white text-gray-900 placeholder:text-gray-400 focus:border-orange-500 focus:ring-orange-500/40",
};

export function Input({ label, variant = "default", className = "", id, ...props }: InputProps) {
  const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
  return (
    <label className="flex flex-col gap-1.5 text-sm">
      {label ? <span className={labelClass[variant]}>{label}</span> : null}
      <input
        id={inputId}
        className={`rounded-lg border px-3 py-2 focus:outline-none focus:ring-1 ${inputClass[variant]} ${className}`}
        {...props}
      />
    </label>
  );
}

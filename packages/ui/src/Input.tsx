import type { InputHTMLAttributes } from "react";

export type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
};

export function Input({ label, className = "", id, ...props }: InputProps) {
  const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
  return (
    <label className="flex flex-col gap-1.5 text-sm">
      {label ? <span className="text-emerald-200/80">{label}</span> : null}
      <input
        id={inputId}
        className={`rounded-lg border border-emerald-700/40 bg-emerald-950/60 px-3 py-2 text-emerald-50 placeholder:text-emerald-400/40 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500/50 ${className}`}
        {...props}
      />
    </label>
  );
}

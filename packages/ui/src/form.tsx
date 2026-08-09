import type { InputHTMLAttributes } from "react";

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

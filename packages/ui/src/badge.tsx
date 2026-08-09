import type { HTMLAttributes } from "react";

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  count: number;
  max?: number;
  className?: string;
};

export function Badge({ count, max = 9, className = "", ...props }: BadgeProps) {
  if (count <= 0) return null;
  const label = count > max ? `${max}+` : String(count);
  return (
    <span
      className={`absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-emerald-400 px-1 text-[10px] font-bold text-emerald-950 ${className}`}
      {...props}
    >
      {label}
    </span>
  );
}

import type { HTMLAttributes } from "react";

type SpinnerProps = HTMLAttributes<HTMLDivElement> & {
  size?: "sm" | "md" | "lg";
  label?: string;
};

const sizes = {
  sm: "h-4 w-4 border-2",
  md: "h-6 w-6 border-2",
  lg: "h-8 w-8 border-[3px]",
};

export function Spinner({ size = "md", label = "Loading", className = "", ...props }: SpinnerProps) {
  return (
    <div
      role="status"
      aria-label={label}
      className={`inline-flex items-center justify-center ${className}`}
      {...props}
    >
      <span
        className={`animate-spin rounded-full border-current border-t-transparent opacity-80 ${sizes[size]}`}
      />
    </div>
  );
}

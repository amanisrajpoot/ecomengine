type LiveIndicatorProps = {
  label?: string;
  className?: string;
};

export function LiveIndicator({ label = "Live", className = "" }: LiveIndicatorProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 text-xs text-white/50 ${className}`}
      title="Auto-refreshing"
    >
      <span className="relative flex h-2 w-2">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400/60 opacity-75" />
        <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
      </span>
      {label}
    </span>
  );
}

export type StatTileProps = {
  label: string;
  value: string | number;
  hint?: string;
  accent?: boolean;
  className?: string;
};

export function StatTile({ label, value, hint, accent = false, className = "" }: StatTileProps) {
  return (
    <div
      className={`rounded-2xl border p-4 shadow-sm ${
        accent
          ? "border-orange-200 bg-orange-50"
          : "border-gray-200 bg-white"
      } ${className}`}
    >
      <p className="text-xs font-medium uppercase tracking-wide text-gray-500">{label}</p>
      <p
        className={`mt-1 text-2xl font-bold tabular-nums ${
          accent ? "text-orange-600" : "text-gray-900"
        }`}
      >
        {value}
      </p>
      {hint ? <p className="mt-1 text-xs text-gray-500">{hint}</p> : null}
    </div>
  );
}

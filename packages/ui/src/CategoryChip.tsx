export type CategoryChipProps = {
  label: string;
  active?: boolean;
  onClick?: () => void;
};

export function CategoryChip({ label, active = false, onClick }: CategoryChipProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`shrink-0 rounded-full px-4 py-2 text-sm font-medium transition ${
        active
          ? "bg-orange-500 text-white shadow-sm"
          : "bg-white text-gray-700 border border-gray-200 hover:border-orange-200"
      }`}
    >
      {label}
    </button>
  );
}

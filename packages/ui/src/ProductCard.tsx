import { PriceDisplay } from "./PriceDisplay";

export type ProductCardProps = {
  name: string;
  description?: string | null;
  pricePaise: number;
  onAdd?: () => void;
  adding?: boolean;
  imageEmoji?: string;
};

export function ProductCard({
  name,
  description,
  pricePaise,
  onAdd,
  adding = false,
  imageEmoji = "🍱",
}: ProductCardProps) {
  return (
    <article className="flex gap-3 rounded-2xl border border-gray-100 bg-white p-3 shadow-sm">
      <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-xl bg-orange-50 text-2xl">
        {imageEmoji}
      </div>
      <div className="flex min-w-0 flex-1 flex-col justify-between">
        <div>
          <h4 className="font-medium text-gray-900 leading-snug">{name}</h4>
          {description ? (
            <p className="mt-0.5 line-clamp-2 text-xs text-gray-500">{description}</p>
          ) : null}
        </div>
        <div className="mt-2 flex items-center justify-between gap-2">
          <PriceDisplay paise={pricePaise} className="text-orange-600" />
          {onAdd ? (
            <button
              type="button"
              onClick={onAdd}
              disabled={adding}
              className="rounded-lg bg-orange-500 px-3 py-1.5 text-xs font-semibold text-white shadow-sm transition hover:bg-orange-600 disabled:opacity-50"
            >
              {adding ? "…" : "ADD"}
            </button>
          ) : null}
        </div>
      </div>
    </article>
  );
}

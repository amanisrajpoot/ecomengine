import Link from "next/link";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-3xl px-5 py-16">
      <p className="animate-rise font-display text-5xl text-amber-50 sm:text-6xl">Merchant</p>
      <h1 className="animate-rise-delay mt-4 text-2xl font-medium text-amber-50/90">
        Kitchen & store operations on the shared order engine.
      </h1>
      <p className="mt-4 max-w-lg text-amber-100/60">
        Accept incoming orders, move food through prepare → ready, or grocery through pick → ready.
        Rider assignment stays in the rider app.
      </p>
      <div className="animate-rise-delay mt-8 flex flex-wrap gap-3">
        <Link
          href="/orders"
          className="rounded-xl bg-amber-500 px-5 py-3 text-sm font-semibold text-amber-950 hover:bg-amber-400"
        >
          Open order queue
        </Link>
        <Link
          href="/catalog"
          className="rounded-xl border border-amber-200/20 px-5 py-3 text-sm font-medium text-amber-50/90 hover:bg-white/5"
        >
          Manage catalog
        </Link>
        <Link
          href="/inventory"
          className="rounded-xl border border-amber-200/20 px-5 py-3 text-sm font-medium text-amber-50/90 hover:bg-white/5"
        >
          Stock board
        </Link>
        <Link
          href="/settlements"
          className="rounded-xl border border-amber-200/20 px-5 py-3 text-sm font-medium text-amber-50/90 hover:bg-white/5"
        >
          Settlements
        </Link>
        <Link
          href="/login"
          className="rounded-xl border border-amber-200/20 px-5 py-3 text-sm font-medium text-amber-50/90 hover:bg-white/5"
        >
          Sign in
        </Link>
      </div>
    </main>
  );
}

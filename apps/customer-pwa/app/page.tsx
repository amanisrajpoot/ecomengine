import Link from "next/link";

const lanes = [
  {
    href: "/browse?type=FOOD",
    title: "Food",
    copy: "Nearby kitchens, menus, and delivery.",
  },
  {
    href: "/browse?type=GROCERY",
    title: "Grocery",
    copy: "Hyperlocal stores with live stock.",
  },
  {
    href: "/courier",
    title: "Courier",
    copy: "Quote a package and book a rider.",
  },
];

export default function HomePage() {
  return (
    <main className="relative overflow-hidden">
      <div
        aria-hidden
        className="hero-orb pointer-events-none absolute -right-16 top-10 h-72 w-72 rounded-full bg-emerald-400/15 blur-3xl"
      />
      <section className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-5xl flex-col justify-center gap-10 px-5 py-16">
        <div className="max-w-2xl">
          <p className="animate-rise font-display text-5xl leading-none tracking-tight text-emerald-50 sm:text-7xl">
            Commerce
          </p>
          <h1 className="animate-rise-delay mt-5 max-w-xl text-2xl font-medium leading-snug text-emerald-50/95 sm:text-3xl">
            Food, grocery, and courier — one checkout.
          </h1>
          <p className="animate-rise-late mt-4 max-w-md text-base text-emerald-100/65">
            Discover nearby businesses, pay in paise-accurate totals, and track the same order
            engine merchants and riders use.
          </p>
          <div className="animate-rise-late mt-8 flex flex-wrap gap-3">
            <Link
              href="/browse"
              className="rounded-xl bg-emerald-500 px-5 py-3 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-400"
            >
              Browse nearby
            </Link>
            <Link
              href="/login"
              className="rounded-xl border border-emerald-200/20 px-5 py-3 text-sm font-medium text-emerald-50/90 transition hover:bg-white/5"
            >
              Sign in
            </Link>
          </div>
        </div>

        <ul className="animate-rise-late grid gap-4 sm:grid-cols-3">
          {lanes.map((lane) => (
            <li key={lane.href}>
              <Link
                href={lane.href}
                className="block rounded-2xl border border-emerald-200/10 bg-emerald-950/30 p-5 transition hover:border-emerald-300/25 hover:bg-emerald-900/40"
              >
                <p className="font-display text-2xl text-emerald-50">{lane.title}</p>
                <p className="mt-2 text-sm text-emerald-100/60">{lane.copy}</p>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}

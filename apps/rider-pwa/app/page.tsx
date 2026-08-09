import Link from "next/link";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-3xl px-5 py-16">
      <p className="animate-rise font-display text-5xl text-sky-50 sm:text-6xl">Rider</p>
      <h1 className="animate-rise-delay mt-4 text-2xl font-medium text-sky-50/90">
        Go online, run assigned jobs, capture POD.
      </h1>
      <p className="mt-4 max-w-lg text-sky-100/60">
        Shared delivery engine — pickup and drop stops, OTP or photo proof, live location
        pings, and order sync on completion.
      </p>
      <div className="animate-rise-delay mt-8 flex flex-wrap gap-3">
        <Link
          href="/deliveries"
          className="rounded-xl bg-sky-500 px-5 py-3 text-sm font-semibold text-sky-950 hover:bg-sky-400"
        >
          View jobs
        </Link>
        <Link
          href="/login"
          className="rounded-xl border border-sky-200/20 px-5 py-3 text-sm font-medium text-sky-50/90 hover:bg-white/5"
        >
          Sign in
        </Link>
      </div>
    </main>
  );
}

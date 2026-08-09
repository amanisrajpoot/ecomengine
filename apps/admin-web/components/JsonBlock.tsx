function JsonBlock({ title, data }: { title: string; data: unknown }) {
  if (data == null || (Array.isArray(data) && data.length === 0)) {
    return (
      <section className="rounded-2xl border border-violet-200/10 bg-violet-950/20 p-4">
        <h2 className="text-sm font-medium uppercase tracking-wide text-violet-200/50">
          {title}
        </h2>
        <p className="mt-2 text-sm text-violet-100/40">—</p>
      </section>
    );
  }
  return (
    <section className="rounded-2xl border border-violet-200/10 bg-violet-950/20 p-4">
      <h2 className="text-sm font-medium uppercase tracking-wide text-violet-200/50">
        {title}
      </h2>
      <pre className="mt-3 max-h-80 overflow-auto text-xs leading-relaxed text-violet-100/75">
        {JSON.stringify(data, null, 2)}
      </pre>
    </section>
  );
}

export { JsonBlock };

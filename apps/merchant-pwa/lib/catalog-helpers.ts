export function businessHasCatalog(capabilities: Record<string, unknown> | undefined): boolean {
  return Boolean(capabilities?.catalog);
}

export function rupeesToPaise(value: string): number {
  const parsed = Number.parseFloat(value.replace(/,/g, "").trim());
  if (!Number.isFinite(parsed) || parsed < 0) return 0;
  return Math.round(parsed * 100);
}

export function paiseToRupeesInput(paise: number): string {
  return (paise / 100).toFixed(2);
}

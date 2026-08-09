export function defaultSettlementPeriod(): { period_start: string; period_end: string } {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - 7);
  return {
    period_start: start.toISOString(),
    period_end: end.toISOString(),
  };
}

export function settlementStatusLabel(status: string): string {
  return status.replace(/_/g, " ");
}

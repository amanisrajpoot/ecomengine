/** Format integer paise as INR display string. */
export function formatPaise(paise: number, currency = "INR"): string {
  const amount = paise / 100;
  if (currency === "INR") {
    return `₹${amount.toFixed(2)}`;
  }
  return `${amount.toFixed(2)} ${currency}`;
}

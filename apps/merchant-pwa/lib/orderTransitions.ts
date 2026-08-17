/** Merchant-actor order transitions (subset of state machine profiles). */

const MERCHANT_TARGETS = new Set([
  "ACCEPTED",
  "PREPARING",
  "PICKING",
  "READY",
  "CANCELLED",
]);

const PROFILE_TRANSITIONS: Record<string, Record<string, string[]>> = {
  FOOD_DELIVERY: {
    PAYMENT_CONFIRMED: ["ACCEPTED", "CANCELLED"],
    ACCEPTED: ["PREPARING", "CANCELLED"],
    PREPARING: ["READY", "CANCELLED"],
  },
  HYPERLOCAL_DELIVERY: {
    PAYMENT_CONFIRMED: ["ACCEPTED", "CANCELLED"],
    ACCEPTED: ["PICKING", "CANCELLED"],
    PICKING: ["READY", "CANCELLED"],
  },
  COURIER: {
    PAYMENT_CONFIRMED: ["CANCELLED"],
  },
  PICKUP_ONLY: {
    PAYMENT_CONFIRMED: ["READY", "CANCELLED"],
    READY: ["DELIVERED", "CANCELLED"],
  },
};

export function merchantTransitionsFor(
  profile: string,
  currentStatus: string,
): string[] {
  const profileMap = PROFILE_TRANSITIONS[profile] ?? PROFILE_TRANSITIONS.FOOD_DELIVERY;
  const candidates = profileMap[currentStatus] ?? [];
  return candidates.filter((status) => MERCHANT_TARGETS.has(status) || status === "DELIVERED");
}

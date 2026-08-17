import type { Order } from "@commerce/types";

import { merchantTransitionsFor } from "./orderTransitions";

export function orderNeedsMerchantAction(profile: string, status: string): boolean {
  return merchantTransitionsFor(profile, status).length > 0;
}

export function primaryMerchantAction(profile: string, status: string): string | null {
  const next = merchantTransitionsFor(profile, status);
  return next.find((s) => s !== "CANCELLED") ?? null;
}

export function formatOrderStatus(status: string): string {
  return status.replace(/_/g, " ");
}

export function orderTotalPaise(order: Order): number | null {
  const total = order.pricing_snapshot?.total_paise;
  return typeof total === "number" ? total : null;
}

export function formatOrderTime(value: string | null | undefined): string {
  if (!value) return "";
  try {
    return new Date(value).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return value;
  }
}

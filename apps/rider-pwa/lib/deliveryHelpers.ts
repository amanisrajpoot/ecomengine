import type { Delivery, DeliveryStop } from "@commerce/types";

import { riderTransitionsFor } from "./orderTransitions";

export function formatAddress(address: Record<string, unknown>): string {
  const parts = [address.line1, address.city, address.pincode].filter(Boolean);
  return parts.join(", ") || "Address not set";
}

export function formatTime(value: string | null | undefined): string {
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

export function stopsCompletedCount(delivery: Delivery): number {
  return (delivery.stops ?? []).filter((s) => s.status === "COMPLETED").length;
}

export function stopsTotalCount(delivery: Delivery): number {
  return delivery.stops?.length ?? 0;
}

export function deliveryNeedsAction(delivery: Delivery): boolean {
  return (delivery.stops ?? []).some((s) => s.status !== "COMPLETED");
}

export function nextPendingStop(delivery: Delivery): DeliveryStop | null {
  const stops = [...(delivery.stops ?? [])].sort((a, b) => a.sequence - b.sequence);
  return stops.find((s) => s.status !== "COMPLETED") ?? null;
}

export function orderNeedsRiderAction(profile: string, status: string): boolean {
  return riderTransitionsFor(profile, status).length > 0;
}

export function primaryRiderAction(profile: string, status: string): string | null {
  return riderTransitionsFor(profile, status)[0] ?? null;
}

export function defaultProof(stop: DeliveryStop): Record<string, unknown> {
  if (stop.stop_type === "PICKUP") {
    return { type: "OTP", code: "1234" };
  }
  return { type: "PHOTO", url: "s3://pod/rider-pwa.jpg" };
}

export function stopIcon(stopType: string): string {
  if (stopType === "PICKUP") return "📦";
  if (stopType === "DROP") return "🏠";
  return "📍";
}

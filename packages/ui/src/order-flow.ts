/** Customer-visible order progress steps keyed by state machine profile. */

export const ORDER_FLOW_STEPS: Record<string, readonly string[]> = {
  FOOD_DELIVERY: [
    "PAYMENT_CONFIRMED",
    "ACCEPTED",
    "PREPARING",
    "READY",
    "PICKED_UP",
    "OUT_FOR_DELIVERY",
    "DELIVERED",
  ],
  HYPERLOCAL_DELIVERY: [
    "PAYMENT_CONFIRMED",
    "ACCEPTED",
    "PICKING",
    "READY",
    "PICKED_UP",
    "OUT_FOR_DELIVERY",
    "DELIVERED",
  ],
  COURIER: ["PAYMENT_CONFIRMED", "PICKUP_ASSIGNED", "PICKED_UP", "IN_TRANSIT", "DELIVERED"],
};

export const STATUS_LABELS: Record<string, string> = {
  CREATED: "Created",
  PAYMENT_PENDING: "Payment pending",
  PAYMENT_CONFIRMED: "Confirmed",
  ACCEPTED: "Accepted",
  PREPARING: "Preparing",
  PICKING: "Picking",
  READY: "Ready",
  PICKUP_ASSIGNED: "Rider assigned",
  PICKED_UP: "Picked up",
  OUT_FOR_DELIVERY: "On the way",
  IN_TRANSIT: "In transit",
  DELIVERED: "Delivered",
  CANCELLED: "Cancelled",
  FAILED: "Failed",
  REFUNDED: "Refunded",
};

export function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status.replaceAll("_", " ").toLowerCase();
}

export function flowStepsFor(profile: string): readonly string[] {
  return ORDER_FLOW_STEPS[profile] ?? ORDER_FLOW_STEPS.FOOD_DELIVERY;
}

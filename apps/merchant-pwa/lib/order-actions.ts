import type { Order } from "@commerce/types";

export type MerchantAction = {
  label: string;
  to_status: string;
  actor: string;
  variant?: "primary" | "danger";
};

/** Next merchant/staff transitions for food + hyperlocal kitchen flows. */
export function merchantActionsFor(order: Order): MerchantAction[] {
  const { status, state_machine_profile: profile } = order;
  const actions: MerchantAction[] = [];

  if (status === "PAYMENT_CONFIRMED") {
    actions.push({ label: "Accept order", to_status: "ACCEPTED", actor: "merchant" });
  } else if (status === "ACCEPTED") {
    if (profile === "HYPERLOCAL_DELIVERY") {
      actions.push({ label: "Start picking", to_status: "PICKING", actor: "staff" });
    } else if (profile === "FOOD_DELIVERY") {
      actions.push({ label: "Start preparing", to_status: "PREPARING", actor: "merchant" });
    }
  } else if (status === "PREPARING" && profile === "FOOD_DELIVERY") {
    actions.push({ label: "Mark ready", to_status: "READY", actor: "merchant" });
  } else if (status === "PICKING" && profile === "HYPERLOCAL_DELIVERY") {
    actions.push({ label: "Mark ready", to_status: "READY", actor: "staff" });
  }

  if (["PAYMENT_CONFIRMED", "ACCEPTED", "PREPARING", "PICKING"].includes(status)) {
    actions.push({
      label: "Cancel order",
      to_status: "CANCELLED",
      actor: "merchant",
      variant: "danger",
    });
  }

  return actions;
}

export const KITCHEN_STATUSES = [
  "PAYMENT_CONFIRMED",
  "ACCEPTED",
  "PREPARING",
  "PICKING",
  "READY",
] as const;

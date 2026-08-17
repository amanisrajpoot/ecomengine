/** Rider-actor order transitions after pickup is assigned. */

const PROFILE_TRANSITIONS: Record<string, Record<string, string[]>> = {
  FOOD_DELIVERY: {
    READY: ["PICKED_UP"],
    PICKED_UP: ["OUT_FOR_DELIVERY"],
    OUT_FOR_DELIVERY: ["DELIVERED"],
  },
  HYPERLOCAL_DELIVERY: {
    READY: ["PICKED_UP"],
    PICKED_UP: ["OUT_FOR_DELIVERY"],
    OUT_FOR_DELIVERY: ["DELIVERED"],
  },
  COURIER: {
    PICKUP_ASSIGNED: ["PICKED_UP"],
    PICKED_UP: ["IN_TRANSIT"],
    IN_TRANSIT: ["DELIVERED"],
  },
};

export function riderTransitionsFor(profile: string, currentStatus: string): string[] {
  const profileMap = PROFILE_TRANSITIONS[profile] ?? PROFILE_TRANSITIONS.FOOD_DELIVERY;
  return profileMap[currentStatus] ?? [];
}

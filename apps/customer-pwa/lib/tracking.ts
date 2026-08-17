import type { OrderTracking } from "@commerce/types";
import type { MapMarker } from "@commerce/ui";

const ACTIVE_TRACKING_STATUSES = new Set([
  "ACCEPTED",
  "PREPARING",
  "PICKING",
  "READY",
  "PICKED_UP",
  "OUT_FOR_DELIVERY",
  "IN_TRANSIT",
  "PICKUP_ASSIGNED",
]);

export function orderShowsLiveMap(status: string): boolean {
  return ACTIVE_TRACKING_STATUSES.has(status);
}

export function trackingToMarkers(tracking: OrderTracking): MapMarker[] {
  const markers: MapMarker[] = [];

  for (const stop of tracking.stops) {
    markers.push({
      id: stop.id,
      lat: stop.lat,
      lng: stop.lng,
      label: `${stop.stop_type} · ${stop.status}`,
      variant: stop.stop_type === "PICKUP" ? "pickup" : stop.stop_type === "DROP" ? "drop" : "default",
    });
  }

  if (tracking.rider) {
    markers.push({
      id: `rider-${tracking.rider.partner_id}`,
      lat: tracking.rider.lat,
      lng: tracking.rider.lng,
      label: "Rider",
      variant: "rider",
    });
  }

  return markers;
}

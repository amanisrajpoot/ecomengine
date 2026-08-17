import type { Delivery } from "@commerce/types";
import type { MapMarker } from "@commerce/ui";

export function deliveryToMarkers(
  delivery: Delivery,
  rider?: { lat: number; lng: number } | null,
): MapMarker[] {
  const markers: MapMarker[] = (delivery.stops ?? []).map((stop) => ({
    id: stop.id,
    lat: stop.lat,
    lng: stop.lng,
    label: `${stop.stop_type} · ${stop.status}`,
    variant: stop.stop_type === "PICKUP" ? "pickup" : stop.stop_type === "DROP" ? "drop" : "default",
  }));

  if (rider) {
    markers.push({
      id: "rider-me",
      lat: rider.lat,
      lng: rider.lng,
      label: "You",
      variant: "rider",
    });
  }

  return markers;
}

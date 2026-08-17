export type MapMarker = {
  id: string;
  lat: number;
  lng: number;
  label?: string;
  variant?: "rider" | "pickup" | "drop" | "default";
};

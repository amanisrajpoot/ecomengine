"use client";

import { useEffect, useMemo } from "react";
import L from "leaflet";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";

import "leaflet/dist/leaflet.css";

export type MapMarker = {
  id: string;
  lat: number;
  lng: number;
  label?: string;
  variant?: "rider" | "pickup" | "drop" | "default";
};

export type LiveMapProps = {
  markers: MapMarker[];
  height?: number;
  className?: string;
};

const VARIANT_COLORS: Record<string, string> = {
  rider: "#2563eb",
  pickup: "#ea580c",
  drop: "#059669",
  default: "#4b5563",
};

function markerIcon(color: string) {
  return L.divIcon({
    className: "",
    html: `<div style="width:14px;height:14px;border-radius:9999px;background:${color};border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,.35)"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
}

function FitBounds({ markers }: { markers: MapMarker[] }) {
  const map = useMap();
  useEffect(() => {
    if (markers.length === 0) return;
    const lats = markers.map((m) => m.lat);
    const lngs = markers.map((m) => m.lng);
    const south = Math.min(...lats);
    const north = Math.max(...lats);
    const west = Math.min(...lngs);
    const east = Math.max(...lngs);
    if (south === north && west === east) {
      map.setView([south, west], 15);
      return;
    }
    map.fitBounds(
      [
        [south, west],
        [north, east],
      ],
      { padding: [32, 32], maxZoom: 16 },
    );
  }, [map, markers]);
  return null;
}

function computeCenter(markers: MapMarker[]): [number, number] {
  if (markers.length === 0) return [12.9716, 77.5946];
  const lat = markers.reduce((sum, m) => sum + m.lat, 0) / markers.length;
  const lng = markers.reduce((sum, m) => sum + m.lng, 0) / markers.length;
  return [lat, lng];
}

export function LiveMap({ markers, height = 240, className = "" }: LiveMapProps) {
  const center = useMemo(() => computeCenter(markers), [markers]);

  if (markers.length === 0) {
    return (
      <div
        className={`flex items-center justify-center rounded-2xl border border-dashed border-gray-200 bg-gray-50 text-sm text-gray-500 ${className}`}
        style={{ height }}
      >
        No map points yet
      </div>
    );
  }

  return (
    <div
      className={`overflow-hidden rounded-2xl border border-gray-200 shadow-sm ${className}`}
      style={{ height }}
    >
      <MapContainer
        center={center}
        zoom={14}
        scrollWheelZoom={false}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution="&copy; OpenStreetMap"
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitBounds markers={markers} />
        {markers.map((marker) => {
          const variant = marker.variant ?? "default";
          return (
            <Marker
              key={marker.id}
              position={[marker.lat, marker.lng]}
              icon={markerIcon(VARIANT_COLORS[variant] ?? VARIANT_COLORS.default)}
            >
              {marker.label ? <Popup>{marker.label}</Popup> : null}
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}

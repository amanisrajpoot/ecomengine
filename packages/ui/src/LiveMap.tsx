"use client";

import { useEffect, useState, type ComponentType } from "react";

import type { MapMarker } from "./map-types";

export type { MapMarker } from "./map-types";

export type LiveMapProps = {
  markers: MapMarker[];
  height?: number;
  className?: string;
};

type LiveMapInnerComponent = ComponentType<LiveMapProps>;

export function LiveMap({ markers, height = 240, className = "" }: LiveMapProps) {
  const [Inner, setInner] = useState<LiveMapInnerComponent | null>(null);

  useEffect(() => {
    let cancelled = false;
    import("./LiveMapInner").then((mod) => {
      if (!cancelled) setInner(() => mod.LiveMapInner);
    });
    return () => {
      cancelled = true;
    };
  }, []);

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

  if (!Inner) {
    return (
      <div
        className={`flex items-center justify-center rounded-2xl border border-gray-200 bg-gray-50 text-sm text-gray-500 ${className}`}
        style={{ height }}
      >
        Loading map…
      </div>
    );
  }

  return <Inner markers={markers} height={height} className={className} />;
}

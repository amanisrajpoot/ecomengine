"use client";

import { useEffect, useRef } from "react";

import { getApiClient } from "@/lib/api";

type UseLiveGpsOptions = {
  enabled?: boolean;
  intervalMs?: number;
};

export function useLiveGps({ enabled = true, intervalMs = 12000 }: UseLiveGpsOptions = {}) {
  const lastSent = useRef(0);

  useEffect(() => {
    if (!enabled || typeof navigator === "undefined" || !navigator.geolocation) return;

    let cancelled = false;

    async function ping(lat: number, lng: number) {
      const now = Date.now();
      if (now - lastSent.current < intervalMs - 500) return;
      lastSent.current = now;
      try {
        await getApiClient().updatePartnerLocation({ lat, lng });
      } catch {
        // ignore transient GPS upload failures
      }
    }

    function onPosition(position: GeolocationPosition) {
      if (cancelled) return;
      ping(position.coords.latitude, position.coords.longitude);
    }

    navigator.geolocation.getCurrentPosition(onPosition, () => undefined, {
      enableHighAccuracy: true,
      maximumAge: 5000,
    });

    const timer = window.setInterval(() => {
      navigator.geolocation.getCurrentPosition(onPosition, () => undefined, {
        enableHighAccuracy: true,
        maximumAge: 5000,
      });
    }, intervalMs);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [enabled, intervalMs]);
}

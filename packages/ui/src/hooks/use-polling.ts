"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export type UsePollingOptions<T> = {
  intervalMs?: number;
  enabled?: boolean;
  immediate?: boolean;
  onData?: (data: T, previous: T | null) => void;
};

export function usePolling<T>(
  fetcher: () => Promise<T>,
  options: UsePollingOptions<T> = {},
) {
  const { intervalMs = 15000, enabled = true, immediate = true, onData } = options;
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(immediate);
  const previousRef = useRef<T | null>(null);
  const onDataRef = useRef(onData);
  onDataRef.current = onData;

  const refresh = useCallback(async () => {
    try {
      const result = await fetcher();
      onDataRef.current?.(result, previousRef.current);
      previousRef.current = result;
      setData(result);
      setError(null);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetcher]);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    if (immediate) {
      refresh().catch(() => undefined);
    }
    const timer = window.setInterval(() => {
      if (!cancelled) refresh().catch(() => undefined);
    }, intervalMs);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [enabled, immediate, intervalMs, refresh]);

  return { data, error, loading, refresh };
}

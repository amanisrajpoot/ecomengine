import type { DayHours } from "@commerce/types";

export const WEEKDAYS: Array<{ key: string; label: string }> = [
  { key: "mon", label: "Monday" },
  { key: "tue", label: "Tuesday" },
  { key: "wed", label: "Wednesday" },
  { key: "thu", label: "Thursday" },
  { key: "fri", label: "Friday" },
  { key: "sat", label: "Saturday" },
  { key: "sun", label: "Sunday" },
];

export function defaultHours(): DayHours[] {
  return WEEKDAYS.map(({ key }) => ({
    day: key,
    open: "09:00",
    close: "22:00",
    closed: false,
  }));
}

export function normalizeHours(raw: DayHours[] | undefined): DayHours[] {
  const map = new Map((raw ?? []).map((row) => [row.day.toLowerCase(), row]));
  return WEEKDAYS.map(({ key }) => {
    const row = map.get(key);
    return {
      day: key,
      open: row?.open ?? "09:00",
      close: row?.close ?? "22:00",
      closed: row?.closed ?? false,
    };
  });
}

export function addressField(
  address: Record<string, unknown>,
  key: string,
  fallback = "",
): string {
  const value = address[key];
  return typeof value === "string" ? value : fallback;
}

export function capabilityLabels(capabilities: Record<string, unknown> | undefined): string[] {
  if (!capabilities) return [];
  return Object.entries(capabilities)
    .filter(([, enabled]) => Boolean(enabled))
    .map(([key]) => key);
}

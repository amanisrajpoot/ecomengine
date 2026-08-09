"use client";

import type { DayHours } from "@commerce/types";
import { TextField } from "@commerce/ui";

import { WEEKDAYS } from "../lib/settings-helpers";

type HoursEditorProps = {
  hours: DayHours[];
  onChange: (hours: DayHours[]) => void;
  className?: string;
};

export function HoursEditor({ hours, onChange, className = "" }: HoursEditorProps) {
  function updateDay(day: string, patch: Partial<DayHours>) {
    onChange(
      hours.map((row) => (row.day === day ? { ...row, ...patch } : row)),
    );
  }

  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      {WEEKDAYS.map(({ key, label }) => {
        const row = hours.find((h) => h.day === key) ?? {
          day: key,
          open: "09:00",
          close: "22:00",
          closed: false,
        };
        return (
          <div
            key={key}
            className="grid gap-2 rounded-xl border border-amber-200/10 bg-amber-950/15 p-3 sm:grid-cols-[1fr_auto_auto_auto]"
          >
            <span className="text-sm text-amber-50/80">{label}</span>
            <label className="flex items-center gap-2 text-xs text-amber-100/60">
              <input
                type="checkbox"
                checked={row.closed ?? false}
                onChange={(e) => updateDay(key, { closed: e.target.checked })}
              />
              Closed
            </label>
            <input
              type="time"
              disabled={row.closed}
              value={row.open ?? "09:00"}
              onChange={(e) => updateDay(key, { open: e.target.value })}
              className="rounded-lg border border-amber-200/15 bg-amber-950/40 px-2 py-1 text-sm text-amber-50 disabled:opacity-40"
            />
            <input
              type="time"
              disabled={row.closed}
              value={row.close ?? "22:00"}
              onChange={(e) => updateDay(key, { close: e.target.value })}
              className="rounded-lg border border-amber-200/15 bg-amber-950/40 px-2 py-1 text-sm text-amber-50 disabled:opacity-40"
            />
          </div>
        );
      })}
    </div>
  );
}

type AddressFieldsProps = {
  line1: string;
  city: string;
  state: string;
  pincode: string;
  onChange: (field: "line1" | "city" | "state" | "pincode", value: string) => void;
};

export function AddressFields({ line1, city, state, pincode, onChange }: AddressFieldsProps) {
  return (
    <div className="flex flex-col gap-3">
      <TextField
        label="Address line"
        value={line1}
        onChange={(e) => onChange("line1", e.target.value)}
        className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
      />
      <div className="grid gap-3 sm:grid-cols-2">
        <TextField
          label="City"
          value={city}
          onChange={(e) => onChange("city", e.target.value)}
          className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
        />
        <TextField
          label="State"
          value={state}
          onChange={(e) => onChange("state", e.target.value)}
          className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
        />
      </div>
      <TextField
        label="Pincode"
        value={pincode}
        onChange={(e) => onChange("pincode", e.target.value)}
        maxLength={6}
        className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
      />
    </div>
  );
}

/** Shared domain primitives (Phase 0 placeholders). */

export type TenantId = string;
export type UserId = string;
export type BusinessId = string;
export type OrderId = string;

/** Money in integer paise (INR). Never use floating point for currency. */
export type MoneyPaise = number;

export interface Money {
  amountPaise: MoneyPaise;
  currency: "INR";
}

export type BusinessType = "FOOD" | "RETAIL" | "GROCERY" | "COURIER";

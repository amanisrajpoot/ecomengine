# Tax Engine (India GST)

## Principle

Tax is an **independent module**. Pricing calls it; ledger/settlement consume its outputs.

Never label every tax line simply as `GST`. Distinguish:

| Kind | Meaning |
|------|---------|
| **Customer transaction tax** | Tax collected on the customer-facing order (item/delivery as applicable) |
| **Platform service tax** | GST on platform commission / convenience fees |
| **Merchant settlement deductions** | Tax components affecting merchant net (e.g. commission GST) |

---

## India V1 model

- Currency: INR
- Components: **CGST**, **SGST**, **IGST** (and cess if configured later)
- Intra-state typically CGST + SGST; inter-state IGST
- Rates stored in **basis points** (`rate_bps`)
- Support `inclusive` vs `exclusive` pricing flags on rules / catalog

Place of supply rules should be documented per fee/item category; V1 may use simplified jurisdiction resolution from business location + customer address state codes.

---

## TaxRule

```text
TaxRule
 ├── code                 # CGST | SGST | IGST | CESS | ...
 ├── category             # GOODS | SERVICE | DELIVERY | PLATFORM_FEE | COMMISSION | ...
 ├── jurisdiction         # IN / state code / ALL
 ├── rate_bps
 ├── inclusive            # bool
 ├── payer                # CUSTOMER | MERCHANT | PLATFORM
 ├── kind                 # CUSTOMER_TRANSACTION | PLATFORM_SERVICE | SETTLEMENT_DEDUCTION
 ├── effective_from
 ├── effective_to
 └── tenant_id           # null = platform default
```

---

## Calculation output

```json
{
  "tax_paise": 2500,
  "lines": [
    {
      "code": "CGST",
      "kind": "CUSTOMER_TRANSACTION",
      "category": "GOODS",
      "rate_bps": 250,
      "taxable_paise": 50000,
      "amount_paise": 1250,
      "payer": "CUSTOMER"
    },
    {
      "code": "SGST",
      "kind": "CUSTOMER_TRANSACTION",
      "category": "GOODS",
      "rate_bps": 250,
      "taxable_paise": 50000,
      "amount_paise": 1250,
      "payer": "CUSTOMER"
    }
  ]
}
```

Platform commission example (settlement time / ledger events):

```json
{
  "code": "CGST",
  "kind": "PLATFORM_SERVICE",
  "category": "COMMISSION",
  "payer": "MERCHANT",
  "amount_paise": 900
}
```

---

## Integration points

1. **Checkout / pricing** — customer transaction tax lines → price breakdown
2. **Ledger** — separate entries for tax liability vs commission GST
3. **Settlement** — merchant payable already net of settlement-related tax lines posted to ledger

---

## Non-goals (V1)

- Full GSTR filing product
- Every HSN/SAC edge case
- Multi-country tax

Keep rules data-driven so rates can change without code forks.

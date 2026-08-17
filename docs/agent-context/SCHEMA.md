# `docs/schema.md` line index

Read **one slice** with Read `offset` + `limit`. Do not load the full spec.

File: `docs/schema.md` (Phase 0 spec; migrations start Phase 1)

| Slice | Heading | offset | limit (approx) |
|-------|---------|--------|----------------|
| Conventions | top | 1 | 14 |
| Tenants / platform_config | tenancy & config | 15 | 24 |
| Users / roles / profiles | identity | 39 | 40 |
| Partner profiles / vehicles | still identity | 78 | 28 |
| businesses | businesses | 106 | 20 |
| business_locations | business_locations | 126 | 18 |
| categories…bundles | catalog | 144 | 81 |
| inventory_items / movements | inventory | 225 | 37 |
| carts / cart_items | cart | 262 | 28 |
| orders / items / status_events | orders | 290 | 46 |
| payments / refunds | payments | 336 | 35 |
| tax_rules | tax | 371 | 21 |
| ledger_entries | ledger | 394 | 18 |
| settlements + links | settlements | 412 | 24 |
| fulfillments | fulfillments | 438 | 13 |
| deliveries / stops | delivery | 451 | 30 |
| promotions stub | promotions | 481 | 20 |

If you insert tables in schema.md, **fix the offsets in this file** in the same PR (or the index lies and agents will over-read).

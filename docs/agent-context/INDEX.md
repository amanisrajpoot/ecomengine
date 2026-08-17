# Agent context index

**Load this first, then `STATE.md`. Stop. Do not open the rest of `docs/` unless a row below says so.**

Full specs stay in `docs/*.md`. This folder is the *router* so agents spend tokens on code, not re-reading architecture.

## Session start (always)

| File | Why |
|------|-----|
| [INDEX.md](./INDEX.md) | This map |
| [STATE.md](./STATE.md) | Current phase, version, next task, stale warnings |
| [PROTOCOL.md](./PROTOCOL.md) | Token budget and how to update STATE |

## Then only the matching row

| Task | Read next (in order) |
|------|----------------------|
| What exists on disk | [MAP.md](./MAP.md) |
| Invariants / do-not-fork | [RULES.md](./RULES.md) |
| Auth, RBAC, tenants | `docs/permissions.md`, `docs/api-conventions.md` |
| Business / locations | `docs/domain-model.md` (Business, Location) |
| Catalog / addons | `docs/domain-model.md`, `docs/schema.md` (catalog tables) |
| Inventory | `docs/schema.md` (inventory), `docs/domain-model.md` |
| Cart / pricing | `docs/pricing-engine.md` |
| GST / tax | `docs/tax-engine.md` |
| Orders / status | `docs/order-state-machines.md` |
| Payments | `docs/api-conventions.md` + `backend/app/payments/` when it exists |
| Ledger | `docs/settlement-engine.md` (ledger section) |
| Settlements | `docs/settlement-engine.md` |
| Fulfillment / delivery | `docs/fulfillment.md` |
| Roadmap / which phase | `docs/milestones.md` (only if changing sequence) |
| Stack / V1 exclusions | `docs/architecture.md` (only if changing shape) |
| Module layout / money | `docs/coding-conventions.md` or [RULES.md](./RULES.md) |
| UI / PWA screens | `apps/<app>/` + `packages/ui/` — grep first |

## Do not

- Paste entire spec files into chat or PR bodies
- Re-summarize all past phases in every reply
- Glob the whole repo before Grep
- Append history essays to `STATE.md` — replace stale lines

# Permissions & RBAC

## Roles

| Role | Description |
|------|-------------|
| `SUPER_ADMIN` | Platform-wide |
| `TENANT_ADMIN` | Full tenant ops |
| `BUSINESS_OWNER` | Owns business(es) |
| `BUSINESS_MANAGER` | Operates business |
| `STAFF` | Limited business ops (orders/catalog subset) |
| `DELIVERY_PARTNER` | Rider |
| `CUSTOMER` | End customer |

Bindings are always evaluated with **tenant** (and business/location when relevant).

---

## Capability matrix (V1 sketch)

| Action | SUPER_ADMIN | TENANT_ADMIN | OWNER | MANAGER | STAFF | RIDER | CUSTOMER |
|--------|:-----------:|:------------:|:-----:|:-------:|:-----:|:-----:|:--------:|
| Manage tenants | Y | — | — | — | — | — | — |
| Manage tenant config | Y | Y | — | — | — | — | — |
| Create business | Y | Y | Y* | — | — | — | — |
| Edit business settings | Y | Y | Y | Y | — | — | — |
| Manage catalog | Y | Y | Y | Y | limited | — | — |
| Manage inventory | Y | Y | Y | Y | limited | — | — |
| Accept/reject orders | Y | Y | Y | Y | Y | — | — |
| View settlements | Y | Y | Y | Y | — | own | — |
| Approve settlements | Y | Y | — | — | — | — | — |
| Go online / accept jobs | — | — | — | — | — | Y | — |
| Place orders | — | — | — | — | — | — | Y |
| Initiate / verify payments | Y | Y | Y | — | — | — | Y |
| Refund payments | Y | Y | — | — | — | — | — |
| Track own orders | — | — | — | — | — | assigned | own |
| Order debugger | Y | Y | — | — | — | — | — |

\* Owner create may be self-serve onboarding under tenant policy.

---

## Business capabilities vs RBAC

RBAC answers **who** may call an API.

Business `capabilities` answer **whether a feature exists** for that business (e.g. hide inventory UI if `inventory: false`).

Both must pass:

```text
allowed = has_role_permission(action) AND business_supports(capability)
```

---

## Implementation notes (Phase 1+)

- Store role bindings in `user_role_bindings(user_id, role, tenant_id, business_id nullable)`
- Enforce in FastAPI dependencies
- Never trust client-sent role claims without server-side binding check

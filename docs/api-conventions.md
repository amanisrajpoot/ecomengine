# API Conventions

## Base

- Prefix: `/api/v1`
- JSON request/response
- UTF-8
- Times in UTC ISO-8601; display TZ `Asia/Kolkata` in clients

Health (outside versioned API):

- `GET /health` → `{ "status": "ok" }`
- `GET /api/v1/meta` → `{ "name": "commerce-engine", "version": "0.0.0" }`

---

## Tenancy

Every tenant-scoped request must resolve `tenant_id`.

V1 resolution order:

1. `X-Tenant-ID` header (UUID), or
2. Host / slug mapping (later)

Platform super-admin routes may omit tenant where documented.

Unauthorized cross-tenant access → `403`.

---

## Auth

(Phase 1+)

- Bearer JWT (access) after OTP / email-password
- `Authorization: Bearer <token>`

---

## Idempotency

Unsafe endpoints that create payments or orders accept:

```http
Idempotency-Key: <client-generated-string>
```

Replay with same key returns the original result.

---

## Error envelope

```json
{
  "error": {
    "code": "ORDER_ILLEGAL_TRANSITION",
    "message": "Cannot move from READY to ACCEPTED",
    "details": {}
  }
}
```

| HTTP | Use |
|------|-----|
| 400 | Validation |
| 401 | Unauthenticated |
| 403 | Forbidden |
| 404 | Not found |
| 409 | Conflict / illegal state |
| 422 | Semantic validation |
| 429 | Rate limit |
| 500 | Unexpected |

---

## Pagination

Cursor or offset; V1 default **offset**:

```text
GET /api/v1/orders?limit=20&offset=0
```

Response:

```json
{
  "data": [],
  "meta": {
    "limit": 20,
    "offset": 0,
    "total": 0
  }
}
```

---

## Money

All monetary fields end with `_paise` (integer). Currency field `currency: "INR"` where objects are returned.

---

## Resource naming

- Plural nouns: `/orders`, `/businesses`, `/products`
- Nested only when ownership is strict: `/businesses/{id}/locations`
- Actions as sub-resources sparingly: `/orders/{id}/transitions`

---

## Versioning

Breaking changes require `/api/v2`. Additive fields are allowed in v1.

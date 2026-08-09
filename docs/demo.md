# Testing with demo data

You can test **all four apps today** once the API is running and demo data is seeded.

## Quick start (≈5 minutes)

### 1. Start infrastructure + API

```bash
cp .env.example .env
docker compose up --build
```

On first boot the backend container runs migrations, bootstrap admin, tax rules, and **`seed_demo`** automatically.

**Or** run the API locally:

```bash
docker compose up postgres redis minio -d
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. alembic upgrade head
PYTHONPATH=. python -m app.scripts.bootstrap_super_admin
PYTHONPATH=. python -m app.scripts.seed_tax_rules
PYTHONPATH=. python -m app.scripts.seed_demo
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

### 2. Seed demo (if not using Docker backend)

```bash
pnpm demo:seed
# writes demo.env at repo root with tenant UUID + credentials
source demo.env
```

### 3. Start frontend apps

In separate terminals (from repo root):

```bash
source demo.env   # sets NEXT_PUBLIC_TENANT_ID and API URL
pnpm install

pnpm dev:customer   # http://localhost:3000
pnpm dev:merchant   # http://localhost:3001
pnpm dev:rider      # http://localhost:3002
pnpm dev:admin      # http://localhost:3003
```

Or copy `demo.env` → `apps/customer-pwa/.env.local` (same for other apps).

## Demo credentials

| App | URL | Login | Password | Tenant ID |
|-----|-----|-------|----------|-----------|
| **Customer** | :3000 | `customer@demo.com` | `Demo123!` | Required — from `demo.env` |
| **Merchant** | :3001 | `merchant@demo.com` | `Demo123!` | Required |
| **Rider** | :3002 | `rider@demo.com` | `Demo123!` | Required |
| **Admin** | :3003 | `admin@example.com` | `ChangeMe123!` | Optional — set tenant for order debugger |

## What’s in the demo tenant

Single tenant **`commerce-demo`** includes:

| Business | Type | Try in |
|----------|------|--------|
| Spice Kitchen | FOOD | Customer → Browse → order Butter Chicken (COD) |
| FreshMart Indiranagar | GROCERY | Customer → Browse (grocery filter) |
| CityDash Courier | COURIER | Customer → Courier quote/book |

Default browse coordinates: **Bengaluru Indiranagar** (`12.9784, 77.6408`).

## End-to-end food flow (manual)

1. **Customer** (:3000) — login → Browse → Spice Kitchen → add Butter Chicken → Cart → checkout COD (`9876543210`)
2. **Merchant** (:3001) — login → Orders → Accept → Preparing → Ready
3. **Rider** (:3002) — login → Go online → complete pickup/drop POD on assigned job
4. **Admin** (:3003) — login (paste tenant ID) → Orders → open debugger chain

## API-only checks

```bash
source demo.env
curl -s http://localhost:8000/health
curl -s "http://localhost:8000/api/v1/stores/nearby?lat=12.9784&lng=77.6408&radius_km=8" \
  -H "Authorization: Bearer $TOKEN" -H "X-Tenant-ID: $NEXT_PUBLIC_TENANT_ID"
```

## Re-seed

`seed_demo` is idempotent — safe to re-run:

```bash
pnpm demo:seed
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Empty browse | Confirm `NEXT_PUBLIC_TENANT_ID` matches `demo.env` |
| Rider login fails | Re-run `seed_demo` (creates partner profile + vehicle) |
| Merchant sees no orders | Place an order as customer first; select Spice Kitchen business |
| CORS / API errors | Ensure API at `http://localhost:8000` and `NEXT_PUBLIC_API_URL` matches |

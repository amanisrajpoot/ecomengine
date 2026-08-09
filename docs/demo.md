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

### 2. Seed demo credentials

**If Docker API is running** (recommended on Windows — no local Python packages needed):

```bash
docker compose up -d    # if not already up
pnpm demo:seed          # runs seed inside the backend container, writes demo.env
```

**Or seed manually via Docker:**

```powershell
docker compose exec -T -e DEMO_ENV_PATH=/app/demo.env backend python -m app.scripts.seed_demo
docker compose cp backend:/app/demo.env ./demo.env
```

**Local Python** (only if you installed backend deps in a venv):

```powershell
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m app.scripts.seed_demo
```

Then set tenant ID — open `demo.env` and copy `NEXT_PUBLIC_TENANT_ID` into each app login, or create `apps/customer-pwa/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_TENANT_ID=<uuid-from-demo.env>
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

## End-to-end food flow

1. **Rider** (:3002) — login → **Go online** (do this before or while kitchen prepares)
2. **Customer** (:3000) — login → Browse → Spice Kitchen → add item → Cart → checkout COD
3. **Merchant** (:3001) — login → Orders → Accept → Preparing → **Ready** (auto-assigns rider)
4. **Rider** (:3002) — job appears → complete pickup/drop POD
5. **Admin** (:3003) — login (tenant from `demo.env`) → Dispatch or Orders → debugger

If no rider was online at Ready, use **Request rider** on merchant order detail or **Admin → Dispatch**.

## End-to-end courier flow

1. **Rider** — Go online
2. **Customer** — Courier tab → quote → book COD (courier business ID from `demo.env`)
3. **Rider** — assigned job after payment → POD

## End-to-end food flow (legacy manual API — no longer required)

Removed — dispatch is automatic + in-app retry.

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
| `pnpm demo:seed` / `No module named 'asyncpg'` | Start Docker (`docker compose up -d`) and run `pnpm demo:seed` again — it seeds via the container. Or install backend venv deps (see above). |
| Empty browse | Confirm `NEXT_PUBLIC_TENANT_ID` matches `demo.env` |
| Rider login fails | Re-run `seed_demo` (creates partner profile + vehicle) |
| Rider sees no jobs | Go **online** on Rider PWA **before** merchant marks Ready; or use Merchant **Request rider** / Admin **Dispatch** |
| CORS / API errors / **405 on OPTIONS** | Pull latest and **rebuild Docker**: `docker compose up --build -d`. PWAs on :3000–3003 need CORS from API :8000. |

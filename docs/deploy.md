# Deploy anywhere (Docker)

Run the **entire stack** — Postgres, Redis, MinIO, API, and all four PWAs — with one command.

## Quick deploy

```bash
git clone https://github.com/amanisrajpoot/ecomengine.git
cd ecomengine

cp .env.production.example .env
# Edit .env: set PUBLIC_HOST, JWT_SECRET, POSTGRES_PASSWORD, CORS_ORIGINS, NEXT_PUBLIC_API_URL

docker compose -f docker-compose.prod.yml up -d --build
```

First boot runs migrations, seeds demo data, and starts all services (~5–10 min build on a small VM).

## URLs

| Service | Default URL |
|---------|-------------|
| API | `http://HOST:8000` |
| API docs | `http://HOST:8000/docs` |
| Customer PWA | `http://HOST:3000` |
| Merchant PWA | `http://HOST:3001` |
| Rider PWA | `http://HOST:3002` |
| Admin | `http://HOST:3003` |

## Demo login

```bash
docker compose -f docker-compose.prod.yml exec backend cat /app/demo.env
```

Use emails/passwords from `demo.env` and paste `NEXT_PUBLIC_TENANT_ID` on each app login screen.

## Oracle Cloud Free Tier

1. Create an **Ampere A1** VM (2 OCPU / 8GB RAM minimum recommended).
2. Open ingress: **22, 8000, 3000–3003**.
3. Install Docker: `curl -fsSL https://get.docker.com | sudo sh`
4. Clone repo, edit `.env`:

```env
PUBLIC_HOST=YOUR_PUBLIC_IP
NEXT_PUBLIC_API_URL=http://YOUR_PUBLIC_IP:8000
CORS_ORIGINS=http://YOUR_PUBLIC_IP:3000,http://YOUR_PUBLIC_IP:3001,http://YOUR_PUBLIC_IP:3002,http://YOUR_PUBLIC_IP:3003
JWT_SECRET=<long-random-string>
POSTGRES_PASSWORD=<strong-password>
OTP_ECHO_IN_RESPONSE=false
```

5. Deploy:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

6. If ports are blocked on Ubuntu, open iptables:

```bash
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 3000:3003 -j ACCEPT
```

## Commands

```bash
# Logs
docker compose -f docker-compose.prod.yml logs -f

# Stop
docker compose -f docker-compose.prod.yml down

# Rebuild after code pull
docker compose -f docker-compose.prod.yml up -d --build

# Re-seed demo data
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.seed_demo
docker compose -f docker-compose.prod.yml cp backend:/app/demo.env ./demo.env
```

## Local dev (unchanged)

For hot-reload frontends, use the slim compose file:

```bash
docker compose up -d          # API + postgres + redis + minio only
pnpm dev:customer             # etc.
```

## Changing the API URL

`NEXT_PUBLIC_API_URL` is baked in at **image build time**. After changing it in `.env`:

```bash
docker compose -f docker-compose.prod.yml build customer merchant rider admin
docker compose -f docker-compose.prod.yml up -d
```

## Requirements

- Docker 24+ with Compose v2
- ~4GB RAM for full stack
- ~10GB disk for images + volumes

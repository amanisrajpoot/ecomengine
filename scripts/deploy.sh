#!/usr/bin/env bash
# Deploy (or redeploy) the full Commerce Engine stack.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

COMPOSE_FILE="docker-compose.prod.yml"

if [ ! -f .env ]; then
  echo "Missing .env — copy and edit first:"
  echo "  cp .env.production.example .env"
  echo "  nano .env   # set PUBLIC_HOST, JWT_SECRET, POSTGRES_PASSWORD, CORS_ORIGINS, NEXT_PUBLIC_API_URL"
  exit 1
fi

# shellcheck disable=SC1091
set -a && source .env && set +a

if [ -z "${PUBLIC_HOST:-}" ] || [ "$PUBLIC_HOST" = "localhost" ]; then
  echo "Warning: PUBLIC_HOST is still localhost. Set it to your VM public IP in .env"
fi

echo "==> Building and starting stack (first run may take 10–15 min)..."
docker compose -f "$COMPOSE_FILE" up -d --build

echo "==> Waiting for API health..."
for i in $(seq 1 60); do
  if curl -sf "http://127.0.0.1:${API_PORT:-8000}/health" >/dev/null; then
    echo "API is up."
    break
  fi
  sleep 5
  if [ "$i" -eq 60 ]; then
    echo "API did not become healthy in time. Check: docker compose -f $COMPOSE_FILE logs backend"
    exit 1
  fi
done

echo ""
echo "==> Deployed. URLs (replace HOST with ${PUBLIC_HOST:-your-ip}):"
echo "  API:      http://${PUBLIC_HOST:-HOST}:${API_PORT:-8000}"
echo "  Customer: http://${PUBLIC_HOST:-HOST}:${CUSTOMER_PORT:-3000}"
echo "  Merchant: http://${PUBLIC_HOST:-HOST}:${MERCHANT_PORT:-3001}"
echo "  Rider:    http://${PUBLIC_HOST:-HOST}:${RIDER_PORT:-3002}"
echo "  Admin:    http://${PUBLIC_HOST:-HOST}:${ADMIN_PORT:-3003}"
echo ""
echo "Demo credentials:"
docker compose -f "$COMPOSE_FILE" exec -T backend cat /app/demo.env 2>/dev/null || true

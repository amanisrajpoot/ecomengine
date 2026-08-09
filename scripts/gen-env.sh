#!/usr/bin/env bash
# Generate .env from your VM public IP (run on the Oracle VM).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PUBLIC_IP="${1:-}"
if [ -z "$PUBLIC_IP" ]; then
  PUBLIC_IP="$(curl -fsSL ifconfig.me 2>/dev/null || curl -fsSL icanhazip.com 2>/dev/null || true)"
fi

if [ -z "$PUBLIC_IP" ]; then
  echo "Usage: $0 <PUBLIC_IP>"
  echo "  or run on VM with internet to auto-detect IP"
  exit 1
fi

JWT_SECRET="$(openssl rand -hex 32 2>/dev/null || head -c 32 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9' | head -c 48)"
DB_PASS="$(openssl rand -hex 16 2>/dev/null || head -c 16 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9' | head -c 24)"

cat > .env <<EOF
PUBLIC_HOST=${PUBLIC_IP}
NEXT_PUBLIC_API_URL=http://${PUBLIC_IP}:8000
CORS_ORIGINS=http://${PUBLIC_IP}:3000,http://${PUBLIC_IP}:3001,http://${PUBLIC_IP}:3002,http://${PUBLIC_IP}:3003

API_PORT=8000
CUSTOMER_PORT=3000
MERCHANT_PORT=3001
RIDER_PORT=3002
ADMIN_PORT=3003

POSTGRES_USER=commerce
POSTGRES_PASSWORD=${DB_PASS}
POSTGRES_DB=commerce

ENVIRONMENT=production
JWT_SECRET=${JWT_SECRET}
OTP_ECHO_IN_RESPONSE=false
APP_NAME=commerce-engine

DATABASE_URL=postgresql+asyncpg://commerce:${DB_PASS}@postgres:5432/commerce
REDIS_URL=redis://redis:6379/0
S3_ENDPOINT_URL=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=${DB_PASS}
S3_BUCKET=commerce
S3_REGION=us-east-1

ONDC_MOCK=true
ONDC_SEND_CALLBACKS=false
NOTIFICATIONS_DEFAULT_CHANNEL=sms_mock
PAYMENTS_DEFAULT_PROVIDER=cashfree
PAYMENTS_MOCK=true
CASHFREE_CLIENT_ID=
CASHFREE_CLIENT_SECRET=
CASHFREE_ENV=sandbox
LEDGER_DEFAULT_COMMISSION_BPS=1000

BOOTSTRAP_ADMIN_EMAIL=admin@example.com
BOOTSTRAP_ADMIN_PASSWORD=ChangeMe123!
EOF

echo "Wrote .env for PUBLIC_HOST=${PUBLIC_IP}"
echo "Review: nano .env"

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${0}")/.." && pwd)"
DATA_DIR="$ROOT/e2e/.data"
DB_PATH="$DATA_DIR/commerce-e2e.db"

mkdir -p "$DATA_DIR"
rm -f "$DB_PATH"

export DATABASE_URL="sqlite+aiosqlite:///$DB_PATH"
export RATE_LIMIT_ENABLED=false
export ENVIRONMENT=test

cd "$ROOT/backend"
PYTHONPATH=. python3 "$ROOT/scripts/init-e2e-db.py"
PYTHONPATH=. python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000

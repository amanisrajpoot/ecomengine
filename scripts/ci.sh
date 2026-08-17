#!/usr/bin/env bash
# Local CI parity with GitHub Actions (.github/workflows/ci.yml).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Backend: full pytest suite"
(
  cd backend
  PYTHONPATH=. python3 -m pytest -q
)

echo "==> Golden paths: Food, Hyperlocal, Courier"
(
  cd backend
  PYTHONPATH=. python3 -m pytest -q -m golden
)

echo "==> Frontend: typecheck"
pnpm typecheck

echo "==> CI checks passed"

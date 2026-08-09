#!/usr/bin/env node
/**
 * Cross-platform demo seed: prefers Docker backend (no local Python deps),
 * falls back to backend/.venv or system python.
 */
import { execSync, spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();

function run(cmd, opts = {}) {
  execSync(cmd, { stdio: "inherit", cwd: root, ...opts });
}

function dockerBackendRunning() {
  try {
    const out = execSync("docker compose ps -q backend", {
      cwd: root,
      stdio: ["pipe", "pipe", "ignore"],
    });
    return out.toString().trim().length > 0;
  } catch {
    return false;
  }
}

function localPython() {
  const winVenv = join(root, "backend", ".venv", "Scripts", "python.exe");
  const unixVenv = join(root, "backend", ".venv", "bin", "python");
  if (existsSync(winVenv)) return winVenv;
  if (existsSync(unixVenv)) return unixVenv;
  return process.platform === "win32" ? "python" : "python3";
}

function seedViaDocker() {
  console.log("Seeding via Docker backend (no local Python packages needed)...\n");
  run("docker compose exec -T -e DEMO_ENV_PATH=/app/demo.env backend python -m app.scripts.seed_demo");
  try {
    run("docker compose cp backend:/app/demo.env ./demo.env");
    console.log("\nWrote demo.env to repo root.");
  } catch {
    console.log("\nCould not copy demo.env — check docker compose logs backend for Tenant ID.");
  }
}

function seedViaLocal() {
  const py = localPython();
  const venvHint =
    process.platform === "win32"
      ? "cd backend && python -m venv .venv && .venv\\Scripts\\pip install -r requirements.txt"
      : "cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt";

  console.log(`Seeding via local Python: ${py}\n`);
  const result = spawnSync(py, ["-m", "app.scripts.seed_demo"], {
    cwd: join(root, "backend"),
    stdio: "inherit",
    shell: process.platform === "win32",
  });

  if (result.status !== 0) {
    console.error("\n--- seed failed ---");
    console.error("Option A (recommended): start Docker API, then re-run:");
    console.error("  docker compose up -d");
    console.error("  pnpm demo:seed");
    console.error("\nOption B: install backend deps locally:");
    console.error(`  ${venvHint}`);
    process.exit(result.status ?? 1);
  }
}

if (dockerBackendRunning()) {
  seedViaDocker();
} else {
  seedViaLocal();
}

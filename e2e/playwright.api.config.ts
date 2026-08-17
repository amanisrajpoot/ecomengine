import baseConfig from "./playwright.config";
import { defineConfig } from "@playwright/test";
import path from "node:path";

const ROOT = path.join(__dirname, "..");
const API_URL = "http://127.0.0.1:8000";
const isCI = Boolean(process.env.CI);

const pwaEnv = {
  NEXT_PUBLIC_API_URL: API_URL,
};

export default defineConfig({
  ...baseConfig,
  testDir: "./tests",
  projects: [
    {
      name: "customer-api",
      testMatch: "**/customer-api.spec.ts",
      use: { baseURL: "http://127.0.0.1:3000" },
    },
    {
      name: "admin-api",
      testMatch: "**/admin-api.spec.ts",
      use: { baseURL: "http://127.0.0.1:3003" },
    },
  ],
  webServer: [
    {
      command: "bash scripts/start-e2e-api.sh",
      cwd: ROOT,
      url: `${API_URL}/health`,
      timeout: 180_000,
      reuseExistingServer: !isCI,
    },
    {
      command: "pnpm --filter @commerce/customer-pwa dev",
      cwd: ROOT,
      url: "http://127.0.0.1:3000",
      timeout: 180_000,
      reuseExistingServer: !isCI,
      env: pwaEnv,
    },
    {
      command: "pnpm --filter @commerce/admin-web dev",
      cwd: ROOT,
      url: "http://127.0.0.1:3003",
      timeout: 180_000,
      reuseExistingServer: !isCI,
      env: pwaEnv,
    },
  ],
});

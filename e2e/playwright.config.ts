import { defineConfig, devices } from "@playwright/test";
import path from "node:path";

const ROOT = path.join(__dirname, "..");
const isCI = Boolean(process.env.CI);

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: isCI,
  retries: isCI ? 1 : 0,
  workers: isCI ? 2 : undefined,
  reporter: isCI ? "github" : "list",
  timeout: 30_000,
  use: {
    trace: "on-first-retry",
    ...devices["Desktop Chrome"],
  },
  projects: [
    {
      name: "customer",
      testMatch: "**/customer.spec.ts",
      use: { baseURL: "http://127.0.0.1:3000" },
    },
    {
      name: "merchant",
      testMatch: "**/merchant.spec.ts",
      use: { baseURL: "http://127.0.0.1:3001" },
    },
    {
      name: "rider",
      testMatch: "**/rider.spec.ts",
      use: { baseURL: "http://127.0.0.1:3002" },
    },
    {
      name: "admin",
      testMatch: "**/admin.spec.ts",
      use: { baseURL: "http://127.0.0.1:3003" },
    },
  ],
  webServer: [
    {
      command: "pnpm --filter @commerce/customer-pwa dev",
      cwd: ROOT,
      url: "http://127.0.0.1:3000",
      timeout: 180_000,
      reuseExistingServer: !isCI,
    },
    {
      command: "pnpm --filter @commerce/merchant-pwa dev",
      cwd: ROOT,
      url: "http://127.0.0.1:3001",
      timeout: 180_000,
      reuseExistingServer: !isCI,
    },
    {
      command: "pnpm --filter @commerce/rider-pwa dev",
      cwd: ROOT,
      url: "http://127.0.0.1:3002",
      timeout: 180_000,
      reuseExistingServer: !isCI,
    },
    {
      command: "pnpm --filter @commerce/admin-web dev",
      cwd: ROOT,
      url: "http://127.0.0.1:3003",
      timeout: 180_000,
      reuseExistingServer: !isCI,
    },
  ],
});

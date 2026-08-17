import { test, expect } from "@playwright/test";

test.describe("Customer PWA smoke", () => {
  test("home shows brand header", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("link", { name: "Commerce" })).toBeVisible();
  });

  test("login page renders auth form", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible();
    await expect(page.getByLabel("Email")).toBeVisible();
    await expect(page.getByLabel("Password")).toBeVisible();
  });

  test("settings page loads", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.getByRole("heading", { name: "Settings" })).toBeVisible();
  });
});

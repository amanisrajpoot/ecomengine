import { test, expect } from "@playwright/test";

test.describe("Admin web smoke", () => {
  test("home shows admin console", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Admin" })).toBeVisible();
  });

  test("login page renders auth form", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByLabel("Email")).toBeVisible();
    await expect(page.getByLabel("Password")).toBeVisible();
  });

  test("orders debugger page", async ({ page }) => {
    await page.goto("/orders");
    await expect(page.getByRole("heading", { name: /orders/i })).toBeVisible();
  });
});

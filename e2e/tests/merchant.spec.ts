import { test, expect } from "@playwright/test";

test.describe("Merchant PWA smoke", () => {
  test("home shows partner hub", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Partner hub" })).toBeVisible();
  });

  test("login page renders auth form", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: "Partner sign in" })).toBeVisible();
    await expect(page.getByLabel("Tenant ID")).toBeVisible();
    await expect(page.getByLabel("Email")).toBeVisible();
  });

  test("stores page heading", async ({ page }) => {
    await page.goto("/businesses");
    await expect(page.getByRole("heading", { name: "My stores" })).toBeVisible();
  });
});

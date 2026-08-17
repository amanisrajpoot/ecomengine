import { test, expect } from "@playwright/test";

test.describe("Rider PWA smoke", () => {
  test("home shows delivery partner", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Delivery partner" })).toBeVisible();
  });

  test("login page renders auth form", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: "Rider sign in" })).toBeVisible();
    await expect(page.getByLabel("Email")).toBeVisible();
  });

  test("jobs page heading", async ({ page }) => {
    await page.goto("/jobs");
    await expect(page.getByRole("heading", { name: "Active jobs" })).toBeVisible();
  });
});

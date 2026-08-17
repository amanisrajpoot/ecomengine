import { test, expect } from "@playwright/test";

test.describe("Admin web + live API", () => {
  test("super admin signs in and reaches live API meta", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill("admin@example.com");
    await page.getByLabel("Password").fill("ChangeMe123!");
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(page.getByRole("heading", { name: "Orders" })).toBeVisible({ timeout: 20_000 });

    await page.goto("/settings");
    await page.getByRole("button", { name: "Check API" }).click();
    await expect(page.getByText(/API commerce-engine v/)).toBeVisible({ timeout: 10_000 });
  });
});

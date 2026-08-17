import { test, expect } from "@playwright/test";

import { seedActiveFoodStore } from "../helpers/api";

test.describe("Customer PWA + live API", () => {
  test("registers and sees seeded store on explore", async ({ page, request }) => {
    const slug = `cust-${Date.now()}`;
    const { tenantId, businessName } = await seedActiveFoodStore(request, slug);
    const email = `user-${slug}@example.com`;

    await page.goto("/register");
    await page.getByLabel("Tenant ID").fill(tenantId);
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill("CustomerPass123!");
    await page.getByRole("button", { name: "Register" }).click();

    await expect(page.getByRole("heading", { name: "Explore" })).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(businessName)).toBeVisible({ timeout: 20_000 });
  });
});

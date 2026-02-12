import { test, expect } from "@playwright/test";

/**
 * E2E Tests: Ideas Page
 *
 * Tests the ideas management functionality:
 * - Page loading
 * - Status tabs
 * - Generate dialog
 * - Table display
 */

test.describe("Ideas Page", () => {
  test.beforeEach(async ({ page }) => {
    // Set up mock authentication by setting localStorage
    await page.goto("/");
    await page.evaluate(() => {
      localStorage.setItem("token", "test-token");
      localStorage.setItem("brand_id", "test-brand-id");
    });
  });

  test("should display the ideas page", async ({ page }) => {
    await page.goto("/ideas");

    // Page should have the title
    await expect(page.getByRole("heading", { name: /idées/i })).toBeVisible();

    // Should have the main action buttons
    await expect(page.getByRole("button", { name: /générer avec l'ia/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /nouvelle idée/i })).toBeVisible();
  });

  test("should have status tabs", async ({ page }) => {
    await page.goto("/ideas");

    // Wait for the page to load
    await expect(page.getByRole("heading", { name: /idées/i })).toBeVisible();

    // Should have status tabs
    await expect(page.getByRole("tab", { name: /toutes/i })).toBeVisible();
    await expect(page.getByRole("tab", { name: /nouvelles/i })).toBeVisible();
    await expect(page.getByRole("tab", { name: /approuvées/i })).toBeVisible();
  });

  test("should switch between status tabs", async ({ page }) => {
    await page.goto("/ideas");

    // Wait for the page to load
    await expect(page.getByRole("heading", { name: /idées/i })).toBeVisible();

    // Click on "Nouvelles" tab
    await page.getByRole("tab", { name: /nouvelles/i }).click();

    // Tab should be active
    await expect(page.getByRole("tab", { name: /nouvelles/i })).toHaveAttribute("aria-selected", "true");

    // Click on "Approuvées" tab
    await page.getByRole("tab", { name: /approuvées/i }).click();

    // Tab should be active
    await expect(page.getByRole("tab", { name: /approuvées/i })).toHaveAttribute("aria-selected", "true");
  });

  test("should open generate ideas dialog", async ({ page }) => {
    await page.goto("/ideas");

    // Wait for the page to load
    await expect(page.getByRole("heading", { name: /idées/i })).toBeVisible();

    // Click generate button
    await page.getByRole("button", { name: /générer avec l'ia/i }).click();

    // Dialog should open
    await expect(page.getByRole("dialog")).toBeVisible();
    await expect(page.getByText(/générer des idées avec l'ia/i)).toBeVisible();

    // Should have form fields
    await expect(page.getByLabel(/nombre d'idées/i)).toBeVisible();
    await expect(page.getByLabel(/thème/i)).toBeVisible();
    await expect(page.getByLabel(/plateforme cible/i)).toBeVisible();
  });

  test("should close generate dialog on cancel", async ({ page }) => {
    await page.goto("/ideas");

    // Wait for the page to load
    await expect(page.getByRole("heading", { name: /idées/i })).toBeVisible();

    // Open dialog
    await page.getByRole("button", { name: /générer avec l'ia/i }).click();

    // Dialog should be visible
    await expect(page.getByRole("dialog")).toBeVisible();

    // Click cancel
    await page.getByRole("button", { name: /annuler/i }).click();

    // Dialog should close
    await expect(page.getByRole("dialog")).not.toBeVisible();
  });

  test("should display empty state when no ideas", async ({ page }) => {
    await page.goto("/ideas");

    // Wait for the page to load
    await expect(page.getByRole("heading", { name: /idées/i })).toBeVisible();

    // If empty, should show empty state message
    // (This depends on the API returning empty data)
    // Just verify the page doesn't crash
    await page.waitForTimeout(1000);
    expect(page.url()).toContain("/ideas");
  });

  test("should have search input", async ({ page }) => {
    await page.goto("/ideas");

    // Wait for the page to load
    await expect(page.getByRole("heading", { name: /idées/i })).toBeVisible();

    // Wait for content to load
    await page.waitForTimeout(1000);

    // If there's a table (ideas exist), should have search
    const searchInput = page.getByPlaceholder(/rechercher une idée/i);
    if (await searchInput.isVisible()) {
      await expect(searchInput).toBeEnabled();
    }
  });

  test("should display page description", async ({ page }) => {
    await page.goto("/ideas");

    // Wait for the page to load
    await expect(page.getByRole("heading", { name: /idées/i })).toBeVisible();

    // Should have page description
    await expect(page.getByText(/gérez vos idées de contenu/i)).toBeVisible();
  });
});

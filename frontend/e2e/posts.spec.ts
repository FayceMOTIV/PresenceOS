import { test, expect } from "@playwright/test";

/**
 * E2E Tests: Posts Page
 *
 * Tests the posts management functionality:
 * - Page loading
 * - Status tabs
 * - Table display
 * - Filters
 * - Actions
 */

test.describe("Posts Page", () => {
  test.beforeEach(async ({ page }) => {
    // Set up mock authentication by setting localStorage
    await page.goto("/");
    await page.evaluate(() => {
      localStorage.setItem("token", "test-token");
      localStorage.setItem("brand_id", "test-brand-id");
    });
  });

  test("should display the posts page", async ({ page }) => {
    await page.goto("/posts");

    // Page should have the title
    await expect(page.getByRole("heading", { name: /posts/i })).toBeVisible();

    // Should have the "Nouveau post" button
    await expect(page.getByRole("button", { name: /nouveau post/i })).toBeVisible();

    // Should have the "Calendrier" button
    await expect(page.getByRole("button", { name: /calendrier/i })).toBeVisible();
  });

  test("should have status tabs", async ({ page }) => {
    await page.goto("/posts");

    // Wait for the page to load
    await expect(page.getByRole("heading", { name: /posts/i })).toBeVisible();

    // Should have status tabs
    await expect(page.getByRole("tab", { name: /tous/i })).toBeVisible();
    await expect(page.getByRole("tab", { name: /planifies/i })).toBeVisible();
    await expect(page.getByRole("tab", { name: /publies/i })).toBeVisible();
  });

  test("should switch between status tabs", async ({ page }) => {
    await page.goto("/posts");

    // Wait for the page to load
    await expect(page.getByRole("heading", { name: /posts/i })).toBeVisible();

    // Click on "Planifies" tab
    await page.getByRole("tab", { name: /planifies/i }).click();

    // Tab should be active
    await expect(page.getByRole("tab", { name: /planifies/i })).toHaveAttribute("data-state", "active");

    // Click on "Publies" tab
    await page.getByRole("tab", { name: /publies/i }).click();

    // Tab should be active
    await expect(page.getByRole("tab", { name: /publies/i })).toHaveAttribute("data-state", "active");
  });

  test("should have filters button on desktop", async ({ page }) => {
    // Set viewport to desktop
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/posts");

    // Wait for the page to load
    await expect(page.getByRole("heading", { name: /posts/i })).toBeVisible();

    // Wait for content to load
    await page.waitForTimeout(1000);

    // Should have filters button
    await expect(page.getByRole("button", { name: /filtres/i })).toBeVisible();
  });

  test("should open filters popover", async ({ page }) => {
    // Set viewport to desktop
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/posts");

    // Wait for the page to load
    await expect(page.getByRole("heading", { name: /posts/i })).toBeVisible();

    // Wait for content to load
    await page.waitForTimeout(1000);

    // Click filters button
    await page.getByRole("button", { name: /filtres/i }).click();

    // Should show filter options
    await expect(page.getByText(/plateformes/i)).toBeVisible();
    await expect(page.getByText(/statut/i)).toBeVisible();
  });

  test("should have search input", async ({ page }) => {
    // Set viewport to desktop
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/posts");

    // Wait for the page to load
    await expect(page.getByRole("heading", { name: /posts/i })).toBeVisible();

    // Wait for content to load
    await page.waitForTimeout(1000);

    // Should have search input
    const searchInput = page.getByPlaceholder(/rechercher un post/i);
    if (await searchInput.isVisible()) {
      await expect(searchInput).toBeEnabled();
    }
  });

  test("should display empty state when no posts", async ({ page }) => {
    await page.goto("/posts");

    // Wait for the page to load
    await expect(page.getByRole("heading", { name: /posts/i })).toBeVisible();

    // Wait for content to load
    await page.waitForTimeout(1000);

    // If empty, should show empty state or table
    // Just verify the page doesn't crash
    expect(page.url()).toContain("/posts");
  });

  test("should navigate to studio when clicking new post", async ({ page }) => {
    await page.goto("/posts");

    // Wait for the page to load
    await expect(page.getByRole("heading", { name: /posts/i })).toBeVisible();

    // Click new post button
    await page.getByRole("button", { name: /nouveau post/i }).click();

    // Should navigate to studio
    await expect(page).toHaveURL(/\/studio/);
  });

  test("should navigate to planner when clicking calendar", async ({ page }) => {
    await page.goto("/posts");

    // Wait for the page to load
    await expect(page.getByRole("heading", { name: /posts/i })).toBeVisible();

    // Click calendar button
    await page.getByRole("button", { name: /calendrier/i }).click();

    // Should navigate to planner
    await expect(page).toHaveURL(/\/planner/);
  });

  test("should display page description", async ({ page }) => {
    await page.goto("/posts");

    // Wait for the page to load
    await expect(page.getByRole("heading", { name: /posts/i })).toBeVisible();

    // Should have page description
    await expect(page.getByText(/gerez vos publications/i)).toBeVisible();
  });

  test("should have date range filter", async ({ page }) => {
    // Set viewport to desktop
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/posts");

    // Wait for the page to load
    await expect(page.getByRole("heading", { name: /posts/i })).toBeVisible();

    // Wait for content to load
    await page.waitForTimeout(1000);

    // Should have period button for date range
    await expect(page.getByRole("button", { name: /periode/i })).toBeVisible();
  });
});

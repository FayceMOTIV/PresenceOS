import { test, expect } from "@playwright/test";

/**
 * E2E Test: Complete Onboarding Flow
 *
 * Tests the full user journey from registration to dashboard:
 * 1. Register with unique email
 * 2. Complete 4-step onboarding wizard
 * 3. Arrive on dashboard with brand visible
 */

test.describe("Onboarding Flow", () => {
  // Generate unique identifiers for each test run
  const timestamp = Date.now();
  const uniqueEmail = `test-${timestamp}@example.com`;
  const password = "TestPassword123!";
  const fullName = "Test User E2E";
  const workspaceName = `E2E Workspace ${timestamp}`;
  const brandName = `E2E Brand ${timestamp}`;

  test("complete onboarding from registration to dashboard", async ({ page }) => {
    // ===== STEP 0: Register =====
    await test.step("Register new account", async () => {
      await page.goto("/auth/register");

      // Wait for the form to be visible
      await expect(page.locator('input[name="full_name"]')).toBeVisible();

      // Fill registration form
      await page.locator('input[name="full_name"]').fill(fullName);
      await page.locator('input[name="email"]').fill(uniqueEmail);
      await page.locator('input[name="password"]').fill(password);
      await page.locator('input[name="workspace_name"]').fill(workspaceName);

      // Submit registration
      await page.getByRole("button", { name: /créer mon compte/i }).click();

      // Wait for redirect to onboarding
      await expect(page).toHaveURL("/onboarding", { timeout: 15000 });
    });

    // ===== STEP 1: Brand Info =====
    await test.step("Step 1: Fill brand information", async () => {
      // Wait for Step 1 to load
      await expect(page.getByText("Parlons de votre marque")).toBeVisible({ timeout: 10000 });

      // Fill brand name
      await page.locator('input#name').fill(brandName);

      // Wait for slug to be auto-generated
      await page.waitForTimeout(500);

      // Select brand type (restaurant)
      await page.getByRole("combobox").click();
      await page.getByRole("option", { name: /restaurant/i }).click();

      // Fill description
      await page.locator("textarea#description").fill("Un restaurant de test pour les tests E2E");

      // Click Next
      await page.getByRole("button", { name: /continuer/i }).click();

      // Wait for Step 2 (text without accent in source code)
      await expect(page.getByText("Ton & Personnalite")).toBeVisible({ timeout: 10000 });
    });

    // ===== STEP 2: Brand Voice =====
    await test.step("Step 2: Configure brand voice", async () => {
      // Add a word to avoid using the input field
      const avoidInput = page.locator('input[placeholder*="prix bas"]');
      await expect(avoidInput).toBeVisible({ timeout: 5000 });
      await avoidInput.fill("cheap");

      // Click the first "Ajouter" button (for words to avoid)
      await page.getByRole("button", { name: "Ajouter" }).first().click();

      // Verify the word was added (should appear as a badge)
      await expect(page.getByText("cheap")).toBeVisible({ timeout: 5000 });

      // Click Next (Continuer button)
      await page.getByRole("button", { name: /continuer/i }).click();

      // Wait for Step 3
      await expect(page.getByText("Vos audiences")).toBeVisible({ timeout: 10000 });
    });

    // ===== STEP 3: Audiences =====
    await test.step("Step 3: Define target audience", async () => {
      // Fill persona name
      await page.locator('input#persona_name').fill("Familles urbaines");

      // Select age range
      await page.getByRole("combobox").click();
      await page.getByRole("option", { name: /25-34/i }).click();

      // Click Next
      await page.getByRole("button", { name: /continuer/i }).click();

      // Wait for Step 4 (text without accent)
      await expect(page.getByText("Connectez vos reseaux")).toBeVisible({ timeout: 10000 });
    });

    // ===== STEP 4: Platforms (Skip) =====
    await test.step("Step 4: Skip platform connections", async () => {
      // Look for the skip/finish button
      const skipButton = page.getByRole("button", { name: /passer|terminer/i });
      await expect(skipButton).toBeVisible();
      await skipButton.click();

      // Wait for redirect to dashboard
      await expect(page).toHaveURL("/dashboard", { timeout: 15000 });
    });

    // ===== VERIFICATION: Dashboard =====
    await test.step("Verify brand appears on dashboard", async () => {
      // Wait for dashboard to fully load (use heading specifically)
      await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible({ timeout: 10000 });

      // Verify the brand name appears in the sidebar brand selector
      await expect(page.getByText(brandName)).toBeVisible({ timeout: 10000 });
    });
  });

  test("redirect to dashboard if already onboarded", async ({ page }) => {
    // This test verifies the guard that redirects users who already have a brand

    // First, we need to complete onboarding (simplified version)
    const ts = Date.now();
    const email2 = `test-guard-${ts}@example.com`;
    const brandName2 = `Guard Brand ${ts}`;
    const workspaceName2 = `Guard Workspace ${ts}`;

    await page.goto("/auth/register");
    await page.locator('input[name="full_name"]').fill("Guard Test");
    await page.locator('input[name="email"]').fill(email2);
    await page.locator('input[name="password"]').fill(password);
    await page.locator('input[name="workspace_name"]').fill(workspaceName2);
    await page.getByRole("button", { name: /créer mon compte/i }).click();

    await expect(page).toHaveURL("/onboarding", { timeout: 15000 });

    // Complete onboarding quickly
    await page.locator('input#name').fill(brandName2);
    await page.waitForTimeout(500);
    await page.getByRole("combobox").click();
    await page.getByRole("option", { name: /autre/i }).click();
    await page.getByRole("button", { name: /continuer/i }).click();

    await expect(page.getByText("Ton & Personnalite")).toBeVisible({ timeout: 10000 });
    await page.getByRole("button", { name: /continuer/i }).click();

    await expect(page.getByText("Vos audiences")).toBeVisible({ timeout: 10000 });
    await page.getByRole("button", { name: /continuer/i }).click();

    await expect(page.getByText("Connectez vos reseaux")).toBeVisible({ timeout: 10000 });
    await page.getByRole("button", { name: /passer|terminer/i }).click();

    await expect(page).toHaveURL("/dashboard", { timeout: 15000 });

    // Now try to access onboarding again - should redirect to dashboard
    await page.goto("/onboarding");
    await expect(page).toHaveURL("/dashboard", { timeout: 15000 });
  });
});

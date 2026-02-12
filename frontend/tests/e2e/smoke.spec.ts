import { test, expect } from "@playwright/test";

test.describe("PresenceOS Smoke Tests", () => {
  test("landing page loads and shows PresenceOS", async ({ page }) => {
    await page.goto("/");

    // Check that the page title/brand name is visible
    await expect(page.getByText("PresenceOS").first()).toBeVisible();

    // Check that the main heading is visible
    await expect(page.getByRole("heading", { name: /Votre présence digitale/i })).toBeVisible();

    // Check that the hero section loads
    await expect(page.getByText(/automatisée par l'IA/i)).toBeVisible();
  });

  test("navigation links exist on the landing page", async ({ page }) => {
    await page.goto("/");

    // Check that login link exists
    const loginLink = page.getByRole("link", { name: /Connexion/i });
    await expect(loginLink).toBeVisible();
    await expect(loginLink).toHaveAttribute("href", "/auth/login");

    // Check that register/signup links exist
    const registerLinks = page.getByRole("link", { name: /Commencer/i });
    await expect(registerLinks.first()).toBeVisible();

    // Check features navigation link
    await expect(page.getByRole("link", { name: /Fonctionnalités/i })).toBeVisible();

    // Check pricing navigation link
    await expect(page.getByRole("link", { name: /Tarifs/i })).toBeVisible();
  });

  test("login page renders with form fields", async ({ page }) => {
    await page.goto("/auth/login");

    // Check page title
    await expect(page.getByRole("heading", { name: /Bon retour/i })).toBeVisible();

    // Check email input field
    const emailInput = page.getByLabel(/Email/i);
    await expect(emailInput).toBeVisible();
    await expect(emailInput).toHaveAttribute("type", "email");

    // Check password input field
    const passwordInput = page.getByLabel(/Mot de passe/i);
    await expect(passwordInput).toBeVisible();
    await expect(passwordInput).toHaveAttribute("type", "password");

    // Check submit button
    await expect(page.getByRole("button", { name: /Se connecter/i })).toBeVisible();

    // Check link to register page
    await expect(page.getByRole("link", { name: /Créer un compte/i })).toBeVisible();

    // Check forgot password link
    await expect(page.getByRole("link", { name: /Mot de passe oublie/i })).toBeVisible();
  });

  test("register page renders with form fields", async ({ page }) => {
    await page.goto("/auth/register");

    // Check page title
    await expect(page.getByRole("heading", { name: /Créer un compte/i })).toBeVisible();

    // Check full name input field
    const nameInput = page.getByLabel(/Nom complet/i);
    await expect(nameInput).toBeVisible();
    await expect(nameInput).toHaveAttribute("type", "text");

    // Check email input field
    const emailInput = page.getByLabel(/Email/i);
    await expect(emailInput).toBeVisible();
    await expect(emailInput).toHaveAttribute("type", "email");

    // Check password input field
    const passwordInput = page.getByLabel(/Mot de passe/i);
    await expect(passwordInput).toBeVisible();
    await expect(passwordInput).toHaveAttribute("type", "password");

    // Check workspace name input field
    const workspaceInput = page.getByLabel(/Nom de votre entreprise/i);
    await expect(workspaceInput).toBeVisible();

    // Check submit button
    await expect(page.getByRole("button", { name: /Créer mon compte/i })).toBeVisible();

    // Check link to login page
    await expect(page.getByRole("link", { name: /Se connecter/i })).toBeVisible();
  });

  test("dashboard redirects to login when unauthenticated", async ({ page }) => {
    // Clear any existing auth tokens
    await page.context().clearCookies();
    await page.goto("/");
    await page.evaluate(() => localStorage.clear());

    // Try to access dashboard
    await page.goto("/dashboard");

    // Should either redirect to login or show login page
    // Wait for navigation to complete
    await page.waitForLoadState("networkidle");

    // Check if we're on the login page or auth is required
    const currentUrl = page.url();
    const isOnLoginPage = currentUrl.includes("/auth/login") || currentUrl.includes("/login");
    const hasLoginForm = await page.getByRole("heading", { name: /Bon retour/i }).isVisible().catch(() => false);

    // Either we should be redirected to login page, or see a login form
    expect(isOnLoginPage || hasLoginForm).toBeTruthy();
  });
});

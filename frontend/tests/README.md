# PresenceOS E2E Tests

This directory contains end-to-end tests for the PresenceOS frontend using Playwright.

## Running Tests

Make sure you have installed dependencies:
```bash
npm install
```

### Run all tests (headless)
```bash
npm run test:e2e
```

### Run tests in UI mode (interactive)
```bash
npm run test:e2e:ui
```

### Run tests in headed mode (see browser)
```bash
npm run test:e2e:headed
```

## Test Structure

- `tests/e2e/smoke.spec.ts` - Smoke tests that verify basic functionality

## Smoke Tests

The smoke test suite verifies:
1. Landing page loads and displays "PresenceOS"
2. Navigation links exist on the landing page
3. Login page renders with all required form fields
4. Register page renders with all required form fields
5. Dashboard redirects to login when user is unauthenticated

## Configuration

Tests are configured in `playwright.config.ts`:
- Base URL: `http://localhost:3001`
- Timeout: 30 seconds per test
- Web server automatically starts Next.js dev server on port 3001
- Tests run in Chromium by default

## Notes

- Tests automatically start the dev server if it's not already running
- Screenshots and videos are captured on test failures
- Tests use the app's baseURL, so all navigation is relative (e.g., `page.goto("/")`)

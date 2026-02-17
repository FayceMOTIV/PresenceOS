// Sentry Server Configuration for PresenceOS
// To enable Sentry monitoring:
// 1. npm install @sentry/nextjs
// 2. Set NEXT_PUBLIC_SENTRY_DSN in .env.local

// @ts-nocheck
/* eslint-disable */

if (process.env.NEXT_PUBLIC_SENTRY_DSN) {
  try {
    const Sentry = require("@sentry/nextjs");
    Sentry.init({
      dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
      tracesSampleRate: process.env.NODE_ENV === "production" ? 0.1 : 1.0,
      debug: false,
      environment: process.env.NODE_ENV,
    });
  } catch {
    // @sentry/nextjs not installed — Sentry disabled
  }
}

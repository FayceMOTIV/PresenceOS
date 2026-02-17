// Sentry Client Configuration for PresenceOS
// To enable Sentry monitoring:
// 1. npm install @sentry/nextjs
// 2. Set NEXT_PUBLIC_SENTRY_DSN in .env.local
// 3. Uncomment the code below

// @ts-nocheck
/* eslint-disable */

if (process.env.NEXT_PUBLIC_SENTRY_DSN) {
  try {
    const Sentry = require("@sentry/nextjs");
    Sentry.init({
      dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
      tracesSampleRate: process.env.NODE_ENV === "production" ? 0.1 : 1.0,
      debug: false,
      replaysOnErrorSampleRate: 1.0,
      replaysSessionSampleRate: 0.1,
      environment: process.env.NODE_ENV,
      ignoreErrors: [
        "ResizeObserver loop limit exceeded",
        "Non-Error promise rejection captured",
        "Load failed",
        "Failed to fetch",
      ],
      beforeSend(event: any) {
        if (typeof window !== "undefined") {
          const userId = localStorage.getItem("user_id");
          if (userId) {
            event.user = { id: userId };
          }
        }
        return event;
      },
    });
  } catch {
    // @sentry/nextjs not installed — Sentry disabled
  }
}

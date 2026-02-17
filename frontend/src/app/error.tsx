'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log to Sentry if available
    try {
      const Sentry = require('@sentry/nextjs');
      Sentry.captureException(error);
    } catch {
      // Sentry not installed, just log
      console.error('Application error:', error);
    }
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50/80 via-white to-violet-50/30">
      <div className="text-center max-w-md mx-auto px-4">
        <div className="text-6xl mb-6">😵</div>
        <h2 className="text-2xl font-bold text-gray-900 mb-3">Oups, une erreur est survenue</h2>
        <p className="text-gray-500 mb-6">
          Nos équipes ont été notifiées et travaillent sur le problème. Veuillez réessayer.
        </p>
        <Button variant="gradient" onClick={reset}>
          Réessayer
        </Button>
      </div>
    </div>
  );
}

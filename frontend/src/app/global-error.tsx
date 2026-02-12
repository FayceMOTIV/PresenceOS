"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Global error:", error);
  }, [error]);

  return (
    <html>
      <body className="bg-zinc-950 text-zinc-100">
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center space-y-6 px-4">
            <div className="mx-auto w-20 h-20 rounded-full bg-red-900/20 flex items-center justify-center">
              <svg
                className="w-10 h-10 text-red-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"
                />
              </svg>
            </div>
            <div className="space-y-2">
              <h2 className="text-2xl font-semibold">
                Erreur critique
              </h2>
              <p className="text-zinc-400 max-w-md mx-auto">
                {"L'application a rencontre une erreur inattendue. Veuillez reessayer."}
              </p>
            </div>
            <button
              onClick={reset}
              className="px-6 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 rounded-lg border border-zinc-700 transition-colors"
            >
              Reessayer
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}

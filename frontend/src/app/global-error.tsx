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
      <body className="bg-gradient-to-br from-gray-50 via-white to-violet-50/30 text-gray-900">
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center space-y-6 px-4">
            <div className="mx-auto w-20 h-20 rounded-2xl bg-red-50 flex items-center justify-center shadow-lg shadow-red-500/10">
              <svg
                className="w-10 h-10 text-red-500"
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
              <h2 className="text-2xl font-bold text-gray-900">
                Erreur critique
              </h2>
              <p className="text-gray-500 max-w-md mx-auto">
                {"L'application a rencontré une erreur inattendue. Veuillez réessayer."}
              </p>
            </div>
            <button
              onClick={reset}
              className="px-6 py-3 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white rounded-xl shadow-lg shadow-purple-500/25 transition-all hover:shadow-xl hover:-translate-y-0.5 font-medium"
            >
              Réessayer
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}

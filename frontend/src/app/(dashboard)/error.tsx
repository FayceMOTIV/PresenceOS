"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { AlertTriangle, RefreshCw } from "lucide-react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Page error:", error);
  }, [error]);

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center space-y-6 px-4">
        <div className="mx-auto w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center">
          <AlertTriangle className="w-8 h-8 text-destructive" />
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-semibold text-foreground">
            Une erreur est survenue
          </h2>
          <p className="text-muted-foreground max-w-md mx-auto">
            {error.message || "Quelque chose s'est mal passé. Veuillez réessayer."}
          </p>
        </div>
        <Button onClick={reset} variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Réessayer
        </Button>
      </div>
    </div>
  );
}

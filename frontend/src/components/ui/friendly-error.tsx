"use client";

import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface FriendlyErrorProps {
  message: string;
  onRetry?: () => void;
}

export function FriendlyError({ message, onRetry }: FriendlyErrorProps) {
  return (
    <div className="rounded-xl border border-red-200 bg-red-50 p-4">
      <p className="text-sm font-medium text-red-800">{message}</p>
      {onRetry && (
        <Button
          onClick={onRetry}
          variant="outline"
          size="sm"
          className="mt-3 border-red-300 text-red-700 hover:bg-red-100"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Réessayer
        </Button>
      )}
    </div>
  );
}

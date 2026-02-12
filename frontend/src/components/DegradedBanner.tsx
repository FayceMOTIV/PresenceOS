"use client";

import { useState } from "react";
import { X } from "lucide-react";

export function DegradedBanner({ degraded }: { degraded: boolean }) {
  const [dismissed, setDismissed] = useState(false);

  if (!degraded || dismissed) return null;

  return (
    <div className="bg-amber-900/30 border border-amber-700/50 text-amber-200 px-4 py-2 text-sm text-center rounded-lg mx-4 mt-2 flex items-center justify-center gap-2 relative">
      <span>
        Mode limite — La base de donnees est indisponible. Le chat et
        l&apos;upload fonctionnent normalement.
      </span>
      <button
        onClick={() => setDismissed(true)}
        className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-amber-800/50 rounded"
      >
        <X className="w-3 h-3" />
      </button>
    </div>
  );
}

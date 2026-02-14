"use client";

import { useState } from "react";
import { X } from "lucide-react";

export function DegradedBanner({ degraded }: { degraded: boolean }) {
  const [dismissed, setDismissed] = useState(false);

  if (!degraded || dismissed) return null;

  return (
    <div className="bg-amber-50 border border-amber-200 text-amber-800 px-4 py-2 text-sm text-center rounded-lg mx-4 mt-2 flex items-center justify-center gap-2 relative">
      <span>
        Certaines fonctions ne marchent pas en ce moment, mais vous pouvez
        toujours créer et publier vos posts.
      </span>
      <button
        onClick={() => setDismissed(true)}
        className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-amber-100 rounded"
      >
        <X className="w-3 h-3" />
      </button>
    </div>
  );
}

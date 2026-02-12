import { Loader2 } from 'lucide-react';

export default function SettingsLoading() {
  return (
    <div className="space-y-6 p-6">
      <div className="h-8 w-32 animate-pulse rounded bg-zinc-800" />
      <div className="space-y-4">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="space-y-2">
            <div className="h-4 w-24 animate-pulse rounded bg-zinc-800" />
            <div className="h-10 animate-pulse rounded bg-zinc-800" />
          </div>
        ))}
      </div>
      <div className="h-10 w-32 animate-pulse rounded bg-zinc-800" />
    </div>
  );
}

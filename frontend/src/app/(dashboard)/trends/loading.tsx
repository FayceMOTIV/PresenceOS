import { Loader2 } from 'lucide-react';

export default function TrendsLoading() {
  return (
    <div className="space-y-6 p-6">
      <div className="h-8 w-32 animate-pulse rounded bg-zinc-800" />
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[...Array(9)].map((_, i) => (
          <div key={i} className="h-40 animate-pulse rounded-lg bg-zinc-800" />
        ))}
      </div>
    </div>
  );
}

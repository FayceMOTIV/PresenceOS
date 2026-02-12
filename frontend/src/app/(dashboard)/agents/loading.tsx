import { Loader2 } from 'lucide-react';

export default function AgentsLoading() {
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="h-8 w-32 animate-pulse rounded bg-zinc-800" />
        <div className="h-10 w-32 animate-pulse rounded bg-zinc-800" />
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="h-48 animate-pulse rounded-lg bg-zinc-800" />
        ))}
      </div>
    </div>
  );
}

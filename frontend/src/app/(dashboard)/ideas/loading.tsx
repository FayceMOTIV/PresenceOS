import { Loader2 } from 'lucide-react';

export default function IdeasLoading() {
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="h-8 w-32 animate-pulse rounded bg-zinc-800" />
        <div className="h-10 w-32 animate-pulse rounded bg-zinc-800" />
      </div>
      <div className="space-y-3">
        {[...Array(10)].map((_, i) => (
          <div key={i} className="h-24 animate-pulse rounded-lg bg-zinc-800" />
        ))}
      </div>
    </div>
  );
}

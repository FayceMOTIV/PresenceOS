import { Loader2 } from 'lucide-react';

export default function MediaLibraryLoading() {
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="h-8 w-32 animate-pulse rounded bg-zinc-800" />
        <div className="h-10 w-32 animate-pulse rounded bg-zinc-800" />
      </div>
      <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
        {[...Array(12)].map((_, i) => (
          <div key={i} className="aspect-square animate-pulse rounded-lg bg-zinc-800" />
        ))}
      </div>
    </div>
  );
}

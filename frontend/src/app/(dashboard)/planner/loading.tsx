import { Loader2 } from 'lucide-react';

export default function PlannerLoading() {
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="h-8 w-48 animate-pulse rounded bg-zinc-800" />
        <div className="flex gap-2">
          <div className="h-10 w-24 animate-pulse rounded bg-zinc-800" />
          <div className="h-10 w-24 animate-pulse rounded bg-zinc-800" />
        </div>
      </div>
      <div className="h-[600px] animate-pulse rounded-lg bg-zinc-800" />
    </div>
  );
}

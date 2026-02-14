import { Skeleton } from '@/components/ui/skeleton';

export function SkeletonIdea() {
  return (
    <div className="border rounded-xl p-6 space-y-3">
      <div className="flex items-center gap-2">
        <Skeleton className="h-6 w-6 rounded" />
        <Skeleton className="h-5 w-32" />
      </div>
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-4/5" />
      <div className="flex gap-2 pt-2">
        <Skeleton className="h-8 w-24 rounded-lg" />
        <Skeleton className="h-8 w-24 rounded-lg" />
      </div>
    </div>
  );
}

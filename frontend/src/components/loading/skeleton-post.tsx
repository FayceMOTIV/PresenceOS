import { Skeleton } from '@/components/ui/skeleton';

export function SkeletonPost() {
  return (
    <div className="border rounded-xl p-6 space-y-4">
      <Skeleton className="h-64 w-full rounded-lg" />
      <div className="space-y-2">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
        <Skeleton className="h-4 w-4/6" />
      </div>
      <div className="flex items-center gap-4">
        <Skeleton className="h-10 w-10 rounded-full" />
        <div className="space-y-2 flex-1">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-3 w-32" />
        </div>
      </div>
    </div>
  );
}

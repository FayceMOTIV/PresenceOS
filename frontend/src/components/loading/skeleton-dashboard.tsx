import { Skeleton } from '@/components/ui/skeleton';

export function SkeletonDashboard() {
  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {Array(4).fill(0).map((_, i) => (
          <div key={i} className="border rounded-xl p-6 space-y-2">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-8 w-16" />
            <Skeleton className="h-3 w-24" />
          </div>
        ))}
      </div>
      <div className="border rounded-xl p-6">
        <Skeleton className="h-64 w-full" />
      </div>
      <div className="space-y-4">
        <Skeleton className="h-6 w-32" />
        <div className="grid gap-4">
          {Array(3).fill(0).map((_, i) => (
            <div key={i} className="border rounded-xl p-4 flex gap-4">
              <Skeleton className="h-20 w-20 rounded" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-2/3" />
                <Skeleton className="h-3 w-24" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

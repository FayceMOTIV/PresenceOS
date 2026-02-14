import { Loader2 } from 'lucide-react';

export default function PlannerLoading() {
  return (
    <div className="space-y-6 p-6 bg-gray-50/50 min-h-screen">
      <div className="flex items-center justify-between">
        <div className="h-8 w-48 animate-pulse rounded-xl bg-gray-200/60 shadow-sm" />
        <div className="flex gap-2">
          <div className="h-10 w-24 animate-pulse rounded-xl bg-gray-200/60 shadow-sm" />
          <div className="h-10 w-24 animate-pulse rounded-xl bg-gray-200/60 shadow-sm" />
        </div>
      </div>
      <div className="h-[600px] animate-pulse rounded-2xl bg-gray-200/60 shadow-sm" />
    </div>
  );
}

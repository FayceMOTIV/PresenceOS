import { Loader2 } from 'lucide-react';

export default function IdeasLoading() {
  return (
    <div className="space-y-6 p-6 bg-gray-50/50 min-h-screen">
      <div className="flex items-center justify-between">
        <div className="h-8 w-32 animate-pulse rounded-xl bg-gray-200/60 shadow-sm" />
        <div className="h-10 w-32 animate-pulse rounded-xl bg-gray-200/60 shadow-sm" />
      </div>
      <div className="space-y-3">
        {[...Array(10)].map((_, i) => (
          <div key={i} className="h-24 animate-pulse rounded-2xl bg-gray-200/60 shadow-sm" />
        ))}
      </div>
    </div>
  );
}

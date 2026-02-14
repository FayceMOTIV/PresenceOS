import { Loader2 } from 'lucide-react';

export default function SettingsLoading() {
  return (
    <div className="space-y-6 p-6 bg-gray-50/50 min-h-screen">
      <div className="h-8 w-32 animate-pulse rounded-xl bg-gray-200/60 shadow-sm" />
      <div className="space-y-4">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="space-y-2">
            <div className="h-4 w-24 animate-pulse rounded bg-gray-300/50" />
            <div className="h-10 animate-pulse rounded-xl bg-gray-200/60 shadow-sm" />
          </div>
        ))}
      </div>
      <div className="h-10 w-32 animate-pulse rounded-xl bg-gray-200/60 shadow-sm" />
    </div>
  );
}

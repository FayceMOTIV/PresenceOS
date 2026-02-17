import { Skeleton } from "@/components/ui/skeleton";

export default function AccountsLoading() {
  return (
    <div className="space-y-8">
      {/* ── Header skeleton ──────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="space-y-2">
          <Skeleton className="h-9 w-48 rounded-lg" />
          <Skeleton className="h-4 w-72 rounded-md" />
        </div>
        <Skeleton className="h-10 w-44 rounded-xl" />
      </div>

      {/* ── Platform sections ─────────────────────────────────────────────────── */}
      {[0, 1, 2, 3].map((i) => (
        <div
          key={i}
          className="rounded-xl border border-gray-200/60 bg-white shadow-sm overflow-hidden"
        >
          {/* Section header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
            <div className="flex items-center gap-3">
              <Skeleton className="h-9 w-9 rounded-lg" />
              <Skeleton className="h-5 w-24 rounded-md" />
            </div>
            <Skeleton className="h-5 w-12 rounded-full" />
          </div>

          {/* Card skeletons */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 p-6">
            <Skeleton className="h-24 w-full rounded-xl" />
            <Skeleton className="h-24 w-full rounded-xl" />
          </div>
        </div>
      ))}
    </div>
  );
}

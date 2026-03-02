"use client";

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Inbox,
  MessageSquare,
  Filter,
  RefreshCw,
  AlertTriangle,
  TrendingUp,
  CheckCircle,
  Clock,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { cmApi } from "@/lib/api";
import { CMInteraction, CMStats } from "@/types";
import { InteractionCard } from "@/components/cm/InteractionCard";

const PAGE_SIZE = 20;

const PLATFORM_FILTERS = [
  { value: "", label: "Toutes" },
  { value: "google", label: "Google" },
  { value: "instagram", label: "Instagram" },
  { value: "facebook", label: "Facebook" },
];

const STATUS_FILTERS = [
  { value: "", label: "Tous" },
  { value: "pending", label: "En attente" },
  { value: "approved", label: "Approuves" },
  { value: "auto_published", label: "Auto-publies" },
  { value: "rejected", label: "Rejetes" },
];

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.05 } },
};

function InboxSkeleton() {
  return (
    <div className="space-y-4">
      {[...Array(5)].map((_, i) => (
        <Card key={i}>
          <CardContent className="p-4 space-y-3">
            <div className="flex items-center gap-3">
              <Skeleton className="w-8 h-8 rounded-lg" />
              <div className="space-y-1.5 flex-1">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-20" />
              </div>
              <Skeleton className="h-5 w-16 rounded-full" />
            </div>
            <Skeleton className="h-16 w-full rounded-lg" />
            <Skeleton className="h-12 w-full rounded-lg" />
            <div className="flex gap-2">
              <Skeleton className="h-7 w-20" />
              <Skeleton className="h-7 w-20" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default function InboxPage() {
  const [interactions, setInteractions] = useState<CMInteraction[]>([]);
  const [stats, setStats] = useState<CMStats | null>(null);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Filters
  const [platformFilter, setPlatformFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const brandId = typeof window !== "undefined" ? localStorage.getItem("brand_id") : null;

  const fetchData = useCallback(
    async (newOffset = 0, refresh = false) => {
      if (!brandId) return;
      if (refresh) setIsRefreshing(true);
      else setIsLoading(true);

      try {
        const params: Record<string, string | number> = {
          limit: PAGE_SIZE,
          offset: newOffset,
        };
        if (platformFilter) params.platform = platformFilter;
        if (statusFilter) params.response_status = statusFilter;

        const [listRes, statsRes] = await Promise.all([
          cmApi.listInteractions(brandId, params),
          cmApi.getStats(brandId, 7),
        ]);

        setInteractions(listRes.data.interactions);
        setTotal(listRes.data.total);
        setOffset(newOffset);
        setStats(statsRes.data);
      } catch {
        // silently fail
      } finally {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    },
    [brandId, platformFilter, statusFilter]
  );

  useEffect(() => {
    fetchData(0);
  }, [fetchData]);

  const handleUpdate = (updated: CMInteraction) => {
    setInteractions((prev) =>
      prev.map((i) => (i.id === updated.id ? updated : i))
    );
    // Refresh stats after action
    if (brandId) {
      cmApi.getStats(brandId, 7).then((res) => setStats(res.data)).catch(() => {});
    }
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  const sentimentEmoji =
    stats && stats.avg_sentiment >= 0.7
      ? "😊"
      : stats && stats.avg_sentiment >= 0.4
        ? "😐"
        : "😟";

  if (!brandId) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-center space-y-3">
          <Inbox className="w-12 h-12 text-gray-300 mx-auto" />
          <p className="text-gray-500">Selectionnez une marque pour voir votre boite de reception.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Inbox className="w-7 h-7 text-violet-600" />
            Community Manager
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Gerez les avis et commentaires de vos clients avec l&apos;IA
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          disabled={isRefreshing}
          onClick={() => fetchData(offset, true)}
          className="gap-1.5"
        >
          <RefreshCw className={cn("w-4 h-4", isRefreshing && "animate-spin")} />
          Actualiser
        </Button>
      </div>

      {/* Stats Row */}
      {stats && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-3"
        >
          <Card className="bg-gradient-to-br from-amber-50 to-orange-50 border-amber-200/60">
            <CardContent className="p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center">
                <Clock className="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-amber-700">{stats.pending_count}</p>
                <p className="text-xs text-amber-600">En attente</p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-emerald-50 to-green-50 border-emerald-200/60">
            <CardContent className="p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center">
                <CheckCircle className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-emerald-700">{stats.published_count}</p>
                <p className="text-xs text-emerald-600">Publiees</p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-violet-50 to-purple-50 border-violet-200/60">
            <CardContent className="p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-violet-100 flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-violet-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-violet-700">{stats.response_rate}%</p>
                <p className="text-xs text-violet-600">Taux reponse</p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200/60">
            <CardContent className="p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center text-lg">
                {sentimentEmoji}
              </div>
              <div>
                <p className="text-2xl font-bold text-blue-700">{Math.round(stats.avg_sentiment * 100)}%</p>
                <p className="text-xs text-blue-600">Sentiment moyen</p>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1.5">
          <Filter className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-500 font-medium">Plateforme :</span>
        </div>
        <Tabs value={platformFilter} onValueChange={(v) => { setPlatformFilter(v); setOffset(0); }}>
          <TabsList className="h-8">
            {PLATFORM_FILTERS.map((f) => (
              <TabsTrigger key={f.value} value={f.value} className="text-xs h-7 px-2.5">
                {f.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>

        <div className="flex items-center gap-1.5 ml-2">
          <span className="text-sm text-gray-500 font-medium">Statut :</span>
        </div>
        <Tabs value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setOffset(0); }}>
          <TabsList className="h-8">
            {STATUS_FILTERS.map((f) => (
              <TabsTrigger key={f.value} value={f.value} className="text-xs h-7 px-2.5">
                {f.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>

      {/* Interactions List */}
      {isLoading ? (
        <InboxSkeleton />
      ) : interactions.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center">
            <MessageSquare className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-700 mb-1">
              Aucune interaction
            </h3>
            <p className="text-sm text-gray-500 max-w-md mx-auto">
              {platformFilter || statusFilter
                ? "Aucun resultat pour ces filtres. Essayez de modifier vos criteres."
                : "Connectez votre Google Business Profile pour commencer a recevoir et repondre aux avis automatiquement."}
            </p>
          </CardContent>
        </Card>
      ) : (
        <motion.div variants={container} initial="hidden" animate="show" className="space-y-3">
          {interactions.map((interaction) => (
            <InteractionCard
              key={interaction.id}
              interaction={interaction}
              onUpdate={handleUpdate}
            />
          ))}
        </motion.div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2">
          <p className="text-sm text-gray-500">
            {offset + 1}-{Math.min(offset + PAGE_SIZE, total)} sur {total} interactions
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage <= 1}
              onClick={() => fetchData(offset - PAGE_SIZE)}
              className="h-8"
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <span className="text-sm text-gray-600 min-w-[60px] text-center">
              {currentPage} / {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage >= totalPages}
              onClick={() => fetchData(offset + PAGE_SIZE)}
              className="h-8"
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

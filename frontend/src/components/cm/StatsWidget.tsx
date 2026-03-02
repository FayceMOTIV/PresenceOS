"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  MessageSquare,
  Clock,
  CheckCircle,
  TrendingUp,
  AlertTriangle,
  ArrowRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { cmApi } from "@/lib/api";
import { CMStats } from "@/types";

interface StatsWidgetProps {
  brandId: string;
}

export function CMStatsWidget({ brandId }: StatsWidgetProps) {
  const [stats, setStats] = useState<CMStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!brandId) return;
    setIsLoading(true);
    cmApi
      .getStats(brandId, 1)
      .then((res) => setStats(res.data))
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, [brandId]);

  if (isLoading) {
    return (
      <Card className="animate-pulse">
        <CardContent className="p-5 h-32" />
      </Card>
    );
  }

  if (!stats || stats.total_interactions === 0) {
    return null;
  }

  const sentimentEmoji =
    stats.avg_sentiment >= 0.7 ? "😊" : stats.avg_sentiment >= 0.4 ? "😐" : "😟";

  const hasUrgent = stats.pending_count > 0;
  const crisisCount = stats.by_classification?.crisis || 0;

  return (
    <Link href="/inbox">
      <Card
        className={cn(
          "group cursor-pointer transition-all duration-200 hover:shadow-md",
          hasUrgent && "ring-1 ring-amber-200",
          crisisCount > 0 && "ring-2 ring-red-200"
        )}
      >
        <CardHeader className="pb-2 px-5 pt-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-semibold text-gray-700 flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-violet-500" />
              Community Manager
            </CardTitle>
            <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-violet-500 group-hover:translate-x-0.5 transition-all" />
          </div>
        </CardHeader>
        <CardContent className="px-5 pb-4 space-y-3">
          <div className="grid grid-cols-3 gap-3">
            {/* Pending */}
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 mb-0.5">
                <Clock className="w-3.5 h-3.5 text-amber-500" />
                <span className="text-lg font-bold text-gray-900">{stats.pending_count}</span>
              </div>
              <p className="text-[10px] text-gray-500">En attente</p>
            </div>

            {/* Published today */}
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 mb-0.5">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
                <span className="text-lg font-bold text-gray-900">{stats.published_count}</span>
              </div>
              <p className="text-[10px] text-gray-500">Publiees</p>
            </div>

            {/* Sentiment */}
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 mb-0.5">
                <span className="text-base">{sentimentEmoji}</span>
                <span className="text-lg font-bold text-gray-900">
                  {Math.round(stats.avg_sentiment * 100)}%
                </span>
              </div>
              <p className="text-[10px] text-gray-500">Sentiment</p>
            </div>
          </div>

          {/* Alert badges */}
          <div className="flex items-center gap-1.5 flex-wrap">
            {crisisCount > 0 && (
              <Badge className="bg-red-100 text-red-700 text-[10px] gap-1">
                <AlertTriangle className="w-2.5 h-2.5" />
                {crisisCount} alerte{crisisCount > 1 ? "s" : ""}
              </Badge>
            )}
            {stats.pending_count > 5 && (
              <Badge className="bg-amber-100 text-amber-700 text-[10px] gap-1">
                <Clock className="w-2.5 h-2.5" />
                {stats.pending_count} a traiter
              </Badge>
            )}
            {stats.response_rate >= 90 && (
              <Badge className="bg-emerald-100 text-emerald-700 text-[10px] gap-1">
                <TrendingUp className="w-2.5 h-2.5" />
                {stats.response_rate}% repondu
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

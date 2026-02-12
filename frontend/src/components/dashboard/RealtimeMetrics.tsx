"use client";

import React, { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  TrendingUp,
  TrendingDown,
  Eye,
  Heart,
  MessageSquare,
  Share2,
  BarChart3,
  RefreshCw,
  Activity,
} from "lucide-react";
import { metricsApi } from "@/lib/api";
import { DashboardMetrics, PlatformBreakdown } from "@/types";
import { formatNumber } from "@/lib/utils";
import { cn } from "@/lib/utils";

interface RealtimeMetricsProps {
  brandId: string;
  refreshInterval?: number; // ms, default 30s
}

interface MetricCard {
  label: string;
  value: number | string;
  previousValue?: number;
  icon: React.ElementType;
  color: string;
  trend?: "up" | "down" | "neutral";
}

export const RealtimeMetrics: React.FC<RealtimeMetricsProps> = ({
  brandId,
  refreshInterval = 30000,
}) => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [platforms, setPlatforms] = useState<PlatformBreakdown[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchMetrics = useCallback(async () => {
    try {
      const [metricsRes, platformsRes] = await Promise.all([
        metricsApi.getDashboard(brandId, 30),
        metricsApi.getPlatforms(brandId, 30),
      ]);
      setMetrics(metricsRes.data);
      setPlatforms(platformsRes.data);
      setLastUpdated(new Date());
    } catch (error) {
      console.error("Failed to fetch metrics:", error);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [brandId]);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchMetrics, refreshInterval]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    fetchMetrics();
  };

  const metricCards: MetricCard[] = metrics
    ? [
        {
          label: "Impressions",
          value: formatNumber(metrics.total_impressions),
          icon: Eye,
          color: "from-blue-500 to-cyan-500",
        },
        {
          label: "Engagement total",
          value: formatNumber(metrics.total_engagement),
          icon: Heart,
          color: "from-pink-500 to-rose-500",
        },
        {
          label: "Taux d'engagement",
          value: `${metrics.average_engagement_rate.toFixed(1)}%`,
          icon: TrendingUp,
          color: "from-green-500 to-emerald-500",
          trend:
            metrics.average_engagement_rate > 3
              ? "up"
              : metrics.average_engagement_rate > 1
                ? "neutral"
                : "down",
        },
        {
          label: "Posts publies",
          value: metrics.total_posts_published,
          icon: BarChart3,
          color: "from-purple-500 to-violet-500",
        },
      ]
    : [];

  const platformColors: Record<string, string> = {
    instagram: "bg-gradient-to-r from-purple-500 to-pink-500",
    facebook: "bg-blue-600",
    tiktok: "bg-black",
    linkedin: "bg-blue-700",
  };

  if (isLoading) {
    return (
      <Card className="glass-card">
        <CardContent className="p-8">
          <div className="flex items-center justify-center gap-3">
            <Activity className="w-5 h-5 animate-pulse text-primary" />
            <span className="text-muted-foreground">
              Chargement des metriques...
            </span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with refresh */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Activity className="w-5 h-5 text-green-500" />
            Metriques en temps reel
          </h3>
          {lastUpdated && (
            <p className="text-xs text-muted-foreground mt-1">
              Mis a jour: {lastUpdated.toLocaleTimeString("fr-FR")}
            </p>
          )}
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={isRefreshing}
        >
          <RefreshCw
            className={cn("w-4 h-4 mr-2", isRefreshing && "animate-spin")}
          />
          Actualiser
        </Button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <AnimatePresence mode="wait">
          {metricCards.map((card, index) => (
            <motion.div
              key={card.label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <Card className="bento-card overflow-hidden">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div
                      className={cn(
                        "w-9 h-9 rounded-lg flex items-center justify-center bg-gradient-to-br",
                        card.color
                      )}
                    >
                      <card.icon className="w-4 h-4 text-white" />
                    </div>
                    {card.trend && (
                      <div
                        className={cn(
                          "flex items-center gap-1 text-xs font-medium",
                          card.trend === "up" && "text-green-500",
                          card.trend === "down" && "text-red-500",
                          card.trend === "neutral" && "text-yellow-500"
                        )}
                      >
                        {card.trend === "up" ? (
                          <TrendingUp className="w-3 h-3" />
                        ) : card.trend === "down" ? (
                          <TrendingDown className="w-3 h-3" />
                        ) : null}
                      </div>
                    )}
                  </div>
                  <p className="text-2xl font-bold">{card.value}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {card.label}
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Platform Breakdown */}
      {platforms.length > 0 && (
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-base">Par plateforme</CardTitle>
            <CardDescription>Performance des 30 derniers jours</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {platforms.map((platform) => {
                const maxImpressions = Math.max(
                  ...platforms.map((p) => p.total_impressions),
                  1
                );
                const barWidth =
                  (platform.total_impressions / maxImpressions) * 100;

                return (
                  <div key={platform.platform} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <div
                          className={cn(
                            "w-3 h-3 rounded-full",
                            platformColors[platform.platform] || "bg-gray-500"
                          )}
                        />
                        <span className="font-medium capitalize">
                          {platform.platform}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Eye className="w-3 h-3" />
                          {formatNumber(platform.total_impressions)}
                        </span>
                        <span className="flex items-center gap-1">
                          <Heart className="w-3 h-3" />
                          {formatNumber(platform.total_engagement)}
                        </span>
                        <span>
                          {platform.average_engagement_rate.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <motion.div
                        className={cn(
                          "h-full rounded-full",
                          platformColors[platform.platform] || "bg-gray-500"
                        )}
                        initial={{ width: 0 }}
                        animate={{ width: `${barWidth}%` }}
                        transition={{ duration: 0.8, ease: "easeOut" }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* AI Insight */}
      {metrics?.ai_insight && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="glass-card border-primary/20 bg-gradient-to-br from-primary/5 to-purple-500/5">
            <CardContent className="p-5">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Activity className="w-4 h-4 text-primary" />
                </div>
                <div>
                  <p className="text-sm font-medium mb-1">Insight IA</p>
                  <p className="text-sm text-muted-foreground">
                    {metrics.ai_insight}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
};

export default RealtimeMetrics;

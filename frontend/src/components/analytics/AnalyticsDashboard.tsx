"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  Users,
  Heart,
  Eye,
  BarChart3,
  Loader2,
  Lightbulb,
  Zap,
  AlertTriangle,
  Instagram,
  Facebook,
  Linkedin,
  Smartphone,
  MapPin,
} from "lucide-react";
import { analyticsApi } from "@/lib/api";

interface KPIMetric {
  current: number;
  previous: number;
  change: number;
  change_pct: number;
}

interface PlatformData {
  platform: string;
  followers: number | null;
  engagement_rate: number | null;
  posts_count: number;
  top_content_type: string;
  best_time: string;
  growth_trend: string;
}

interface Insight {
  type: string;
  icon: string;
  title: string;
  message: string;
  priority: string;
}

interface AnalyticsOverview {
  brand_id: string;
  period_days: number;
  kpis: {
    followers: KPIMetric;
    engagement_rate: KPIMetric;
    reach: KPIMetric;
    impressions: KPIMetric;
  };
  platforms: PlatformData[];
  top_content: any[];
  weekly_insights: Insight[];
}

interface AnalyticsDashboardProps {
  brandId: string;
}

const PLATFORM_ICONS: Record<string, typeof Instagram> = {
  instagram: Instagram,
  tiktok: Smartphone,
  facebook: Facebook,
  linkedin: Linkedin,
  google_business: MapPin,
};

const PLATFORM_COLORS: Record<string, string> = {
  instagram: "text-pink-400 bg-pink-500/10 border-pink-500/30",
  tiktok: "text-cyan-400 bg-cyan-500/10 border-cyan-500/30",
  facebook: "text-blue-400 bg-blue-500/10 border-blue-500/30",
  linkedin: "text-sky-400 bg-sky-500/10 border-sky-500/30",
  google_business: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
};

const INSIGHT_ICONS: Record<string, typeof TrendingUp> = {
  growth: TrendingUp,
  engagement: Heart,
  recommendation: Lightbulb,
  opportunity: Zap,
  alert: AlertTriangle,
};

const INSIGHT_COLORS: Record<string, string> = {
  high: "border-amber-500/40 bg-amber-500/5",
  medium: "border-zinc-700 bg-zinc-800/30",
  low: "border-zinc-800 bg-zinc-900/30",
};

function KPICard({
  label,
  icon: Icon,
  metric,
  format,
}: {
  label: string;
  icon: typeof Users;
  metric: KPIMetric;
  format?: (v: number) => string;
}) {
  const fmt = format || ((v: number) => v.toLocaleString("fr-FR"));
  const isPositive = metric.change >= 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4 space-y-2"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs text-zinc-500 uppercase tracking-wider">{label}</span>
        <Icon className="w-4 h-4 text-zinc-600" />
      </div>
      <div className="text-2xl font-bold text-zinc-100">{fmt(metric.current)}</div>
      <div className="flex items-center gap-1">
        {isPositive ? (
          <TrendingUp className="w-3 h-3 text-emerald-400" />
        ) : (
          <TrendingDown className="w-3 h-3 text-red-400" />
        )}
        <span
          className={`text-xs font-medium ${isPositive ? "text-emerald-400" : "text-red-400"}`}
        >
          {isPositive ? "+" : ""}
          {metric.change_pct}%
        </span>
        <span className="text-xs text-zinc-600">vs periode precedente</span>
      </div>
    </motion.div>
  );
}

function PlatformCard({ data }: { data: PlatformData }) {
  const Icon = PLATFORM_ICONS[data.platform] || BarChart3;
  const color = PLATFORM_COLORS[data.platform] || "text-zinc-400 bg-zinc-800/50 border-zinc-700";

  return (
    <div className={`border rounded-xl p-4 space-y-3 ${color.split(" ").slice(1).join(" ")}`}>
      <div className="flex items-center gap-2">
        <Icon className={`w-4 h-4 ${color.split(" ")[0]}`} />
        <span className="text-sm font-semibold text-zinc-100 capitalize">{data.platform.replace("_", " ")}</span>
        <span
          className={`ml-auto text-[10px] font-medium px-2 py-0.5 rounded-full ${
            data.growth_trend === "up"
              ? "bg-emerald-500/20 text-emerald-400"
              : data.growth_trend === "down"
                ? "bg-red-500/20 text-red-400"
                : "bg-zinc-700/50 text-zinc-400"
          }`}
        >
          {data.growth_trend === "up" ? "En hausse" : data.growth_trend === "down" ? "En baisse" : "Stable"}
        </span>
      </div>
      <div className="grid grid-cols-3 gap-2 text-center">
        <div>
          <div className="text-sm font-bold text-zinc-100">
            {data.followers !== null ? data.followers.toLocaleString("fr-FR") : "—"}
          </div>
          <div className="text-[10px] text-zinc-500">Abonnes</div>
        </div>
        <div>
          <div className="text-sm font-bold text-zinc-100">
            {data.engagement_rate !== null ? `${data.engagement_rate}%` : "—"}
          </div>
          <div className="text-[10px] text-zinc-500">Engagement</div>
        </div>
        <div>
          <div className="text-sm font-bold text-zinc-100">{data.posts_count}</div>
          <div className="text-[10px] text-zinc-500">Posts</div>
        </div>
      </div>
      <div className="flex items-center justify-between text-[10px] text-zinc-600">
        <span>Top : {data.top_content_type}</span>
        <span>Meilleure heure : {data.best_time}</span>
      </div>
    </div>
  );
}

function InsightCard({ insight }: { insight: Insight }) {
  const Icon = INSIGHT_ICONS[insight.type] || Lightbulb;
  const borderColor = INSIGHT_COLORS[insight.priority] || INSIGHT_COLORS.medium;

  return (
    <div className={`border rounded-xl p-4 space-y-2 ${borderColor}`}>
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 text-amber-400" />
        <span className="text-sm font-semibold text-zinc-100">{insight.title}</span>
      </div>
      <p className="text-xs text-zinc-400 leading-relaxed">{insight.message}</p>
    </div>
  );
}

export function AnalyticsDashboard({ brandId }: AnalyticsDashboardProps) {
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [period, setPeriod] = useState(30);

  useEffect(() => {
    if (!brandId) return;
    setIsLoading(true);
    analyticsApi
      .getOverview(brandId, period)
      .then((res) => setData(res.data))
      .catch((err) => console.error("Error fetching analytics:", err))
      .finally(() => setIsLoading(false));
  }, [brandId, period]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-zinc-500" />
      </div>
    );
  }

  if (!data) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      {/* Period selector */}
      <div className="flex items-center gap-2">
        {[7, 14, 30, 60].map((d) => (
          <button
            key={d}
            onClick={() => setPeriod(d)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              period === d
                ? "bg-amber-500/15 text-amber-400 border border-amber-500/40"
                : "bg-zinc-800/50 text-zinc-400 border border-zinc-800 hover:border-zinc-700"
            }`}
          >
            {d}j
          </button>
        ))}
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KPICard label="Abonnes" icon={Users} metric={data.kpis.followers} />
        <KPICard
          label="Engagement"
          icon={Heart}
          metric={data.kpis.engagement_rate}
          format={(v) => `${v}%`}
        />
        <KPICard label="Portee" icon={Eye} metric={data.kpis.reach} />
        <KPICard label="Impressions" icon={BarChart3} metric={data.kpis.impressions} />
      </div>

      {/* Platform Breakdown */}
      <div>
        <h3 className="text-sm font-semibold text-zinc-300 mb-3">Par plateforme</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {data.platforms.map((p) => (
            <PlatformCard key={p.platform} data={p} />
          ))}
        </div>
      </div>

      {/* Weekly Insights */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Lightbulb className="w-4 h-4 text-amber-400" />
          <h3 className="text-sm font-semibold text-zinc-300">Insights hebdomadaires IA</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {data.weekly_insights.map((insight, i) => (
            <InsightCard key={i} insight={insight} />
          ))}
        </div>
      </div>

      {/* Top Content */}
      {data.top_content.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-zinc-300 mb-3">Top contenu</h3>
          <div className="space-y-2">
            {data.top_content.map((content, i) => {
              const Icon = PLATFORM_ICONS[content.platform] || BarChart3;
              return (
                <div
                  key={content.id}
                  className="flex items-center gap-3 bg-zinc-900/40 border border-zinc-800 rounded-xl p-3"
                >
                  <span className="text-xs font-bold text-zinc-500 w-5">#{i + 1}</span>
                  <Icon className="w-4 h-4 text-zinc-500 flex-shrink-0" />
                  <span className="text-sm text-zinc-200 flex-1 truncate">
                    {content.caption}
                  </span>
                  <div className="flex items-center gap-3 text-xs text-zinc-500">
                    <span>{content.likes} likes</span>
                    <span>{content.comments} comm.</span>
                    <span className="font-bold text-amber-400">
                      {content.engagement_rate}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </motion.div>
  );
}

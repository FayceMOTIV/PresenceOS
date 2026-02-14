"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Zap,
  TrendingUp,
  Loader2,
  Hash,
  Clock,
  Instagram,
  Smartphone,
  Facebook,
  Linkedin,
  Copy,
  CheckCircle2,
} from "lucide-react";
import { trendsRadarApi } from "@/lib/api";

interface Trend {
  id: string;
  topic: string;
  category: string;
  virality_score: number;
  platforms: string[];
  description: string;
  content_suggestion: string;
  hashtags: string[];
  detected_at: string;
  expires_in_hours: number;
}

interface TrendRadarProps {
  brandId: string;
}

const PLATFORM_ICONS: Record<string, typeof Instagram> = {
  instagram: Instagram,
  tiktok: Smartphone,
  facebook: Facebook,
  linkedin: Linkedin,
};

const CATEGORY_LABELS: Record<string, string> = {
  food_trend: "Food",
  marketing_trend: "Marketing",
  content_format: "Format",
  seasonal: "Saison",
  values_trend: "Valeurs",
};

function ViralityBadge({ score }: { score: number }) {
  const color =
    score >= 85
      ? "text-emerald-400 bg-emerald-500/15 border-emerald-500/40"
      : score >= 70
        ? "text-amber-400 bg-amber-500/15 border-amber-500/40"
        : "text-gray-500 bg-gray-100/60 border-gray-200";

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[10px] font-bold ${color}`}>
      <Zap className="w-2.5 h-2.5" />
      {score}
    </span>
  );
}

function TrendCard({ trend }: { trend: Trend }) {
  const [copied, setCopied] = useState(false);

  const handleCopyHashtags = async () => {
    await navigator.clipboard.writeText(trend.hashtags.map((h) => `#${h}`).join(" "));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white border border-gray-200/60 rounded-xl p-4 space-y-3 shadow-sm"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-amber-400" />
          <span className="text-sm font-semibold text-gray-900">{trend.topic}</span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-gray-100/60 text-gray-600 border border-gray-200">
            {CATEGORY_LABELS[trend.category] || trend.category}
          </span>
        </div>
        <ViralityBadge score={trend.virality_score} />
      </div>

      {/* Description */}
      <p className="text-xs text-gray-600 leading-relaxed">{trend.description}</p>

      {/* Content suggestion */}
      <div className="bg-amber-500/5 border border-amber-500/20 rounded-lg p-3">
        <p className="text-xs text-amber-300">
          <span className="font-semibold">Suggestion :</span> {trend.content_suggestion}
        </p>
      </div>

      {/* Platforms + Hashtags */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          {trend.platforms.map((p) => {
            const Icon = PLATFORM_ICONS[p] || Smartphone;
            return <Icon key={p} className="w-3.5 h-3.5 text-gray-500" />;
          })}
        </div>
        <button
          onClick={handleCopyHashtags}
          className="flex items-center gap-1 text-[10px] text-gray-500 hover:text-gray-800 transition-colors"
        >
          {copied ? (
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
          ) : (
            <Copy className="w-3 h-3" />
          )}
          <Hash className="w-3 h-3" />
          {trend.hashtags.length} hashtags
        </button>
      </div>

      {/* Expiry */}
      <div className="flex items-center gap-1 text-[10px] text-gray-400">
        <Clock className="w-3 h-3" />
        Expire dans {trend.expires_in_hours}h
      </div>
    </motion.div>
  );
}

export function TrendRadar({ brandId }: TrendRadarProps) {
  const [trends, setTrends] = useState<Trend[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [category, setCategory] = useState<string | null>(null);
  const [categories, setCategories] = useState<{ id: string; label: string }[]>([]);

  useEffect(() => {
    if (!brandId) return;
    setIsLoading(true);
    Promise.all([
      trendsRadarApi.getTrends(brandId, { category: category || undefined }),
      trendsRadarApi.getCategories(),
    ])
      .then(([trendsRes, catsRes]) => {
        setTrends(trendsRes.data || []);
        setCategories(catsRes.data || []);
      })
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [brandId, category]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
      {/* Category filter */}
      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => setCategory(null)}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
            !category
              ? "bg-amber-500/15 text-amber-400 border border-amber-500/40"
              : "bg-gray-100/60 text-gray-600 border border-gray-200/60 hover:bg-gray-100"
          }`}
        >
          Toutes
        </button>
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setCategory(cat.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              category === cat.id
                ? "bg-amber-500/15 text-amber-400 border border-amber-500/40"
                : "bg-gray-100/60 text-gray-600 border border-gray-200/60 hover:bg-gray-100"
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Trends list */}
      <div className="space-y-3">
        {trends.map((trend) => (
          <TrendCard key={trend.id} trend={trend} />
        ))}
      </div>

      {trends.length === 0 && (
        <div className="text-center py-8">
          <TrendingUp className="w-8 h-8 text-gray-200 mx-auto mb-2" />
          <p className="text-sm text-gray-500">Aucune tendance detectee pour ce filtre</p>
        </div>
      )}
    </motion.div>
  );
}

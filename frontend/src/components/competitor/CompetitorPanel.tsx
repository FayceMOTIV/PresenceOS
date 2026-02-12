"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Users,
  Plus,
  Trash2,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Loader2,
  Instagram,
  Smartphone,
  Facebook,
  Target,
} from "lucide-react";
import { competitorApi } from "@/lib/api";

interface Competitor {
  id: string;
  name: string;
  handle: string;
  platform: string;
  followers: number;
  engagement_rate: number;
  post_frequency: number;
  top_content: string;
  strength: string;
  weakness: string;
}

interface Benchmark {
  your_metrics: { followers: number; engagement_rate: number; post_frequency: number };
  competitor_avg: { followers: number; engagement_rate: number; post_frequency: number };
  ranking: { followers: number; engagement: number; total_competitors: number };
  gaps: string[];
}

interface CompetitorPanelProps {
  brandId: string;
}

const PLATFORM_ICONS: Record<string, typeof Instagram> = {
  instagram: Instagram,
  tiktok: Smartphone,
  facebook: Facebook,
};

function CompetitorCard({
  competitor,
  onRemove,
}: {
  competitor: Competitor;
  onRemove: () => void;
}) {
  const Icon = PLATFORM_ICONS[competitor.platform] || Users;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4 space-y-3"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 text-zinc-500" />
          <span className="text-sm font-semibold text-zinc-100">{competitor.name}</span>
          <span className="text-xs text-zinc-500">{competitor.handle}</span>
        </div>
        <button
          onClick={onRemove}
          className="text-zinc-600 hover:text-red-400 transition-colors"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="bg-zinc-800/40 rounded-lg p-2">
          <div className="text-sm font-bold text-zinc-100">
            {competitor.followers.toLocaleString("fr-FR")}
          </div>
          <div className="text-[10px] text-zinc-500">Abonnes</div>
        </div>
        <div className="bg-zinc-800/40 rounded-lg p-2">
          <div className="text-sm font-bold text-zinc-100">{competitor.engagement_rate}%</div>
          <div className="text-[10px] text-zinc-500">Engagement</div>
        </div>
        <div className="bg-zinc-800/40 rounded-lg p-2">
          <div className="text-sm font-bold text-zinc-100">{competitor.post_frequency}/sem</div>
          <div className="text-[10px] text-zinc-500">Frequence</div>
        </div>
      </div>

      <div className="space-y-1.5 text-xs">
        <p className="text-emerald-400">
          <span className="font-medium">Force :</span> {competitor.strength}
        </p>
        <p className="text-red-400">
          <span className="font-medium">Faiblesse :</span> {competitor.weakness}
        </p>
      </div>
    </motion.div>
  );
}

export function CompetitorPanel({ brandId }: CompetitorPanelProps) {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [benchmark, setBenchmark] = useState<Benchmark | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [newName, setNewName] = useState("");
  const [newHandle, setNewHandle] = useState("");

  useEffect(() => {
    if (!brandId) return;
    setIsLoading(true);
    Promise.all([
      competitorApi.getCompetitors(brandId),
      competitorApi.getBenchmark(brandId),
    ])
      .then(([compRes, benchRes]) => {
        setCompetitors(compRes.data || []);
        setBenchmark(benchRes.data);
      })
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [brandId]);

  const handleAdd = async () => {
    if (!newName.trim() || !newHandle.trim()) return;
    try {
      const res = await competitorApi.addCompetitor(brandId, {
        name: newName,
        handle: newHandle,
      });
      setCompetitors((prev) => [...prev, res.data]);
      setNewName("");
      setNewHandle("");
      setShowAdd(false);
    } catch (err) {
      console.error("Error adding competitor:", err);
    }
  };

  const handleRemove = async (competitorId: string) => {
    try {
      await competitorApi.removeCompetitor(brandId, competitorId);
      setCompetitors((prev) => prev.filter((c) => c.id !== competitorId));
    } catch (err) {
      console.error("Error removing competitor:", err);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-zinc-500" />
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-5">
      {/* Benchmark summary */}
      {benchmark && (
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-2">
            <Target className="w-5 h-5 text-amber-400" />
            <h3 className="text-sm font-semibold text-zinc-100">Benchmark concurrentiel</h3>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "Abonnes", yours: benchmark.your_metrics.followers, avg: benchmark.competitor_avg.followers },
              { label: "Engagement", yours: benchmark.your_metrics.engagement_rate, avg: benchmark.competitor_avg.engagement_rate, suffix: "%" },
              { label: "Posts/sem", yours: benchmark.your_metrics.post_frequency, avg: benchmark.competitor_avg.post_frequency },
            ].map((m) => {
              const isAbove = m.yours >= m.avg;
              return (
                <div key={m.label} className="bg-zinc-800/40 rounded-lg p-3 text-center">
                  <div className="text-xs text-zinc-500 mb-1">{m.label}</div>
                  <div className="text-lg font-bold text-zinc-100">
                    {typeof m.yours === "number" ? m.yours.toLocaleString("fr-FR") : m.yours}
                    {m.suffix || ""}
                  </div>
                  <div className={`flex items-center justify-center gap-1 text-[10px] ${isAbove ? "text-emerald-400" : "text-red-400"}`}>
                    {isAbove ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                    vs moy. {m.avg}{m.suffix || ""}
                  </div>
                </div>
              );
            })}
          </div>
          {benchmark.gaps.length > 0 && (
            <div className="space-y-1">
              <p className="text-[10px] text-zinc-600 uppercase tracking-wider">Recommandations</p>
              {benchmark.gaps.map((gap, i) => (
                <p key={i} className="text-xs text-zinc-400">• {gap}</p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Competitors list */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-300">
          Concurrents suivis ({competitors.length})
        </h3>
        <button
          onClick={() => setShowAdd(!showAdd)}
          className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-medium hover:bg-amber-500/20 transition-colors"
        >
          <Plus className="w-3 h-3" />
          Ajouter
        </button>
      </div>

      {/* Add form */}
      {showAdd && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="flex gap-2"
        >
          <input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Nom"
            className="flex-1 bg-zinc-800/50 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-600 focus:border-amber-500/50 focus:outline-none"
          />
          <input
            value={newHandle}
            onChange={(e) => setNewHandle(e.target.value)}
            placeholder="@handle"
            className="flex-1 bg-zinc-800/50 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-600 focus:border-amber-500/50 focus:outline-none"
          />
          <button
            onClick={handleAdd}
            className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-black text-sm font-medium transition-colors"
          >
            OK
          </button>
        </motion.div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {competitors.map((c) => (
          <CompetitorCard
            key={c.id}
            competitor={c}
            onRemove={() => handleRemove(c.id)}
          />
        ))}
      </div>
    </motion.div>
  );
}

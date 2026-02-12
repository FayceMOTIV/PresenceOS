"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import {
  TrendingUp,
  X,
  ExternalLink,
  Loader2,
  Sparkles,
  RefreshCw,
} from "lucide-react";
import { agentsApi } from "@/lib/api";
import { useAgentTask } from "@/hooks/use-agent-task";
import type { TrendItem, TrendsScanResult } from "@/types/agents";
import { cn } from "@/lib/utils";

interface TrendsSidebarProps {
  onClose: () => void;
  onCreatePost: (topic: string) => void;
}

function TrendCard({
  trend,
  index,
  onCreatePost,
}: {
  trend: TrendItem;
  index: number;
  onCreatePost: (topic: string) => void;
}) {
  const scoreColor =
    trend.relevance_score >= 8
      ? "text-green-500"
      : trend.relevance_score >= 5
        ? "text-yellow-500"
        : "text-muted-foreground";

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1 }}
      className="rounded-lg border bg-card p-3 space-y-2 hover:border-primary/30 transition-colors"
    >
      <div className="flex items-start justify-between gap-2">
        <h4 className="text-sm font-medium leading-tight">{trend.topic}</h4>
        <span className={cn("text-xs font-bold whitespace-nowrap", scoreColor)}>
          {trend.relevance_score}/10
        </span>
      </div>

      {trend.suggested_angle && (
        <p className="text-xs text-muted-foreground">{trend.suggested_angle}</p>
      )}

      {trend.platforms && trend.platforms.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {trend.platforms.map((p) => (
            <span
              key={p}
              className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground"
            >
              {p}
            </span>
          ))}
        </div>
      )}

      {trend.hashtags && trend.hashtags.length > 0 && (
        <p className="text-[10px] text-primary truncate">
          {trend.hashtags.slice(0, 4).join(" ")}
        </p>
      )}

      <Button
        variant="outline"
        size="sm"
        className="w-full text-xs h-7"
        onClick={() =>
          onCreatePost(
            `Cree un post sur la tendance: ${trend.topic}. Angle: ${trend.suggested_angle || trend.topic}`
          )
        }
      >
        <Sparkles className="w-3 h-3 mr-1" />
        Creer un post
      </Button>
    </motion.div>
  );
}

export function TrendsSidebar({ onClose, onCreatePost }: TrendsSidebarProps) {
  const [trends, setTrends] = useState<TrendItem[]>([]);
  const [summary, setSummary] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const { task } = useAgentTask(taskId);

  const loadTrends = async () => {
    const brandId = localStorage.getItem("brand_id");
    if (!brandId) return;

    setIsLoading(true);
    setTrends([]);
    setSummary("");

    try {
      const response = await agentsApi.scanTrends({
        brand_id: brandId,
        industry: "general",
        platforms: ["instagram", "linkedin", "tiktok"],
      });
      setTaskId(response.data.task_id);
    } catch {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!task || !taskId) return;

    if (task.status === "completed" && task.result) {
      const result = task.result as unknown as TrendsScanResult;
      setTrends(result.trends || []);
      setSummary(result.summary || "");
      setIsLoading(false);
      setTaskId(null);
    } else if (task.status === "failed") {
      setIsLoading(false);
      setTaskId(null);
    }
  }, [task, taskId]);

  useEffect(() => {
    loadTrends();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="h-full flex flex-col border-l bg-card/50 rounded-l-xl">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-primary" />
          <h3 className="font-semibold text-sm">Tendances</h3>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={loadTrends}
            disabled={isLoading}
            className="h-7 w-7 p-0"
          >
            <RefreshCw className={cn("w-3.5 h-3.5", isLoading && "animate-spin")} />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="h-7 w-7 p-0"
          >
            <X className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-40 gap-3">
            <Loader2 className="w-6 h-6 animate-spin text-primary" />
            <p className="text-xs text-muted-foreground">Scan des tendances...</p>
          </div>
        ) : trends.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 gap-3 text-center">
            <TrendingUp className="w-8 h-8 text-muted-foreground/50" />
            <p className="text-xs text-muted-foreground">
              Aucune tendance detectee. Cliquez sur rafraichir pour scanner.
            </p>
          </div>
        ) : (
          <>
            {summary && (
              <div className="text-xs text-muted-foreground bg-muted/50 rounded-lg p-2">
                {summary}
              </div>
            )}
            {trends.map((trend, i) => (
              <TrendCard
                key={i}
                trend={trend}
                index={i}
                onCreatePost={onCreatePost}
              />
            ))}
          </>
        )}
      </div>
    </div>
  );
}

"use client";

import { motion } from "framer-motion";
import { Flame, Target, BookOpen } from "lucide-react";
import type { PhotoCaptionSuggestion, EngagementScore } from "@/types";
import type { CaptionStyle } from "@/types";

interface CaptionCardProps {
  suggestion: PhotoCaptionSuggestion;
  engagementScore?: EngagementScore;
  isSelected: boolean;
  onSelect: () => void;
}

const STYLE_CONFIG: Record<CaptionStyle, {
  label: string;
  icon: typeof Flame;
  gradient: string;
  border: string;
  bg: string;
}> = {
  gourmande: {
    label: "Version Gourmande",
    icon: Flame,
    gradient: "from-amber-500 to-orange-500",
    border: "border-amber-500/30",
    bg: "bg-amber-500/5",
  },
  promo: {
    label: "Version Promo",
    icon: Target,
    gradient: "from-red-500 to-pink-500",
    border: "border-red-500/30",
    bg: "bg-red-500/5",
  },
  story: {
    label: "Version Story",
    icon: BookOpen,
    gradient: "from-blue-500 to-indigo-500",
    border: "border-blue-500/30",
    bg: "bg-blue-500/5",
  },
};

export function CaptionCard({ suggestion, engagementScore, isSelected, onSelect }: CaptionCardProps) {
  const config = STYLE_CONFIG[suggestion.style];
  const Icon = config.icon;

  const truncatedCaption = suggestion.caption.length > 120
    ? suggestion.caption.substring(0, 120) + "..."
    : suggestion.caption;

  return (
    <motion.button
      onClick={onSelect}
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      className={`w-full text-left rounded-2xl border-2 p-4 transition-all duration-200 ${
        isSelected
          ? `${config.border} ${config.bg} shadow-lg`
          : "border-border/50 hover:border-border bg-card"
      }`}
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${config.gradient} flex items-center justify-center`}>
          <Icon className="w-4 h-4 text-white" />
        </div>
        <span className="font-semibold text-sm text-foreground">{config.label}</span>
        {engagementScore && (
          <span className={`ml-auto text-xs font-bold px-2 py-0.5 rounded-full ${
            engagementScore.total >= 70 ? "bg-green-500/10 text-green-500" :
            engagementScore.total >= 40 ? "bg-yellow-500/10 text-yellow-500" :
            "bg-red-500/10 text-red-500"
          }`}>
            {engagementScore.total}/100
          </span>
        )}
      </div>

      {/* Caption preview */}
      <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line mb-3">
        {truncatedCaption}
      </p>

      {/* Footer */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">
          {suggestion.hashtags.length} hashtags
        </span>
        <span className="text-xs text-muted-foreground italic">
          {suggestion.ai_notes.length > 60
            ? suggestion.ai_notes.substring(0, 60) + "..."
            : suggestion.ai_notes}
        </span>
      </div>
    </motion.button>
  );
}

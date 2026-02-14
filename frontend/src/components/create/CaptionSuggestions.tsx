"use client";

import { motion } from "framer-motion";
import { RefreshCw, Eye, Sparkles } from "lucide-react";
import type { PhotoCaptionSuggestion, ImageAnalysis, EngagementScore, CaptionStyle } from "@/types";
import { CaptionCard } from "./CaptionCard";

interface CaptionSuggestionsProps {
  suggestions: PhotoCaptionSuggestion[];
  engagementScores: Record<string, EngagementScore>;
  imageAnalysis: ImageAnalysis;
  photoPreviewUrl: string | null;
  onSelect: (style: CaptionStyle) => void;
  onRegenerateAll: () => void;
  isAnalyzing: boolean;
}

export function CaptionSuggestions({
  suggestions,
  engagementScores,
  imageAnalysis,
  photoPreviewUrl,
  onSelect,
  onRegenerateAll,
  isAnalyzing,
}: CaptionSuggestionsProps) {
  return (
    <div className="flex gap-6 items-start">
      {/* Left: Photo + Analysis */}
      <div className="w-[280px] flex-shrink-0 space-y-4">
        {photoPreviewUrl && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="rounded-2xl overflow-hidden border border-border/50 shadow-lg"
          >
            <img
              src={photoPreviewUrl}
              alt="Photo uploadee"
              className="w-full h-auto object-cover"
            />
          </motion.div>
        )}

        {/* Analysis summary */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-card rounded-xl p-3 space-y-2"
        >
          <div className="flex items-center gap-1.5 mb-1">
            <Eye className="w-3.5 h-3.5 text-primary" />
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Analyse IA
            </span>
          </div>
          <p className="text-xs text-foreground leading-relaxed">
            {imageAnalysis.description}
          </p>
          <div className="flex flex-wrap gap-1 mt-2">
            {imageAnalysis.tags.slice(0, 6).map((tag) => (
              <span
                key={tag}
                className="text-[10px] px-1.5 py-0.5 rounded-full bg-primary/10 text-primary"
              >
                {tag}
              </span>
            ))}
          </div>
          <div className="flex items-center gap-1 mt-1">
            <Sparkles className="w-3 h-3 text-muted-foreground" />
            <span className="text-[10px] text-muted-foreground capitalize">
              Mood: {imageAnalysis.mood}
            </span>
          </div>
        </motion.div>
      </div>

      {/* Right: 3 Caption Cards */}
      <div className="flex-1 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-foreground">
            Choisis ton style
          </h3>
          <button
            onClick={onRegenerateAll}
            disabled={isAnalyzing}
            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isAnalyzing ? "animate-spin" : ""}`} />
            Régénérer
          </button>
        </div>

        {suggestions.map((suggestion, index) => (
          <motion.div
            key={suggestion.style}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <CaptionCard
              suggestion={suggestion}
              engagementScore={engagementScores[suggestion.style]}
              isSelected={false}
              onSelect={() => onSelect(suggestion.style)}
            />
          </motion.div>
        ))}
      </div>
    </div>
  );
}

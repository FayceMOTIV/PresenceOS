"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Save, Calendar } from "lucide-react";
import type { EngagementScore } from "@/types";
import { PLATFORM_CHAR_LIMITS } from "@/types";
import { CharacterCounter } from "./CharacterCounter";
import { EngagementGauge } from "./EngagementGauge";

interface MultiPlatformPreviewProps {
  photoUrl: string | null;
  caption: string;
  hashtags: string[];
  brandName: string;
  platforms: string[];
  engagementScore?: EngagementScore;
  onBack: () => void;
  onSave: () => void;
}

const PLATFORM_CONFIG: Record<string, { label: string; abbr: string; color: string }> = {
  instagram_post: { label: "Instagram", abbr: "IG", color: "from-pink-500 to-purple-500" },
  facebook: { label: "Facebook", abbr: "FB", color: "from-blue-600 to-blue-400" },
  linkedin: { label: "LinkedIn", abbr: "LI", color: "from-blue-700 to-blue-500" },
  tiktok: { label: "TikTok", abbr: "TT", color: "from-gray-900 to-gray-700" },
  instagram_story: { label: "Story", abbr: "ST", color: "from-orange-500 to-pink-500" },
  instagram_reel: { label: "Reel", abbr: "RL", color: "from-purple-500 to-pink-500" },
};

export function MultiPlatformPreview({
  photoUrl,
  caption,
  hashtags,
  brandName,
  platforms,
  engagementScore,
  onBack,
  onSave,
}: MultiPlatformPreviewProps) {
  const [activeTab, setActiveTab] = useState(platforms[0] || "instagram_post");

  const fullCaption = caption + (hashtags.length > 0 ? "\n\n" + hashtags.map((h) => `#${h.replace(/^#/, "")}`).join(" ") : "");
  const charLimit = PLATFORM_CHAR_LIMITS[activeTab] || 2200;
  const isOverLimit = fullCaption.length > charLimit;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Modifier
        </button>
        <h3 className="text-sm font-semibold text-foreground">
          Previsualisation
        </h3>
      </div>

      {/* Platform tabs */}
      <div className="flex gap-2">
        {platforms.map((platform) => {
          const config = PLATFORM_CONFIG[platform] || { label: platform, abbr: "?", color: "from-gray-500 to-gray-400" };
          return (
            <button
              key={platform}
              onClick={() => setActiveTab(platform)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === platform
                  ? `bg-gradient-to-r ${config.color} text-white shadow-md`
                  : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
              }`}
            >
              {config.label}
            </button>
          );
        })}
      </div>

      <div className="flex gap-6 items-start">
        {/* Preview mockup */}
        <div className="flex-1 glass-card rounded-2xl overflow-hidden">
          {/* Platform header */}
          <div className="px-4 py-3 border-b border-border/50 flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-primary/60" />
            <span className="font-semibold text-sm text-foreground">{brandName}</span>
          </div>

          {/* Photo */}
          {photoUrl && (
            <img src={photoUrl} alt="Preview" className="w-full h-auto" />
          )}

          {/* Caption */}
          <div className="p-4">
            <p className="text-sm text-foreground whitespace-pre-line leading-relaxed">
              {caption}
            </p>
            {hashtags.length > 0 && (
              <p className="text-sm text-primary mt-2">
                {hashtags.map((h) => `#${h.replace(/^#/, "")}`).join(" ")}
              </p>
            )}
          </div>

          {/* Footer */}
          <div className="px-4 py-3 border-t border-border/50 flex items-center justify-between">
            <CharacterCounter text={fullCaption} platform={activeTab} />
            {isOverLimit && (
              <span className="text-xs text-red-500 font-medium">
                Depasse la limite !
              </span>
            )}
          </div>
        </div>

        {/* Engagement score */}
        {engagementScore && (
          <div className="w-[120px] flex-shrink-0 group relative">
            <EngagementGauge score={engagementScore} size="lg" />
          </div>
        )}
      </div>

      {/* Action buttons */}
      <div className="flex gap-3">
        <motion.button
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
          onClick={onSave}
          className="flex-1 py-3 rounded-xl bg-gradient-to-r from-primary to-primary/80 text-primary-foreground font-semibold text-sm flex items-center justify-center gap-2 shadow-lg hover:shadow-xl transition-all"
        >
          <Save className="w-4 h-4" />
          Sauvegarder le brouillon
        </motion.button>
        <motion.button
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
          className="px-6 py-3 rounded-xl border border-border text-sm font-medium text-foreground flex items-center gap-2 hover:bg-secondary transition-all"
        >
          <Calendar className="w-4 h-4" />
          Programmer
        </motion.button>
      </div>
    </motion.div>
  );
}

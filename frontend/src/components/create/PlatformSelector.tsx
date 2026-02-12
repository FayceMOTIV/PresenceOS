"use client";

import { motion } from "framer-motion";

const platformConfig: Record<string, { label: string; color: string; icon: string }> = {
  instagram: {
    label: "Instagram",
    color: "from-[#833AB4] via-[#FD1D1D] to-[#F77737]",
    icon: "IG",
  },
  facebook: {
    label: "Facebook",
    color: "from-[#1877F2] to-[#1877F2]",
    icon: "FB",
  },
  tiktok: {
    label: "TikTok",
    color: "from-black to-black",
    icon: "TT",
  },
  linkedin: {
    label: "LinkedIn",
    color: "from-[#0A66C2] to-[#0A66C2]",
    icon: "LI",
  },
};

interface PlatformSelectorProps {
  platforms: string[];
  onToggle: (platform: string) => void;
}

export function PlatformSelector({ platforms, onToggle }: PlatformSelectorProps) {
  const allPlatforms = ["instagram", "facebook", "tiktok", "linkedin"];

  return (
    <div className="flex gap-2 flex-wrap">
      {allPlatforms.map((p) => {
        const config = platformConfig[p];
        const isActive = platforms.includes(p);

        return (
          <motion.button
            key={p}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => onToggle(p)}
            className={`
              inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
              transition-all duration-200 border
              ${
                isActive
                  ? `bg-gradient-to-r ${config.color} text-white border-transparent shadow-md`
                  : "bg-secondary/30 text-muted-foreground border-border/50 opacity-50 hover:opacity-80"
              }
            `}
          >
            <span className="font-bold">{config.icon}</span>
            <span>{config.label}</span>
          </motion.button>
        );
      })}
    </div>
  );
}

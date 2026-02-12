"use client";

import { motion } from "framer-motion";
import type { EngagementScore } from "@/types";

interface EngagementGaugeProps {
  score: EngagementScore;
  size?: "sm" | "md" | "lg";
}

const SIZES = {
  sm: { width: 60, stroke: 4, text: "text-sm" },
  md: { width: 80, stroke: 5, text: "text-lg" },
  lg: { width: 100, stroke: 6, text: "text-xl" },
};

export function EngagementGauge({ score, size = "md" }: EngagementGaugeProps) {
  const { width, stroke, text } = SIZES[size];
  const radius = (width - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score.total / 100) * circumference;

  let color = "stroke-red-500";
  let textColor = "text-red-500";
  if (score.total >= 70) {
    color = "stroke-green-500";
    textColor = "text-green-500";
  } else if (score.total >= 40) {
    color = "stroke-yellow-500";
    textColor = "text-yellow-500";
  }

  const breakdown = [
    { label: "Hook", value: score.has_hook, max: 20 },
    { label: "CTA", value: score.has_cta, max: 15 },
    { label: "Hashtags", value: score.hashtag_score, max: 15 },
    { label: "Emojis", value: score.emoji_score, max: 10 },
    { label: "Longueur", value: score.length_score, max: 15 },
    { label: "Lisibilite", value: score.readability_score, max: 10 },
    { label: "Mix tags", value: score.trending_score, max: 15 },
  ];

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width, height: width }}>
        <svg width={width} height={width} className="-rotate-90">
          <circle
            cx={width / 2}
            cy={width / 2}
            r={radius}
            fill="none"
            strokeWidth={stroke}
            className="stroke-muted/30"
          />
          <motion.circle
            cx={width / 2}
            cy={width / 2}
            r={radius}
            fill="none"
            strokeWidth={stroke}
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1, ease: "easeOut" }}
            strokeLinecap="round"
            className={color}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={`font-bold ${text} ${textColor}`}>{score.total}</span>
        </div>
      </div>
      <span className="text-[10px] text-muted-foreground uppercase tracking-wider">
        Score engagement
      </span>

      {/* Breakdown tooltip on hover */}
      <div className="hidden group-hover:block absolute top-full mt-2 bg-popover border rounded-lg p-3 shadow-lg z-10 w-48">
        {breakdown.map((item) => (
          <div key={item.label} className="flex justify-between text-xs py-0.5">
            <span className="text-muted-foreground">{item.label}</span>
            <span className="font-medium">
              {item.value}/{item.max}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

"use client";

import { PLATFORM_CHAR_LIMITS } from "@/types";

interface CharacterCounterProps {
  text: string;
  platform: string;
}

export function CharacterCounter({ text, platform }: CharacterCounterProps) {
  const max = PLATFORM_CHAR_LIMITS[platform] || 2200;
  const current = text.length;
  const percentage = (current / max) * 100;

  let colorClass = "text-green-500";
  if (percentage > 90) colorClass = "text-red-500";
  else if (percentage > 75) colorClass = "text-yellow-500";

  return (
    <span className={`text-xs font-mono ${colorClass}`}>
      {current}/{max}
    </span>
  );
}

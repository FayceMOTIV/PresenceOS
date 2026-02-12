"use client";

import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

const thinkingTexts = [
  "Analyse de l'image...",
  "Redaction en cours...",
  "Preparation du preview...",
];

export function ThinkingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="flex items-start gap-3 py-3"
    >
      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 animate-glow-pulse">
        <Sparkles className="w-4 h-4 text-primary" />
      </div>
      <div className="flex-1 space-y-2 pt-1">
        <div className="h-2 rounded-full bg-secondary overflow-hidden relative">
          <div className="absolute inset-0 animate-knight-rider bg-gradient-to-r from-transparent via-primary/40 to-transparent rounded-full" />
        </div>
        <div className="h-2 w-2/3 rounded-full bg-secondary overflow-hidden relative">
          <div
            className="absolute inset-0 animate-knight-rider bg-gradient-to-r from-transparent via-primary/30 to-transparent rounded-full"
            style={{ animationDelay: "0.3s" }}
          />
        </div>
      </div>
    </motion.div>
  );
}

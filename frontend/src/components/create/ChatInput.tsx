"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { SendHorizonal } from "lucide-react";

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({ onSend, disabled, placeholder }: ChatInputProps) {
  const [text, setText] = useState("");

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const trimmed = text.trim();
      if (!trimmed || disabled) return;
      onSend(trimmed);
      setText("");
    },
    [text, onSend, disabled]
  );

  return (
    <form onSubmit={handleSubmit} className="relative">
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={disabled}
        placeholder={placeholder || "Ajoute du contexte... (prix, promo, horaires)"}
        className="
          w-full rounded-xl border border-border/50 bg-secondary/30 px-4 py-3 pr-12
          text-sm text-foreground placeholder:text-muted-foreground/60
          focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50
          disabled:opacity-50 transition-all
        "
      />
      <motion.button
        type="submit"
        disabled={disabled || !text.trim()}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        className="
          absolute right-2 top-1/2 -translate-y-1/2
          w-8 h-8 rounded-lg flex items-center justify-center
          text-primary disabled:text-muted-foreground/30
          hover:bg-primary/10 transition-colors
        "
      >
        <SendHorizonal className="w-4 h-4" />
      </motion.button>
    </form>
  );
}

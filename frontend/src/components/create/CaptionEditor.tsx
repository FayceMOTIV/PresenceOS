"use client";

import { motion } from "framer-motion";
import { Hash, Smile, ArrowLeft, Check, RefreshCw, X, Sparkles } from "lucide-react";
import type { CaptionStyle, ToneOption } from "@/types";
import { CharacterCounter } from "./CharacterCounter";

interface CaptionEditorProps {
  caption: string;
  hashtags: string[];
  selectedStyle: CaptionStyle;
  currentTone: ToneOption | null;
  onCaptionChange: (text: string) => void;
  onHashtagsChange: (tags: string[]) => void;
  onRegenerateHashtags: () => void;
  onChangeTone: (tone: ToneOption) => void;
  onSuggestEmojis: () => void;
  onValidate: () => void;
  onBack: () => void;
  isRegeneratingHashtags: boolean;
  isChangingTone: boolean;
  isSuggestingEmojis: boolean;
  platform: string;
}

const TONE_OPTIONS: { value: ToneOption; label: string; emoji: string }[] = [
  { value: "fun", label: "Fun", emoji: "🎉" },
  { value: "premium", label: "Premium", emoji: "✨" },
  { value: "urgence", label: "Urgence", emoji: "⚡" },
];

const STYLE_LABELS: Record<CaptionStyle, string> = {
  gourmande: "Gourmande",
  promo: "Promo",
  story: "Story",
};

export function CaptionEditor({
  caption,
  hashtags,
  selectedStyle,
  currentTone,
  onCaptionChange,
  onHashtagsChange,
  onRegenerateHashtags,
  onChangeTone,
  onSuggestEmojis,
  onValidate,
  onBack,
  isRegeneratingHashtags,
  isChangingTone,
  isSuggestingEmojis,
  platform,
}: CaptionEditorProps) {
  const removeHashtag = (index: number) => {
    onHashtagsChange(hashtags.filter((_, i) => i !== index));
  };

  const isAnyLoading = isRegeneratingHashtags || isChangingTone || isSuggestingEmojis;

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="space-y-5"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Retour
        </button>
        <span className="text-xs text-muted-foreground">
          Edition — Style {STYLE_LABELS[selectedStyle]}
        </span>
      </div>

      {/* Caption textarea */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Caption
          </label>
          <CharacterCounter text={caption} platform={platform} />
        </div>
        <textarea
          value={caption}
          onChange={(e) => onCaptionChange(e.target.value)}
          rows={8}
          className="w-full rounded-xl border border-border bg-background p-4 text-sm text-foreground resize-none focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
          placeholder="Ecris ta caption..."
        />
      </div>

      {/* Tone selector */}
      <div className="space-y-2">
        <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Changer le ton
        </label>
        <div className="flex gap-2">
          {TONE_OPTIONS.map((tone) => (
            <button
              key={tone.value}
              onClick={() => onChangeTone(tone.value)}
              disabled={isChangingTone}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                currentTone === tone.value
                  ? "bg-primary text-primary-foreground shadow-md"
                  : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
              } disabled:opacity-50`}
            >
              <span>{tone.emoji}</span>
              {tone.label}
              {isChangingTone && currentTone === tone.value && (
                <RefreshCw className="w-3 h-3 animate-spin ml-1" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Hashtags */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Hashtags ({hashtags.length})
          </label>
          <button
            onClick={onRegenerateHashtags}
            disabled={isRegeneratingHashtags}
            className="flex items-center gap-1 text-xs text-primary hover:text-primary/80 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3 h-3 ${isRegeneratingHashtags ? "animate-spin" : ""}`} />
            Regenerer
          </button>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {hashtags.map((tag, i) => (
            <motion.span
              key={`${tag}-${i}`}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-primary/10 text-primary text-xs"
            >
              <Hash className="w-3 h-3" />
              {tag.replace(/^#/, "")}
              <button
                onClick={() => removeHashtag(i)}
                className="hover:text-destructive transition-colors ml-0.5"
              >
                <X className="w-3 h-3" />
              </button>
            </motion.span>
          ))}
        </div>
      </div>

      {/* Emoji suggestion */}
      <button
        onClick={onSuggestEmojis}
        disabled={isSuggestingEmojis}
        className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border border-dashed border-border text-sm text-muted-foreground hover:text-foreground hover:border-border/80 transition-all disabled:opacity-50"
      >
        <Smile className={`w-4 h-4 ${isSuggestingEmojis ? "animate-bounce" : ""}`} />
        {isSuggestingEmojis ? "Suggestion en cours..." : "Suggerer des emojis"}
      </button>

      {/* Validate button */}
      <motion.button
        onClick={onValidate}
        disabled={isAnyLoading || !caption.trim()}
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        className="w-full py-3 rounded-xl bg-gradient-to-r from-primary to-primary/80 text-primary-foreground font-semibold text-sm flex items-center justify-center gap-2 disabled:opacity-50 transition-all shadow-lg hover:shadow-xl"
      >
        <Check className="w-4 h-4" />
        Valider et previsualiser
      </motion.button>
    </motion.div>
  );
}

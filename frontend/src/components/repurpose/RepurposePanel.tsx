"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Repeat2,
  Copy,
  CheckCircle2,
  Loader2,
  Instagram,
  Facebook,
  Linkedin,
  Smartphone,
  MapPin,
  Film,
  ImageIcon,
} from "lucide-react";
import { repurposeApi } from "@/lib/api";

interface Variant {
  id: string;
  format: string;
  label: string;
  caption: string;
  hashtags: string[];
  hashtag_text: string;
  suggested_cta: string;
  media_urls: string[];
  crop_spec: { aspect_ratio: string; resolution: string };
  tone: string;
  platform_tips: string;
}

interface ContentPackage {
  id: string;
  brand_id: string;
  original: {
    caption: string;
    hashtags: string[];
    media_urls: string[];
  };
  variants: Variant[];
  variant_count: number;
  created_at: string;
}

interface RepurposePanelProps {
  brandId: string;
  caption?: string;
  hashtags?: string[];
  mediaUrls?: string[];
  onUseVariant?: (variant: Variant) => void;
}

const FORMAT_ICONS: Record<string, typeof Instagram> = {
  instagram_post: Instagram,
  instagram_reel: Film,
  instagram_story: ImageIcon,
  tiktok: Smartphone,
  facebook: Facebook,
  gbp: MapPin,
  linkedin: Linkedin,
};

const FORMAT_COLORS: Record<string, string> = {
  instagram_post: "border-pink-500/40 bg-pink-500/10 text-pink-400",
  instagram_reel: "border-purple-500/40 bg-purple-500/10 text-purple-400",
  instagram_story: "border-orange-500/40 bg-orange-500/10 text-orange-400",
  tiktok: "border-cyan-500/40 bg-cyan-500/10 text-cyan-400",
  facebook: "border-blue-500/40 bg-blue-500/10 text-blue-400",
  gbp: "border-emerald-500/40 bg-emerald-500/10 text-emerald-400",
  linkedin: "border-sky-500/40 bg-sky-500/10 text-sky-400",
};

function VariantCard({
  variant,
  onUse,
}: {
  variant: Variant;
  onUse?: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const Icon = FORMAT_ICONS[variant.format] || Repeat2;
  const colorClass = FORMAT_COLORS[variant.format] || "border-zinc-700 bg-zinc-800/50 text-zinc-400";

  const handleCopy = async () => {
    const fullText = variant.caption +
      (variant.hashtag_text ? `\n\n${variant.hashtag_text}` : "") +
      (variant.suggested_cta ? `\n\n${variant.suggested_cta}` : "");
    await navigator.clipboard.writeText(fullText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`border rounded-xl p-4 space-y-3 ${colorClass.split(" ").slice(0, 2).join(" ")}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className={`w-4 h-4 ${colorClass.split(" ")[2]}`} />
          <span className="text-sm font-semibold text-zinc-100">{variant.label}</span>
        </div>
        <span className="text-[10px] text-zinc-500 font-mono">
          {variant.crop_spec.aspect_ratio}
        </span>
      </div>

      {/* Caption preview */}
      <div className="bg-zinc-900/60 rounded-lg p-3 space-y-2">
        <p className="text-sm text-zinc-200 leading-relaxed">{variant.caption}</p>
        {variant.hashtag_text && (
          <p className="text-xs text-amber-400/70">{variant.hashtag_text}</p>
        )}
        {variant.suggested_cta && (
          <p className="text-xs text-zinc-500 italic">CTA : {variant.suggested_cta}</p>
        )}
      </div>

      {/* Tips */}
      <p className="text-[10px] text-zinc-600">{variant.platform_tips}</p>

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={handleCopy}
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg border border-zinc-700 text-zinc-300 text-xs hover:bg-zinc-800 transition-colors"
        >
          {copied ? (
            <>
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              Copie !
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              Copier
            </>
          )}
        </button>
        {onUse && (
          <button
            onClick={onUse}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-black text-xs font-medium transition-colors"
          >
            Utiliser
          </button>
        )}
      </div>
    </motion.div>
  );
}

export function RepurposePanel({
  brandId,
  caption = "",
  hashtags = [],
  mediaUrls = [],
  onUseVariant,
}: RepurposePanelProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [contentPackage, setContentPackage] = useState<ContentPackage | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRepurpose = async () => {
    if (!caption.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await repurposeApi.repurpose({
        brand_id: brandId,
        caption,
        hashtags,
        media_urls: mediaUrls,
      });
      setContentPackage(response.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Erreur lors du repurposing");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-zinc-900/80 border border-zinc-800 rounded-2xl p-5 space-y-4"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Repeat2 className="w-5 h-5 text-amber-400" />
          <h3 className="text-sm font-semibold text-zinc-100">
            Content Repurposing
          </h3>
        </div>
        {contentPackage && (
          <span className="text-xs text-zinc-500">
            {contentPackage.variant_count} variantes generees
          </span>
        )}
      </div>

      {/* Generate button */}
      {!contentPackage && (
        <>
          <p className="text-xs text-zinc-500">
            Transformez votre contenu en 7 formats adaptes a chaque plateforme.
          </p>
          <button
            onClick={handleRepurpose}
            disabled={isLoading || !caption.trim()}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-medium text-sm transition-colors disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Generation en cours...
              </>
            ) : (
              <>
                <Repeat2 className="w-4 h-4" />
                Generer 7 variantes
              </>
            )}
          </button>
        </>
      )}

      {/* Error */}
      {error && (
        <div className="text-sm text-red-400 bg-red-900/20 border border-red-800/40 rounded-lg px-3 py-2">
          {error}
        </div>
      )}

      {/* Variants grid */}
      <AnimatePresence>
        {contentPackage && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="grid grid-cols-1 md:grid-cols-2 gap-3"
          >
            {contentPackage.variants.map((variant) => (
              <VariantCard
                key={variant.id}
                variant={variant}
                onUse={onUseVariant ? () => onUseVariant(variant) : undefined}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Reset */}
      {contentPackage && (
        <button
          onClick={() => setContentPackage(null)}
          className="w-full text-xs text-zinc-500 hover:text-zinc-300 py-2 transition-colors"
        >
          Recommencer avec un autre contenu
        </button>
      )}
    </motion.div>
  );
}

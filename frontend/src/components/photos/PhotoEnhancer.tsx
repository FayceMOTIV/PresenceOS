"use client";

import { useState, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Camera,
  Sparkles,
  CheckCircle2,
  Loader2,
  ChevronLeft,
  ChevronRight,
  Image as ImageIcon,
  Utensils,
  ShoppingBag,
  Smartphone,
} from "lucide-react";
import { photosApi } from "@/lib/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface QualityScore {
  score: number;
  level: string;
  brightness: number;
  contrast: number;
  color_richness: number;
  resolution: number;
  recommendation: string;
}

interface EnhanceResult {
  id: string;
  original_url: string;
  enhanced_url: string;
  style: string;
  quality_before: QualityScore;
  quality_after: QualityScore;
  improvement: number;
}

const STYLES = [
  {
    id: "instagram",
    label: "Instagram",
    description: "Chaud, lifestyle",
    icon: Camera,
  },
  {
    id: "delivery",
    label: "Livraison",
    description: "Net, neutre",
    icon: ShoppingBag,
  },
  {
    id: "menu",
    label: "Menu",
    description: "Pro, detaille",
    icon: Utensils,
  },
  {
    id: "story",
    label: "Story",
    description: "Vibrant, vertical",
    icon: Smartphone,
  },
];

function QualityBadge({ score, level }: { score: number; level: string }) {
  const color =
    level === "excellent"
      ? "text-emerald-400 bg-emerald-900/30 border-emerald-700/50"
      : level === "good"
        ? "text-amber-400 bg-amber-900/30 border-amber-700/50"
        : "text-red-400 bg-red-900/30 border-red-700/50";
  const label =
    level === "excellent"
      ? "Excellente"
      : level === "good"
        ? "Bonne"
        : "A ameliorer";

  return (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium ${color}`}>
      <Camera className="w-3 h-3" />
      <span>Qualite : {label}</span>
      <span className="opacity-70">({score}/100)</span>
    </div>
  );
}

function CompareSlider({
  originalUrl,
  enhancedUrl,
}: {
  originalUrl: string;
  enhancedUrl: string;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [sliderPos, setSliderPos] = useState(50);
  const [isDragging, setIsDragging] = useState(false);

  const handleMove = useCallback(
    (clientX: number) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const x = clientX - rect.left;
      const pct = Math.max(0, Math.min(100, (x / rect.width) * 100));
      setSliderPos(pct);
    },
    []
  );

  return (
    <div
      ref={containerRef}
      className="relative w-full aspect-square rounded-xl overflow-hidden cursor-col-resize select-none bg-gray-50"
      onMouseDown={() => setIsDragging(true)}
      onMouseUp={() => setIsDragging(false)}
      onMouseLeave={() => setIsDragging(false)}
      onMouseMove={(e) => isDragging && handleMove(e.clientX)}
      onTouchMove={(e) => handleMove(e.touches[0].clientX)}
    >
      {/* Enhanced (full) */}
      <img
        src={`${API_BASE_URL}${enhancedUrl}`}
        alt="Amelioree"
        className="absolute inset-0 w-full h-full object-cover"
        draggable={false}
      />
      {/* Original (clipped) */}
      <div
        className="absolute inset-0 overflow-hidden"
        style={{ width: `${sliderPos}%` }}
      >
        <img
          src={`${API_BASE_URL}${originalUrl}`}
          alt="Original"
          className="absolute inset-0 w-full h-full object-cover"
          style={{ minWidth: containerRef.current?.offsetWidth }}
          draggable={false}
        />
      </div>
      {/* Slider line */}
      <div
        className="absolute top-0 bottom-0 w-0.5 bg-white/80 z-10"
        style={{ left: `${sliderPos}%` }}
      >
        <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-white/90 border-2 border-gray-300 flex items-center justify-center shadow-lg">
          <ChevronLeft className="w-3 h-3 text-gray-800" />
          <ChevronRight className="w-3 h-3 text-gray-800" />
        </div>
      </div>
      {/* Labels */}
      <div className="absolute top-3 left-3 px-2 py-0.5 rounded bg-black/60 text-white text-xs">
        Original
      </div>
      <div className="absolute top-3 right-3 px-2 py-0.5 rounded bg-amber-500/80 text-white text-xs">
        Amelioree
      </div>
    </div>
  );
}

interface PhotoEnhancerProps {
  file?: File;
  onUseEnhanced?: (enhancedUrl: string) => void;
  onDismiss?: () => void;
}

export function PhotoEnhancer({ file, onUseEnhanced, onDismiss }: PhotoEnhancerProps) {
  const [selectedStyle, setSelectedStyle] = useState("instagram");
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [result, setResult] = useState<EnhanceResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // Generate local preview when file changes
  useState(() => {
    if (file) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      return () => URL.revokeObjectURL(url);
    }
  });

  const handleEnhance = async () => {
    if (!file) return;
    setIsEnhancing(true);
    setError(null);
    try {
      const response = await photosApi.enhance(file, selectedStyle);
      setResult(response.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Erreur lors de l'enhancement");
    } finally {
      setIsEnhancing(false);
    }
  };

  const handleUse = () => {
    if (result && onUseEnhanced) {
      onUseEnhanced(`${API_BASE_URL}${result.enhanced_url}`);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white border border-gray-200/60 rounded-2xl p-5 space-y-4 shadow-sm"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-amber-400" />
          <h3 className="text-sm font-semibold text-gray-900">
            Photo Enhancement IA
          </h3>
        </div>
        {result && (
          <QualityBadge
            score={result.quality_after.score}
            level={result.quality_after.level}
          />
        )}
        {!result && file && (
          <button
            onClick={onDismiss}
            className="text-xs text-gray-500 hover:text-gray-800 transition-colors"
          >
            Ignorer
          </button>
        )}
      </div>

      {/* Style selector */}
      {!result && (
        <div className="grid grid-cols-4 gap-2">
          {STYLES.map((style) => {
            const Icon = style.icon;
            const active = selectedStyle === style.id;
            return (
              <button
                key={style.id}
                onClick={() => setSelectedStyle(style.id)}
                className={`flex flex-col items-center gap-1 p-3 rounded-xl border transition-all text-xs ${
                  active
                    ? "border-amber-500/60 bg-amber-500/10 text-amber-400"
                    : "border-gray-200/60 bg-gray-100/60 text-gray-600 hover:bg-gray-100"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="font-medium">{style.label}</span>
                <span className="text-[10px] opacity-60">{style.description}</span>
              </button>
            );
          })}
        </div>
      )}

      {/* Preview / Comparison */}
      {result ? (
        <CompareSlider
          originalUrl={result.original_url}
          enhancedUrl={result.enhanced_url}
        />
      ) : (
        previewUrl && (
          <div className="relative aspect-square rounded-xl overflow-hidden bg-gray-100">
            <img
              src={previewUrl}
              alt="Preview"
              className="w-full h-full object-cover"
            />
          </div>
        )
      )}

      {/* Improvement stats */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="grid grid-cols-3 gap-3"
          >
            {[
              { label: "Avant", value: result.quality_before.score },
              { label: "Apres", value: result.quality_after.score },
              { label: "Gain", value: `+${result.improvement}` },
            ].map((stat) => (
              <div
                key={stat.label}
                className="bg-gray-100/60 rounded-lg p-2.5 text-center"
              >
                <div className="text-lg font-bold text-gray-900">{stat.value}</div>
                <div className="text-[10px] text-gray-500 uppercase">{stat.label}</div>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error */}
      {error && (
        <div className="text-sm text-red-400 bg-red-900/20 border border-red-800/40 rounded-lg px-3 py-2">
          {error}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        {!result ? (
          <button
            onClick={handleEnhance}
            disabled={isEnhancing || !file}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-400 hover:from-amber-400 hover:to-amber-300 text-black font-medium text-sm transition-colors disabled:opacity-50"
          >
            {isEnhancing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Enhancement en cours...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Ameliorer la photo
              </>
            )}
          </button>
        ) : (
          <>
            <button
              onClick={handleUse}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-400 hover:from-amber-400 hover:to-amber-300 text-black font-medium text-sm transition-colors"
            >
              <CheckCircle2 className="w-4 h-4" />
              Utiliser cette version
            </button>
            <button
              onClick={() => setResult(null)}
              className="px-4 py-2.5 rounded-xl border border-gray-200 text-gray-800 text-sm hover:bg-gray-100 transition-colors"
            >
              Recommencer
            </button>
          </>
        )}
      </div>
    </motion.div>
  );
}

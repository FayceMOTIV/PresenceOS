"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Clock,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Zap,
  Calendar,
  Loader2,
  Instagram,
  Facebook,
  Linkedin,
} from "lucide-react";
import { schedulingApi } from "@/lib/api";

interface TimeSlot {
  datetime: string;
  day: string;
  day_label: string;
  hour: number;
  hour_label: string;
  score: number;
  platform: string;
}

interface SchedulePickerProps {
  brandId: string;
  platform?: string;
  timezoneOffset?: number;
  onSelect?: (slot: TimeSlot) => void;
  onManualSelect?: (datetime: string) => void;
  compact?: boolean;
}

const PLATFORM_ICONS: Record<string, typeof Instagram> = {
  instagram: Instagram,
  facebook: Facebook,
  linkedin: Linkedin,
};

const PLATFORM_OPTIONS = [
  { id: "instagram", label: "Instagram" },
  { id: "tiktok", label: "TikTok" },
  { id: "facebook", label: "Facebook" },
  { id: "linkedin", label: "LinkedIn" },
];

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 85
      ? "text-emerald-400 bg-emerald-900/30 border-emerald-700/50"
      : score >= 70
        ? "text-amber-400 bg-amber-900/30 border-amber-700/50"
        : "text-zinc-400 bg-zinc-800/50 border-zinc-700/50";
  const label = score >= 85 ? "Optimal" : score >= 70 ? "Bon" : "Moyen";

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[10px] font-semibold uppercase ${color}`}
    >
      <Zap className="w-2.5 h-2.5" />
      {label} {score}
    </span>
  );
}

function SlotCard({
  slot,
  isSelected,
  onSelect,
}: {
  slot: TimeSlot;
  isSelected: boolean;
  onSelect: () => void;
}) {
  return (
    <motion.button
      onClick={onSelect}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`w-full flex items-center gap-3 p-3 rounded-xl border transition-all text-left ${
        isSelected
          ? "border-amber-500/60 bg-amber-500/10 ring-1 ring-amber-500/30"
          : "border-zinc-800 bg-zinc-800/40 hover:border-zinc-700 hover:bg-zinc-800/60"
      }`}
    >
      {/* Time */}
      <div className="flex-shrink-0 w-14 text-center">
        <div className={`text-lg font-bold ${isSelected ? "text-amber-400" : "text-zinc-100"}`}>
          {slot.hour_label}
        </div>
      </div>

      {/* Day + Score */}
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-zinc-200 truncate">
          {slot.day_label}
        </div>
        <div className="text-xs text-zinc-500">
          {new Date(slot.datetime).toLocaleDateString("fr-FR", {
            day: "numeric",
            month: "short",
          })}
        </div>
      </div>

      {/* Score badge */}
      <ScoreBadge score={slot.score} />
    </motion.button>
  );
}

export function SchedulePicker({
  brandId,
  platform = "instagram",
  timezoneOffset = 1,
  onSelect,
  onManualSelect,
  compact = false,
}: SchedulePickerProps) {
  const [slots, setSlots] = useState<TimeSlot[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<TimeSlot | null>(null);
  const [activePlatform, setActivePlatform] = useState(platform);
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(!compact);
  const [error, setError] = useState<string | null>(null);

  const fetchOptimalTimes = useCallback(async () => {
    if (!brandId) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await schedulingApi.getOptimalTimes(
        brandId,
        activePlatform,
        compact ? 3 : 7,
        timezoneOffset
      );
      setSlots(response.data || []);
    } catch (err: any) {
      setError("Impossible de charger les creneaux optimaux");
      console.error("Error fetching optimal times:", err);
    } finally {
      setIsLoading(false);
    }
  }, [brandId, activePlatform, timezoneOffset, compact]);

  useEffect(() => {
    fetchOptimalTimes();
  }, [fetchOptimalTimes]);

  const handleSlotSelect = (slot: TimeSlot) => {
    setSelectedSlot(slot);
    onSelect?.(slot);
  };

  // Next optimal slot (first in the sorted list)
  const nextOptimal = slots[0] || null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-zinc-900/80 border border-zinc-800 rounded-2xl overflow-hidden"
    >
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-zinc-800/30 transition-colors"
      >
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-left">
            <h3 className="text-sm font-semibold text-zinc-100">
              Smart Scheduling
            </h3>
            {nextOptimal && !isExpanded && (
              <p className="text-xs text-zinc-500">
                Prochain creneau : {nextOptimal.day_label} a {nextOptimal.hour_label}{" "}
                (score {nextOptimal.score})
              </p>
            )}
          </div>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-zinc-500" />
        ) : (
          <ChevronDown className="w-4 h-4 text-zinc-500" />
        )}
      </button>

      {/* Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-3">
              {/* Platform selector */}
              <div className="flex gap-1.5">
                {PLATFORM_OPTIONS.map((p) => {
                  const Icon = PLATFORM_ICONS[p.id] || Clock;
                  const active = activePlatform === p.id;
                  return (
                    <button
                      key={p.id}
                      onClick={() => setActivePlatform(p.id)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                        active
                          ? "bg-amber-500/15 text-amber-400 border border-amber-500/40"
                          : "bg-zinc-800/50 text-zinc-400 border border-zinc-800 hover:border-zinc-700"
                      }`}
                    >
                      <Icon className="w-3 h-3" />
                      {p.label}
                    </button>
                  );
                })}
              </div>

              {/* Loading */}
              {isLoading && (
                <div className="flex items-center justify-center py-6">
                  <Loader2 className="w-5 h-5 animate-spin text-amber-400" />
                  <span className="ml-2 text-xs text-zinc-500">
                    Analyse des meilleurs creneaux...
                  </span>
                </div>
              )}

              {/* Error */}
              {error && (
                <div className="text-sm text-red-400 bg-red-900/20 border border-red-800/40 rounded-lg px-3 py-2">
                  {error}
                </div>
              )}

              {/* Time slots */}
              {!isLoading && !error && (
                <div className="space-y-2">
                  {slots.map((slot, i) => (
                    <SlotCard
                      key={`${slot.datetime}-${i}`}
                      slot={slot}
                      isSelected={selectedSlot?.datetime === slot.datetime}
                      onSelect={() => handleSlotSelect(slot)}
                    />
                  ))}
                </div>
              )}

              {/* Empty state */}
              {!isLoading && !error && slots.length === 0 && (
                <div className="text-center py-4">
                  <Calendar className="w-8 h-8 text-zinc-600 mx-auto mb-2" />
                  <p className="text-xs text-zinc-500">
                    Aucun creneau disponible pour cette plateforme
                  </p>
                </div>
              )}

              {/* Use selected slot button */}
              {selectedSlot && (
                <motion.div
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="pt-1"
                >
                  <button
                    onClick={() => onManualSelect?.(selectedSlot.datetime)}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-medium text-sm transition-colors"
                  >
                    <Clock className="w-4 h-4" />
                    Planifier pour {selectedSlot.day_label} a {selectedSlot.hour_label}
                  </button>
                </motion.div>
              )}

              {/* Methodology note */}
              <p className="text-[10px] text-zinc-600 text-center pt-1">
                Bases sur les benchmarks Sprout Social / Later 2025 pour la restauration
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

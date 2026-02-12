"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Clock, Sparkles, Zap } from "lucide-react";
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

interface OptimalTimesWidgetProps {
  brandId: string;
  platform?: string;
  onSlotClick?: (slot: TimeSlot) => void;
}

export function OptimalTimesWidget({
  brandId,
  platform = "instagram",
  onSlotClick,
}: OptimalTimesWidgetProps) {
  const [nextSlot, setNextSlot] = useState<TimeSlot | null>(null);
  const [topSlots, setTopSlots] = useState<TimeSlot[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!brandId) return;

    const fetchData = async () => {
      setIsLoading(true);
      try {
        const [nextRes, topRes] = await Promise.all([
          schedulingApi.getNextOptimal(brandId, platform),
          schedulingApi.getOptimalTimes(brandId, platform, 3),
        ]);
        setNextSlot(nextRes.data);
        setTopSlots(topRes.data || []);
      } catch (err) {
        console.error("Error fetching optimal times:", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [brandId, platform]);

  if (isLoading) {
    return (
      <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4 animate-pulse">
        <div className="h-4 bg-zinc-800 rounded w-32 mb-3" />
        <div className="h-10 bg-zinc-800 rounded mb-2" />
        <div className="h-6 bg-zinc-800 rounded w-24" />
      </div>
    );
  }

  if (!nextSlot) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4 space-y-3"
    >
      <div className="flex items-center gap-2">
        <Sparkles className="w-4 h-4 text-amber-400" />
        <h4 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">
          Prochain creneau optimal
        </h4>
      </div>

      {/* Next slot highlight */}
      <button
        onClick={() => onSlotClick?.(nextSlot)}
        className="w-full flex items-center gap-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 hover:bg-amber-500/15 transition-colors text-left"
      >
        <div className="w-10 h-10 rounded-lg bg-amber-500/20 flex items-center justify-center">
          <Clock className="w-5 h-5 text-amber-400" />
        </div>
        <div className="flex-1">
          <div className="text-sm font-bold text-amber-400">
            {nextSlot.day_label} a {nextSlot.hour_label}
          </div>
          <div className="text-xs text-zinc-500">
            {new Date(nextSlot.datetime).toLocaleDateString("fr-FR", {
              day: "numeric",
              month: "long",
            })}
          </div>
        </div>
        <div className="flex items-center gap-1 px-2 py-1 rounded-full bg-amber-500/20 text-amber-400 text-xs font-bold">
          <Zap className="w-3 h-3" />
          {nextSlot.score}
        </div>
      </button>

      {/* Other slots */}
      {topSlots.length > 1 && (
        <div className="space-y-1.5">
          <p className="text-[10px] text-zinc-600 uppercase tracking-wider">
            Autres creneaux
          </p>
          {topSlots.slice(1).map((slot, i) => (
            <button
              key={`${slot.datetime}-${i}`}
              onClick={() => onSlotClick?.(slot)}
              className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-zinc-800/40 hover:bg-zinc-800/60 border border-zinc-800 transition-colors text-left"
            >
              <span className="text-xs text-zinc-300">
                {slot.day_label} a {slot.hour_label}
              </span>
              <span className="text-[10px] text-zinc-500 font-medium">
                {slot.score}/100
              </span>
            </button>
          ))}
        </div>
      )}
    </motion.div>
  );
}

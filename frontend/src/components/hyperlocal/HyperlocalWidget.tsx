"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Cloud,
  Sun,
  CloudRain,
  Snowflake,
  Calendar,
  Leaf,
  Lightbulb,
  Loader2,
  MapPin,
  Clock,
} from "lucide-react";
import { hyperlocalApi } from "@/lib/api";

interface WeatherData {
  condition: string;
  temp: number;
  icon: string;
  tip: string;
}

interface EventData {
  name: string;
  type: string;
  date: string;
  distance_km: number;
  tip: string;
}

interface SeasonalData {
  season: string;
  trending_ingredients: string[];
  content_themes: string[];
  tip: string;
}

interface Suggestion {
  type: string;
  priority: string;
  title: string;
  suggestion: string;
  best_time: string;
  platforms: string[];
}

interface HyperlocalContext {
  weather: WeatherData;
  events: EventData[];
  seasonal: SeasonalData;
  day_context: { label: string; tip: string; best_format: string };
  suggestions: Suggestion[];
}

interface HyperlocalWidgetProps {
  brandId: string;
}

const WEATHER_ICONS: Record<string, typeof Sun> = {
  sun: Sun,
  cloud: Cloud,
  rain: CloudRain,
  snow: Snowflake,
};

const PRIORITY_COLORS: Record<string, string> = {
  high: "border-amber-500/40 bg-amber-500/5",
  medium: "border-zinc-700 bg-zinc-800/30",
  low: "border-zinc-800 bg-zinc-900/30",
};

const TYPE_ICONS: Record<string, typeof Sun> = {
  weather: Cloud,
  event: Calendar,
  seasonal: Leaf,
  day: Clock,
};

export function HyperlocalWidget({ brandId }: HyperlocalWidgetProps) {
  const [context, setContext] = useState<HyperlocalContext | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!brandId) return;
    setIsLoading(true);
    hyperlocalApi
      .getContext(brandId)
      .then((res) => setContext(res.data))
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [brandId]);

  if (isLoading) {
    return (
      <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-6 flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-zinc-500" />
      </div>
    );
  }

  if (!context) return null;

  const WeatherIcon = WEATHER_ICONS[context.weather.icon] || Cloud;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-zinc-900/80 border border-zinc-800 rounded-2xl overflow-hidden"
    >
      {/* Header with weather */}
      <div className="p-5 border-b border-zinc-800">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <MapPin className="w-5 h-5 text-amber-400" />
            <h3 className="text-sm font-semibold text-zinc-100">Intelligence locale</h3>
          </div>
          <div className="flex items-center gap-2">
            <WeatherIcon className="w-5 h-5 text-amber-400" />
            <span className="text-sm font-bold text-zinc-100">{context.weather.temp}°C</span>
            <span className="text-xs text-zinc-500">{context.weather.condition}</span>
          </div>
        </div>
        <p className="text-xs text-zinc-400">{context.weather.tip}</p>
      </div>

      <div className="p-5 space-y-4">
        {/* Seasonal context */}
        <div className="bg-zinc-800/30 border border-zinc-800 rounded-xl p-3 space-y-2">
          <div className="flex items-center gap-2">
            <Leaf className="w-4 h-4 text-emerald-400" />
            <span className="text-xs font-semibold text-zinc-200 capitalize">
              Saison : {context.seasonal.season}
            </span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {context.seasonal.trending_ingredients.map((ing) => (
              <span
                key={ing}
                className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[10px]"
              >
                {ing}
              </span>
            ))}
          </div>
          <p className="text-[10px] text-zinc-500">{context.seasonal.tip}</p>
        </div>

        {/* Events */}
        {context.events.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
              Evenements proches
            </h4>
            {context.events.map((event, i) => (
              <div
                key={i}
                className="flex items-start gap-3 bg-zinc-800/30 border border-zinc-800 rounded-lg p-3"
              >
                <Calendar className="w-4 h-4 text-zinc-500 flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-zinc-200 truncate">{event.name}</span>
                    <span className="text-[10px] text-zinc-600">{event.distance_km} km</span>
                  </div>
                  <p className="text-[10px] text-zinc-500 mt-0.5">{event.tip}</p>
                  <p className="text-[10px] text-zinc-600 mt-0.5">
                    {new Date(event.date).toLocaleDateString("fr-FR", { day: "numeric", month: "short" })}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Content suggestions */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Lightbulb className="w-4 h-4 text-amber-400" />
            <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
              Suggestions du jour
            </h4>
          </div>
          {context.suggestions.map((suggestion, i) => {
            const SuggIcon = TYPE_ICONS[suggestion.type] || Lightbulb;
            const borderColor = PRIORITY_COLORS[suggestion.priority] || PRIORITY_COLORS.medium;
            return (
              <div key={i} className={`border rounded-lg p-3 space-y-1 ${borderColor}`}>
                <div className="flex items-center gap-2">
                  <SuggIcon className="w-3 h-3 text-zinc-500" />
                  <span className="text-xs font-medium text-zinc-200">{suggestion.title}</span>
                  <span className="ml-auto text-[10px] text-zinc-600">{suggestion.best_time}</span>
                </div>
                <p className="text-[10px] text-zinc-400">{suggestion.suggestion}</p>
              </div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}

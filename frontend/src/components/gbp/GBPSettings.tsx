"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  MapPin,
  Settings,
  ToggleLeft,
  ToggleRight,
  Send,
  Loader2,
  CheckCircle2,
  BarChart3,
} from "lucide-react";
import { gbpApi } from "@/lib/api";

interface GBPConfig {
  brand_id: string;
  enabled: boolean;
  location_id: string | null;
  auto_sync: boolean;
  default_post_type: string;
  default_cta: string;
  include_photos: boolean;
  include_offers: boolean;
  publish_frequency: string;
}

interface GBPStats {
  brand_id: string;
  total_published: number;
  this_month: number;
  post_types: Record<string, number>;
  last_published: string | null;
}

interface GBPSettingsProps {
  brandId: string;
}

const POST_TYPES = [
  { value: "WHATS_NEW", label: "Nouveaute" },
  { value: "EVENT", label: "Evenement" },
  { value: "OFFER", label: "Offre" },
];

const CTA_OPTIONS = [
  { value: "LEARN_MORE", label: "En savoir plus" },
  { value: "BOOK", label: "Reserver" },
  { value: "ORDER", label: "Commander" },
  { value: "CALL", label: "Appeler" },
  { value: "SIGN_UP", label: "S'inscrire" },
];

const FREQUENCIES = [
  { value: "daily", label: "Quotidien" },
  { value: "weekly", label: "Hebdomadaire" },
  { value: "biweekly", label: "Bi-mensuel" },
];

function Toggle({
  enabled,
  onToggle,
  label,
}: {
  enabled: boolean;
  onToggle: () => void;
  label: string;
}) {
  return (
    <button
      onClick={onToggle}
      className="flex items-center justify-between w-full py-2"
    >
      <span className="text-sm text-gray-800">{label}</span>
      {enabled ? (
        <ToggleRight className="w-6 h-6 text-amber-400" />
      ) : (
        <ToggleLeft className="w-6 h-6 text-gray-400" />
      )}
    </button>
  );
}

export function GBPSettings({ brandId }: GBPSettingsProps) {
  const [config, setConfig] = useState<GBPConfig | null>(null);
  const [stats, setStats] = useState<GBPStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!brandId) return;
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const [configRes, statsRes] = await Promise.all([
          gbpApi.getConfig(brandId),
          gbpApi.getStats(brandId),
        ]);
        setConfig(configRes.data);
        setStats(statsRes.data);
      } catch (err) {
        console.error("Error fetching GBP data:", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [brandId]);

  const handleToggleEnabled = async () => {
    if (!config) return;
    try {
      const res = await gbpApi.toggle(brandId);
      setConfig(res.data);
    } catch (err) {
      console.error("Error toggling GBP:", err);
    }
  };

  const handleUpdate = async (field: string, value: any) => {
    if (!config) return;
    setConfig({ ...config, [field]: value });
    setIsSaving(true);
    setSaved(false);
    try {
      await gbpApi.updateConfig(brandId, { [field]: value });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      console.error("Error updating GBP config:", err);
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white border border-gray-200/60 rounded-2xl p-6 flex items-center justify-center py-12 shadow-sm">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (!config) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white border border-gray-200/60 rounded-2xl overflow-hidden shadow-sm"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-5 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
            <MapPin className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900">
              Google Business Profile
            </h3>
            <p className="text-xs text-gray-500">
              Publication automatique sur votre fiche Google
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isSaving && <Loader2 className="w-3 h-3 animate-spin text-gray-400" />}
          {saved && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
        </div>
      </div>

      <div className="p-5 space-y-5">
        {/* Main toggle */}
        <div className="flex items-center justify-between p-3 rounded-xl bg-gray-100/60 border border-gray-200/60">
          <div className="flex items-center gap-2">
            <Settings className="w-4 h-4 text-gray-600" />
            <span className="text-sm font-medium text-gray-800">
              Autopublish active
            </span>
          </div>
          <button onClick={handleToggleEnabled}>
            {config.enabled ? (
              <ToggleRight className="w-7 h-7 text-emerald-400" />
            ) : (
              <ToggleLeft className="w-7 h-7 text-gray-400" />
            )}
          </button>
        </div>

        {/* Config options */}
        <div className="space-y-3">
          {/* Location ID */}
          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wider mb-1 block">
              Location ID (Google)
            </label>
            <input
              type="text"
              value={config.location_id || ""}
              onChange={(e) => handleUpdate("location_id", e.target.value || null)}
              placeholder="accounts/xxx/locations/yyy"
              className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800 placeholder:text-gray-400 focus:border-amber-500/50 focus:outline-none"
            />
          </div>

          {/* Default post type */}
          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wider mb-1 block">
              Type de post par defaut
            </label>
            <div className="flex gap-2">
              {POST_TYPES.map((pt) => (
                <button
                  key={pt.value}
                  onClick={() => handleUpdate("default_post_type", pt.value)}
                  className={`flex-1 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                    config.default_post_type === pt.value
                      ? "bg-amber-500/15 text-amber-400 border border-amber-500/40"
                      : "bg-gray-100/60 text-gray-600 border border-gray-200/60 hover:bg-gray-100"
                  }`}
                >
                  {pt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Default CTA */}
          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wider mb-1 block">
              Bouton d&apos;action
            </label>
            <div className="flex flex-wrap gap-2">
              {CTA_OPTIONS.map((cta) => (
                <button
                  key={cta.value}
                  onClick={() => handleUpdate("default_cta", cta.value)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    config.default_cta === cta.value
                      ? "bg-amber-500/15 text-amber-400 border border-amber-500/40"
                      : "bg-gray-100/60 text-gray-600 border border-gray-200/60 hover:bg-gray-100"
                  }`}
                >
                  {cta.label}
                </button>
              ))}
            </div>
          </div>

          {/* Frequency */}
          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wider mb-1 block">
              Frequence de publication
            </label>
            <div className="flex gap-2">
              {FREQUENCIES.map((f) => (
                <button
                  key={f.value}
                  onClick={() => handleUpdate("publish_frequency", f.value)}
                  className={`flex-1 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                    config.publish_frequency === f.value
                      ? "bg-amber-500/15 text-amber-400 border border-amber-500/40"
                      : "bg-gray-100/60 text-gray-600 border border-gray-200/60 hover:bg-gray-100"
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* Toggles */}
          <div className="border-t border-gray-200 pt-3 space-y-1">
            <Toggle
              enabled={config.auto_sync}
              onToggle={() => handleUpdate("auto_sync", !config.auto_sync)}
              label="Sync automatique"
            />
            <Toggle
              enabled={config.include_photos}
              onToggle={() => handleUpdate("include_photos", !config.include_photos)}
              label="Inclure les photos"
            />
            <Toggle
              enabled={config.include_offers}
              onToggle={() => handleUpdate("include_offers", !config.include_offers)}
              label="Inclure les offres"
            />
          </div>
        </div>

        {/* Stats */}
        {stats && (
          <div className="border-t border-gray-200 pt-4">
            <div className="flex items-center gap-2 mb-3">
              <BarChart3 className="w-4 h-4 text-gray-500" />
              <span className="text-xs text-gray-500 uppercase tracking-wider">
                Statistiques GBP
              </span>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-gray-100/60 rounded-lg p-3 text-center">
                <div className="text-lg font-bold text-gray-900">{stats.total_published}</div>
                <div className="text-[10px] text-gray-500 uppercase">Total</div>
              </div>
              <div className="bg-gray-100/60 rounded-lg p-3 text-center">
                <div className="text-lg font-bold text-gray-900">{stats.this_month}</div>
                <div className="text-[10px] text-gray-500 uppercase">Ce mois</div>
              </div>
              <div className="bg-gray-100/60 rounded-lg p-3 text-center">
                <div className="text-lg font-bold text-gray-900">
                  {stats.last_published
                    ? new Date(stats.last_published).toLocaleDateString("fr-FR", { day: "numeric", month: "short" })
                    : "—"}
                </div>
                <div className="text-[10px] text-gray-500 uppercase">Dernier</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}

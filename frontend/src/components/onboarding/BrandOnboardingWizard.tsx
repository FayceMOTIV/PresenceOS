"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  Check,
  Store,
  Sparkles,
  Users,
  Globe,
  Loader2,
} from "lucide-react";
import { brandsApi } from "@/lib/api";

interface BrandOnboardingWizardProps {
  brandId: string;
  onComplete: (brandData: any) => void;
}

type ToneVoice = "chaleureux" | "premium" | "fun" | "professionnel" | "inspirant";
type BusinessType = "restaurant" | "ecommerce" | "saas" | "service" | "personal";

const BUSINESS_TYPES: { value: BusinessType; label: string; icon: string }[] = [
  { value: "restaurant", label: "Restaurant / Cafe", icon: "🍽️" },
  { value: "ecommerce", label: "E-commerce", icon: "🛍️" },
  { value: "saas", label: "SaaS / Tech", icon: "💻" },
  { value: "service", label: "Service", icon: "🔧" },
  { value: "personal", label: "Personnel / Creator", icon: "👤" },
];

const TONE_OPTIONS: { value: ToneVoice; label: string; description: string }[] = [
  {
    value: "chaleureux",
    label: "Chaleureux",
    description: "Accueillant, empathique et proche",
  },
  {
    value: "premium",
    label: "Premium",
    description: "Elegant, sophistique et raffine",
  },
  {
    value: "fun",
    label: "Fun",
    description: "Dynamique, leger et divertissant",
  },
  {
    value: "professionnel",
    label: "Professionnel",
    description: "Serieux, credible et formel",
  },
  {
    value: "inspirant",
    label: "Inspirant",
    description: "Motivant, ambitieux et emotionnel",
  },
];

export function BrandOnboardingWizard({
  brandId,
  onComplete,
}: BrandOnboardingWizardProps) {
  const [step, setStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form data
  const [name, setName] = useState("");
  const [businessType, setBusinessType] = useState<BusinessType | "">("");
  const [toneVoice, setToneVoice] = useState<ToneVoice | "">("");
  const [targetAudience, setTargetAudience] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");

  const totalSteps = 5;

  const canProceed = () => {
    switch (step) {
      case 1:
        return name.trim().length > 0;
      case 2:
        return businessType !== "";
      case 3:
        return toneVoice !== "";
      case 4:
        return targetAudience.trim().length > 0;
      case 5:
        return true; // Website URL is optional
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (step < totalSteps && canProceed()) {
      setStep(step + 1);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  const handleComplete = async () => {
    if (!canProceed()) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const payload = {
        name,
        business_type: businessType,
        tone_voice: toneVoice,
        target_audience: targetAudience,
        website_url: websiteUrl || null,
      };

      const response = await brandsApi.onboard(brandId, payload);
      onComplete(response.data);
    } catch (err: any) {
      console.error("Onboarding error:", err);
      setError(err.response?.data?.detail || "Une erreur est survenue");
      setIsSubmitting(false);
    }
  };

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <motion.div
            key="step1"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-4"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <Store className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-foreground">
                  Nom de votre marque
                </h2>
                <p className="text-sm text-muted-foreground">
                  Comment s&apos;appelle votre entreprise ?
                </p>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Nom de la marque
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Ex: Family's Restaurant"
                className="w-full px-4 py-3 rounded-xl bg-secondary border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                autoFocus
              />
            </div>
          </motion.div>
        );

      case 2:
        return (
          <motion.div
            key="step2"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-4"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <Store className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-foreground">
                  Type d&apos;entreprise
                </h2>
                <p className="text-sm text-muted-foreground">
                  Quel est votre secteur d&apos;activite ?
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3">
              {BUSINESS_TYPES.map((type) => (
                <button
                  key={type.value}
                  onClick={() => setBusinessType(type.value)}
                  className={`p-4 rounded-xl border-2 transition-all text-left ${
                    businessType === type.value
                      ? "border-primary bg-primary/5"
                      : "border-border bg-secondary hover:border-primary/50"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{type.icon}</span>
                    <span className="font-medium text-foreground">
                      {type.label}
                    </span>
                    {businessType === type.value && (
                      <Check className="w-5 h-5 text-primary ml-auto" />
                    )}
                  </div>
                </button>
              ))}
            </div>
          </motion.div>
        );

      case 3:
        return (
          <motion.div
            key="step3"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-4"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-foreground">
                  Ton de voix
                </h2>
                <p className="text-sm text-muted-foreground">
                  Comment voulez-vous communiquer ?
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3">
              {TONE_OPTIONS.map((tone) => (
                <button
                  key={tone.value}
                  onClick={() => setToneVoice(tone.value)}
                  className={`p-4 rounded-xl border-2 transition-all text-left ${
                    toneVoice === tone.value
                      ? "border-primary bg-primary/5"
                      : "border-border bg-secondary hover:border-primary/50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-foreground mb-1">
                        {tone.label}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {tone.description}
                      </div>
                    </div>
                    {toneVoice === tone.value && (
                      <Check className="w-5 h-5 text-primary ml-4" />
                    )}
                  </div>
                </button>
              ))}
            </div>
          </motion.div>
        );

      case 4:
        return (
          <motion.div
            key="step4"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-4"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <Users className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-foreground">
                  Audience cible
                </h2>
                <p className="text-sm text-muted-foreground">
                  Qui sont vos clients ideaux ?
                </p>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Decrivez votre audience
              </label>
              <textarea
                value={targetAudience}
                onChange={(e) => setTargetAudience(e.target.value)}
                placeholder="Ex: Familles CSP+ de 30-50 ans, passionnees de gastronomie"
                className="w-full px-4 py-3 rounded-xl bg-secondary border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 min-h-[120px] resize-none"
                autoFocus
              />
            </div>
          </motion.div>
        );

      case 5:
        return (
          <motion.div
            key="step5"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-4"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <Globe className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-foreground">
                  Site web (optionnel)
                </h2>
                <p className="text-sm text-muted-foreground">
                  Ajoutez votre site pour plus de contexte
                </p>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                URL du site web
              </label>
              <input
                type="url"
                value={websiteUrl}
                onChange={(e) => setWebsiteUrl(e.target.value)}
                placeholder="https://example.com"
                className="w-full px-4 py-3 rounded-xl bg-secondary border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                autoFocus
              />
              <p className="text-xs text-muted-foreground mt-2">
                Ce champ est optionnel, vous pouvez le laisser vide
              </p>
            </div>
          </motion.div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Progress bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-foreground">
              Etape {step} sur {totalSteps}
            </span>
            <span className="text-sm text-muted-foreground">
              {Math.round((step / totalSteps) * 100)}%
            </span>
          </div>
          <div className="h-2 bg-secondary rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-primary"
              initial={{ width: 0 }}
              animate={{ width: `${(step / totalSteps) * 100}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        </div>

        {/* Main card */}
        <div className="glass-card rounded-2xl p-8 border border-border">
          <AnimatePresence mode="wait">{renderStep()}</AnimatePresence>

          {/* Error message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 p-4 rounded-xl bg-red-500/10 border border-red-500/20"
            >
              <p className="text-sm text-red-500">{error}</p>
            </motion.div>
          )}

          {/* Navigation buttons */}
          <div className="flex items-center justify-between mt-8 pt-6 border-t border-border">
            <button
              onClick={handleBack}
              disabled={step === 1}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-foreground hover:bg-secondary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
              Retour
            </button>

            {step < totalSteps ? (
              <button
                onClick={handleNext}
                disabled={!canProceed()}
                className="flex items-center gap-2 px-6 py-2 rounded-xl bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Suivant
                <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={handleComplete}
                disabled={!canProceed() || isSubmitting}
                className="flex items-center gap-2 px-6 py-2 rounded-xl bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Creation...
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4" />
                    Terminer
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

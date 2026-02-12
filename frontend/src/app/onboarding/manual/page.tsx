"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, Sparkles } from "lucide-react";
import Link from "next/link";
import { workspacesApi, brandsApi } from "@/lib/api";
import { toast } from "@/hooks/use-toast";
import { ProgressIndicator } from "../components/progress-indicator";
import { StepBrandInfo } from "../components/step-brand-info";
import { StepBrandVoice } from "../components/step-brand-voice";
import { StepAudiences } from "../components/step-audiences";
import { StepPlatforms } from "../components/step-platforms";
import type { OnboardingData } from "../page";

const STEPS = [
  { id: 1, title: "Votre marque", description: "Informations de base" },
  { id: 2, title: "Ton & style", description: "Personnalite de marque" },
  { id: 3, title: "Audiences", description: "Vos cibles" },
  { id: 4, title: "Plateformes", description: "Connexion reseaux" },
];

const defaultData: OnboardingData = {
  name: "",
  slug: "",
  brand_type: "other",
  description: "",
  website_url: "",
  tone_formal: 50,
  tone_playful: 50,
  tone_bold: 50,
  tone_emotional: 50,
  words_to_avoid: [],
  words_to_prefer: [],
  custom_instructions: "",
  target_persona: {
    name: "",
    age_range: "",
    interests: [],
    pain_points: [],
    goals: [],
  },
  locations: [],
  content_pillars: {
    education: 20,
    entertainment: 20,
    engagement: 20,
    promotion: 20,
    behind_scenes: 20,
  },
};

export default function ManualOnboardingPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [workspaceId, setWorkspaceId] = useState<string | null>(null);
  const [brandId, setBrandId] = useState<string | null>(null);
  const [data, setData] = useState<OnboardingData>(defaultData);

  useEffect(() => {
    const checkExistingBrand = async () => {
      try {
        const wsId = localStorage.getItem("workspace_id");
        if (!wsId) {
          setIsLoading(false);
          return;
        }
        setWorkspaceId(wsId);

        const response = await workspacesApi.getBrands(wsId);
        const brands = response.data;
        if (brands && brands.length > 0) {
          router.replace("/dashboard");
          return;
        }

        setIsLoading(false);
      } catch (error) {
        console.error("Error checking brand:", error);
        setIsLoading(false);
      }
    };
    checkExistingBrand();
  }, [router]);

  const updateData = (updates: Partial<OnboardingData>) => {
    setData((prev) => ({ ...prev, ...updates }));
  };

  const generateSlug = (name: string) => {
    return name
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
  };

  const handleStep1Complete = async () => {
    if (!workspaceId) return;
    setIsSaving(true);
    try {
      const response = await brandsApi.create(workspaceId, {
        name: data.name,
        slug: data.slug || generateSlug(data.name),
        brand_type: data.brand_type,
        description: data.description || undefined,
        website_url: data.website_url || undefined,
      });
      const newBrandId = response.data.id;
      setBrandId(newBrandId);
      localStorage.setItem("onboarding_brand_id", newBrandId);
      setCurrentStep(2);
    } catch (error: any) {
      toast({
        title: "Erreur",
        description: error.response?.data?.detail || "Impossible de creer la marque",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleStep2Complete = async () => {
    if (!brandId) return;
    setIsSaving(true);
    try {
      await brandsApi.updateVoice(brandId, {
        tone_formal: data.tone_formal,
        tone_playful: data.tone_playful,
        tone_bold: data.tone_bold,
        tone_emotional: data.tone_emotional,
        words_to_avoid: data.words_to_avoid.length > 0 ? data.words_to_avoid : undefined,
        words_to_prefer: data.words_to_prefer.length > 0 ? data.words_to_prefer : undefined,
        custom_instructions: data.custom_instructions || undefined,
      });
      setCurrentStep(3);
    } catch (error: any) {
      toast({
        title: "Erreur",
        description: error.response?.data?.detail || "Impossible de sauvegarder le ton",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleStep3Complete = async () => {
    if (!brandId) return;
    setIsSaving(true);
    try {
      await brandsApi.update(brandId, {
        target_persona: data.target_persona.name ? data.target_persona : undefined,
        locations: data.locations.length > 0 ? data.locations : undefined,
        content_pillars: data.content_pillars,
      });
      setCurrentStep(4);
    } catch (error: any) {
      toast({
        title: "Erreur",
        description: error.response?.data?.detail || "Impossible de sauvegarder les audiences",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleComplete = () => {
    localStorage.removeItem("onboarding_step");
    localStorage.removeItem("onboarding_brand_id");
    if (brandId) {
      localStorage.setItem("brand_id", brandId);
    }
    toast({
      title: "Configuration terminee !",
      description: "Votre marque est prete. Bienvenue sur PresenceOS !",
    });
    router.push("/dashboard");
  };

  const handleBack = () => {
    setCurrentStep((prev) => Math.max(1, prev - 1));
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-muted">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Chargement...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted">
      <header className="border-b bg-background/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <span className="font-semibold text-lg">PresenceOS</span>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/onboarding"
              className="text-xs text-muted-foreground hover:text-foreground transition-colors underline underline-offset-4"
            >
              Revenir a l&apos;interview IA
            </Link>
            <span className="text-sm text-muted-foreground">Configuration manuelle</span>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-4xl">
        <ProgressIndicator steps={STEPS} currentStep={currentStep} />

        <div className="mt-8">
          <AnimatePresence mode="wait">
            {currentStep === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <StepBrandInfo
                  data={data}
                  updateData={updateData}
                  onNext={handleStep1Complete}
                  isLoading={isSaving}
                />
              </motion.div>
            )}

            {currentStep === 2 && (
              <motion.div
                key="step2"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <StepBrandVoice
                  data={data}
                  updateData={updateData}
                  onNext={handleStep2Complete}
                  onBack={handleBack}
                  isLoading={isSaving}
                />
              </motion.div>
            )}

            {currentStep === 3 && (
              <motion.div
                key="step3"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <StepAudiences
                  data={data}
                  updateData={updateData}
                  onNext={handleStep3Complete}
                  onBack={handleBack}
                  isLoading={isSaving}
                />
              </motion.div>
            )}

            {currentStep === 4 && (
              <motion.div
                key="step4"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <StepPlatforms
                  brandId={brandId}
                  onComplete={handleComplete}
                  onBack={handleBack}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, Sparkles, MessageSquare, Plug2 } from "lucide-react";
import Link from "next/link";
import { workspacesApi, brandsApi } from "@/lib/api";
import { toast } from "@/hooks/use-toast";
import { ProgressIndicator } from "./components/progress-indicator";
import { OnboardingChat } from "./components/onboarding-chat";
import { StepPlatforms } from "./components/step-platforms";
import { fireSuccessConfetti } from "@/lib/confetti";

// Exported for backward compatibility with manual step components
export interface OnboardingData {
  name: string;
  slug: string;
  brand_type: string;
  description: string;
  website_url: string;
  tone_formal: number;
  tone_playful: number;
  tone_bold: number;
  tone_emotional: number;
  words_to_avoid: string[];
  words_to_prefer: string[];
  custom_instructions: string;
  target_persona: {
    name: string;
    age_range: string;
    interests: string[];
    pain_points: string[];
    goals: string[];
  };
  locations: string[];
  content_pillars: {
    education: number;
    entertainment: number;
    engagement: number;
    promotion: number;
    behind_scenes: number;
  };
}

const STEPS = [
  { id: 1, title: "Votre marque", description: "Interview IA" },
  { id: 2, title: "Plateformes", description: "Connexion réseaux" },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [currentStep, setCurrentStep] = useState(1);
  const [workspaceId, setWorkspaceId] = useState<string | null>(null);
  const [brandId, setBrandId] = useState<string | null>(null);

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

        const savedStep = localStorage.getItem("onboarding_step");
        const savedBrandId = localStorage.getItem("onboarding_brand_id");

        if (savedStep) {
          setCurrentStep(parseInt(savedStep, 10));
        }

        if (savedBrandId) {
          setBrandId(savedBrandId);
        }

        setIsLoading(false);
      } catch (error) {
        console.error("Error checking brand:", error);
        setIsLoading(false);
      }
    };

    checkExistingBrand();
  }, [router]);

  const generateSlug = (name: string) => {
    return name
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
  };

  const handleChatComplete = async (brandData: Record<string, unknown>) => {
    if (!workspaceId) {
      toast({
        title: "Erreur",
        description: "Workspace non trouve",
        variant: "destructive",
      });
      return;
    }

    try {
      const brand = brandData.brand as Record<string, unknown>;
      const voice = brandData.voice as Record<string, unknown>;
      const brandName = (brand?.name as string) || "Ma Marque";

      const response = await brandsApi.create(workspaceId, {
        name: brandName,
        slug: generateSlug(brandName),
        brand_type: brand?.brand_type || "other",
        description: brand?.description || undefined,
        website_url: brand?.website_url || undefined,
        target_persona: brand?.target_persona || undefined,
        locations: brand?.locations || undefined,
      });

      const newBrandId = response.data.id;
      setBrandId(newBrandId);
      localStorage.setItem("onboarding_brand_id", newBrandId);

      if (voice) {
        try {
          await brandsApi.updateVoice(newBrandId, voice);
        } catch {
          console.warn("Could not update brand voice");
        }
      }

      localStorage.setItem("onboarding_step", "2");
      setCurrentStep(2);

      toast({
        title: "Profil créé !",
        description: "Votre profil de marque a été créé avec succès.",
      });
    } catch (error: any) {
      toast({
        title: "Erreur",
        description: error.response?.data?.detail || "Impossible de créer la marque",
        variant: "destructive",
      });
    }
  };

  const handleComplete = () => {
    localStorage.removeItem("onboarding_step");
    localStorage.removeItem("onboarding_brand_id");

    if (brandId) {
      localStorage.setItem("brand_id", brandId);
    }

    toast({
      title: "Configuration terminée !",
      description: "Votre marque est prête. Bienvenue sur PresenceOS !",
    });

    fireSuccessConfetti();
    router.push("/dashboard");
  };

  const handleBack = () => {
    if (currentStep > 1) {
      const newStep = currentStep - 1;
      setCurrentStep(newStep);
      localStorage.setItem("onboarding_step", newStep.toString());
    }
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
      {/* Header */}
      <header className="border-b bg-background/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <span className="font-semibold text-lg">PresenceOS</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm text-muted-foreground">
              {currentStep === 1 ? (
                <span className="flex items-center gap-1">
                  <MessageSquare className="w-4 h-4" />
                  Interview IA
                </span>
              ) : (
                <span className="flex items-center gap-1">
                  <Plug2 className="w-4 h-4" />
                  Connexion réseaux
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Progress */}
        <ProgressIndicator steps={STEPS} currentStep={currentStep} />

        {/* Skip link for manual fill */}
        {currentStep === 1 && (
          <div className="mt-4 text-center">
            <Link
              href="/onboarding/manual"
              className="text-xs text-muted-foreground hover:text-foreground transition-colors underline underline-offset-4"
            >
              Préférer remplir manuellement ?
            </Link>
          </div>
        )}

        {/* Step content */}
        <div className="mt-8">
          <AnimatePresence mode="wait">
            {currentStep === 1 && (
              <motion.div
                key="step1-chat"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <div className="bg-card rounded-xl border shadow-sm overflow-hidden">
                  <OnboardingChat onComplete={handleChatComplete} />
                </div>
              </motion.div>
            )}

            {currentStep === 2 && (
              <motion.div
                key="step2-platforms"
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

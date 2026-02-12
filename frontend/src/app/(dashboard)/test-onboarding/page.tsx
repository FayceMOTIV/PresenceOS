"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { BrandOnboardingWizard } from "@/components/onboarding";
import { Loader2 } from "lucide-react";

/**
 * Test page for the BrandOnboardingWizard component
 *
 * This page demonstrates the simplified brand onboarding flow.
 * In production, you would typically:
 * 1. Create a brand shell first (just name + slug)
 * 2. Then use this wizard to complete the onboarding
 *
 * For testing: Set a brand_id in localStorage before visiting this page.
 * Example: localStorage.setItem('brand_id', 'your-brand-uuid-here')
 */
export default function TestOnboardingPage() {
  const router = useRouter();
  const [brandId, setBrandId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // In production, you'd get this from the workspace/brand creation flow
    const testBrandId = localStorage.getItem("brand_id");

    if (!testBrandId) {
      // For testing, you could create a test brand here or redirect
      console.error("No brand_id found in localStorage");
    }

    setBrandId(testBrandId);
    setIsLoading(false);
  }, []);

  const handleComplete = (brandData: any) => {
    console.log("Onboarding complete!", brandData);

    // Save the completed brand data
    localStorage.setItem("onboarding_complete", "true");

    // Redirect to dashboard or next step
    router.push("/dashboard");
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Chargement...</p>
        </div>
      </div>
    );
  }

  if (!brandId) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <div className="max-w-md w-full glass-card rounded-2xl p-8 border border-border text-center">
          <h1 className="text-xl font-bold text-foreground mb-4">
            Aucune marque trouvee
          </h1>
          <p className="text-muted-foreground mb-6">
            Pour tester l&apos;onboarding, vous devez d&apos;abord avoir une marque.
            Ajoutez un brand_id dans localStorage ou creez une marque.
          </p>
          <button
            onClick={() => router.push("/dashboard")}
            className="px-6 py-2 rounded-xl bg-primary text-white hover:bg-primary/90 transition-colors"
          >
            Retour au dashboard
          </button>
        </div>
      </div>
    );
  }

  return <BrandOnboardingWizard brandId={brandId} onComplete={handleComplete} />;
}

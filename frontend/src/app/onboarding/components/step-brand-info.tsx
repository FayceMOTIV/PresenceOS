"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ArrowRight, Building2, Globe, Loader2, Store, Briefcase, User, Package, Sparkles } from "lucide-react";
import type { OnboardingData } from "../page";
import { agentsApi } from "@/lib/api";

const BRAND_TYPES = [
  { value: "restaurant", label: "Restaurant / Food", icon: Store },
  { value: "ecommerce", label: "E-commerce", icon: Package },
  { value: "saas", label: "SaaS / Tech", icon: Globe },
  { value: "service", label: "Service / Agence", icon: Briefcase },
  { value: "personal", label: "Personal Brand", icon: User },
  { value: "other", label: "Autre", icon: Building2 },
];

interface StepBrandInfoProps {
  data: OnboardingData;
  updateData: (updates: Partial<OnboardingData>) => void;
  onNext: () => void;
  isLoading: boolean;
}

export function StepBrandInfo({ data, updateData, onNext, isLoading }: StepBrandInfoProps) {
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isExtracting, setIsExtracting] = useState(false);

  // Auto-generate slug from name
  useEffect(() => {
    if (data.name && !data.slug) {
      const slug = data.name
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-|-$/g, "");
      updateData({ slug });
    }
  }, [data.name]);

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!data.name.trim()) {
      newErrors.name = "Le nom de la marque est requis";
    } else if (data.name.length < 2) {
      newErrors.name = "Le nom doit contenir au moins 2 caracteres";
    }

    if (!data.slug.trim()) {
      newErrors.slug = "L'identifiant est requis";
    } else if (!/^[a-z0-9-]+$/.test(data.slug)) {
      newErrors.slug = "Uniquement lettres minuscules, chiffres et tirets";
    }

    if (data.website_url && !/^https?:\/\/.+/.test(data.website_url)) {
      newErrors.website_url = "URL invalide (doit commencer par http:// ou https://)";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) {
      onNext();
    }
  };

  const handleExtract = async () => {
    if (!data.website_url) return;
    setIsExtracting(true);
    try {
      const { data: taskData } = await agentsApi.extractBrand(data.website_url);
      // Poll for result
      const pollInterval = setInterval(async () => {
        try {
          const { data: status } = await agentsApi.getTaskStatus(taskData.task_id);
          if (status.status === "completed" && status.result) {
            clearInterval(pollInterval);
            const r = status.result;
            updateData({
              name: r.business_name || data.name,
              description: r.description || data.description,
            });
            setIsExtracting(false);
          } else if (status.status === "failed") {
            clearInterval(pollInterval);
            setIsExtracting(false);
          }
        } catch {
          clearInterval(pollInterval);
          setIsExtracting(false);
        }
      }, 2000);
    } catch {
      setIsExtracting(false);
    }
  };

  return (
    <Card className="glass-card">
      <CardHeader>
        <CardTitle className="text-2xl">Parlons de votre marque</CardTitle>
        <CardDescription>
          Ces informations nous aident a personnaliser l&apos;IA pour votre business.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Brand name */}
          <div className="space-y-2">
            <Label htmlFor="name">Nom de la marque *</Label>
            <Input
              id="name"
              placeholder="Ex: Family's Restaurant"
              value={data.name}
              onChange={(e) => updateData({ name: e.target.value })}
              className={errors.name ? "border-destructive" : ""}
            />
            {errors.name && <p className="text-sm text-destructive">{errors.name}</p>}
          </div>

          {/* Slug */}
          <div className="space-y-2">
            <Label htmlFor="slug">Identifiant unique *</Label>
            <div className="flex items-center">
              <span className="text-muted-foreground text-sm mr-2">presenceos.app/</span>
              <Input
                id="slug"
                placeholder="familys-restaurant"
                value={data.slug}
                onChange={(e) =>
                  updateData({
                    slug: e.target.value
                      .toLowerCase()
                      .replace(/[^a-z0-9-]/g, ""),
                  })
                }
                className={errors.slug ? "border-destructive" : ""}
              />
            </div>
            {errors.slug && <p className="text-sm text-destructive">{errors.slug}</p>}
          </div>

          {/* Brand type */}
          <div className="space-y-2">
            <Label>Type d&apos;activite *</Label>
            <Select
              value={data.brand_type}
              onValueChange={(value) => updateData({ brand_type: value })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Selectionnez votre type d'activite" />
              </SelectTrigger>
              <SelectContent>
                {BRAND_TYPES.map((type) => {
                  const Icon = type.icon;
                  return (
                    <SelectItem key={type.value} value={type.value}>
                      <div className="flex items-center gap-2">
                        <Icon className="w-4 h-4" />
                        <span>{type.label}</span>
                      </div>
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description (optionnel)</Label>
            <Textarea
              id="description"
              placeholder="Decrivez votre activite en quelques phrases..."
              value={data.description}
              onChange={(e) => updateData({ description: e.target.value })}
              rows={3}
            />
            <p className="text-xs text-muted-foreground">
              Cette description aide l&apos;IA a mieux comprendre votre business.
            </p>
          </div>

          {/* Website */}
          <div className="space-y-2">
            <Label htmlFor="website">Site web (optionnel)</Label>
            <div className="flex gap-2">
              <Input
                id="website"
                type="url"
                placeholder="https://votre-site.com"
                value={data.website_url}
                onChange={(e) => updateData({ website_url: e.target.value })}
                className={errors.website_url ? "border-destructive" : ""}
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={!data.website_url || isExtracting}
                onClick={handleExtract}
                className="border-primary/30"
              >
                {isExtracting ? (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Analyse en cours...</>
                ) : (
                  <><Sparkles className="w-4 h-4 mr-2" />Extraire automatiquement</>
                )}
              </Button>
            </div>
            {errors.website_url && (
              <p className="text-sm text-destructive">{errors.website_url}</p>
            )}
          </div>

          {/* Submit */}
          <div className="flex justify-end pt-4">
            <Button type="submit" variant="gradient" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creation...
                </>
              ) : (
                <>
                  Continuer
                  <ArrowRight className="w-4 h-4 ml-2" />
                </>
              )}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

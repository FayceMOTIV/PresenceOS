"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ArrowLeft,
  ArrowRight,
  Building2,
  Globe,
  Loader2,
  Store,
  Briefcase,
  User,
  Package,
  Sparkles,
  CheckCircle,
} from "lucide-react";
import { brandsApi } from "@/lib/api";
import { toast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

const BRAND_TYPES = [
  { value: "restaurant", label: "Restaurant / Food", icon: Store },
  { value: "ecommerce", label: "E-commerce", icon: Package },
  { value: "saas", label: "SaaS / Tech", icon: Globe },
  { value: "service", label: "Service / Agence", icon: Briefcase },
  { value: "personal", label: "Personal Brand", icon: User },
  { value: "other", label: "Autre", icon: Building2 },
];

interface BrandFormData {
  name: string;
  slug: string;
  brand_type: string;
  description: string;
  website_url: string;
}

const generateSlug = (name: string) => {
  return name
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
};

export default function NewBrandPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formData, setFormData] = useState<BrandFormData>({
    name: "",
    slug: "",
    brand_type: "other",
    description: "",
    website_url: "",
  });

  // Auto-generate slug from name
  useEffect(() => {
    if (formData.name) {
      setFormData((prev) => ({
        ...prev,
        slug: generateSlug(prev.name),
      }));
    }
  }, [formData.name]);

  const updateField = (field: keyof BrandFormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = "Le nom de la marque est requis";
    } else if (formData.name.length < 2) {
      newErrors.name = "Le nom doit contenir au moins 2 caracteres";
    }

    if (!formData.slug.trim()) {
      newErrors.slug = "L'identifiant est requis";
    } else if (!/^[a-z0-9-]+$/.test(formData.slug)) {
      newErrors.slug = "Uniquement lettres minuscules, chiffres et tirets";
    }

    if (
      formData.website_url &&
      !/^https?:\/\/.+/.test(formData.website_url)
    ) {
      newErrors.website_url =
        "URL invalide (doit commencer par http:// ou https://)";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    const workspaceId = localStorage.getItem("workspace_id");
    if (!workspaceId) {
      toast({
        title: "Erreur",
        description: "Aucun workspace actif. Reconnectez-vous.",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      const response = await brandsApi.create(workspaceId, {
        name: formData.name.trim(),
        slug: formData.slug.trim(),
        brand_type: formData.brand_type,
        description: formData.description.trim() || undefined,
        website_url: formData.website_url.trim() || undefined,
      });

      const newBrandId = response.data.id;
      localStorage.setItem("brand_id", newBrandId);

      setIsSuccess(true);

      toast({
        title: "Marque creee!",
        description: `${formData.name} a ete ajoutee avec succes.`,
      });

      // Redirect after a short delay so the user sees the success state
      setTimeout(() => {
        router.push("/dashboard");
        // Force reload to refresh sidebar brand list
        window.location.href = "/dashboard";
      }, 1200);
    } catch (error: any) {
      const message =
        error.response?.data?.detail || "Impossible de creer la marque";
      toast({
        title: "Erreur",
        description: message,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="max-w-lg mx-auto py-16">
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 200 }}
        >
          <Card className="text-center">
            <CardContent className="pt-10 pb-10">
              <div className="w-16 h-16 rounded-2xl bg-emerald-50 mx-auto mb-4 flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-emerald-500" />
              </div>
              <h2 className="text-2xl font-bold mb-2">Marque creee!</h2>
              <p className="text-muted-foreground">
                Redirection vers le dashboard...
              </p>
              <Loader2 className="w-5 h-5 animate-spin text-muted-foreground mx-auto mt-4" />
            </CardContent>
          </Card>
        </motion.div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="max-w-2xl mx-auto py-4"
    >
      {/* Back link */}
      <Link
        href="/dashboard"
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Retour au dashboard
      </Link>

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">
          Ajouter une marque
        </h1>
        <p className="text-muted-foreground mt-1">
          Configurez votre nouvelle marque pour personnaliser l&apos;IA.
        </p>
      </div>

      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Brand name */}
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className="space-y-2"
            >
              <Label htmlFor="name">
                Nom de la marque <span className="text-destructive">*</span>
              </Label>
              <Input
                id="name"
                placeholder="Ex: Family's Restaurant"
                value={formData.name}
                onChange={(e) => updateField("name", e.target.value)}
                className={errors.name ? "border-destructive" : ""}
              />
              {errors.name && (
                <p className="text-sm text-destructive">{errors.name}</p>
              )}
            </motion.div>

            {/* Slug */}
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.15 }}
              className="space-y-2"
            >
              <Label htmlFor="slug">
                Identifiant unique{" "}
                <span className="text-destructive">*</span>
              </Label>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground whitespace-nowrap">
                  presenceos.app/
                </span>
                <Input
                  id="slug"
                  placeholder="familys-restaurant"
                  value={formData.slug}
                  onChange={(e) =>
                    updateField(
                      "slug",
                      e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "")
                    )
                  }
                  className={errors.slug ? "border-destructive" : ""}
                />
              </div>
              {errors.slug && (
                <p className="text-sm text-destructive">{errors.slug}</p>
              )}
            </motion.div>

            {/* Brand type */}
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="space-y-2"
            >
              <Label>
                Type d&apos;activite{" "}
                <span className="text-destructive">*</span>
              </Label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {BRAND_TYPES.map((type) => {
                  const Icon = type.icon;
                  const isSelected = formData.brand_type === type.value;
                  return (
                    <button
                      key={type.value}
                      type="button"
                      onClick={() => updateField("brand_type", type.value)}
                      className={cn(
                        "flex items-center gap-2.5 rounded-xl border px-4 py-3 text-sm font-medium transition-all duration-200 text-left",
                        isSelected
                          ? "border-violet-300 bg-violet-50 text-violet-700 shadow-sm shadow-violet-500/10"
                          : "border-gray-200/80 bg-white hover:bg-gray-50 hover:border-gray-300/80 text-gray-700"
                      )}
                    >
                      <Icon
                        className={cn(
                          "w-4 h-4",
                          isSelected
                            ? "text-violet-600"
                            : "text-gray-400"
                        )}
                      />
                      {type.label}
                    </button>
                  );
                })}
              </div>
            </motion.div>

            {/* Description */}
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.25 }}
              className="space-y-2"
            >
              <Label htmlFor="description">Description (optionnel)</Label>
              <Textarea
                id="description"
                placeholder="Decrivez votre activite en quelques phrases..."
                value={formData.description}
                onChange={(e) => updateField("description", e.target.value)}
                rows={3}
                className="resize-none"
              />
              <p className="text-xs text-muted-foreground">
                Cette description aide l&apos;IA a mieux comprendre votre
                business.
              </p>
            </motion.div>

            {/* Website */}
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              className="space-y-2"
            >
              <Label htmlFor="website">Site web (optionnel)</Label>
              <Input
                id="website"
                type="url"
                placeholder="https://votre-site.com"
                value={formData.website_url}
                onChange={(e) => updateField("website_url", e.target.value)}
                className={errors.website_url ? "border-destructive" : ""}
              />
              {errors.website_url && (
                <p className="text-sm text-destructive">
                  {errors.website_url}
                </p>
              )}
            </motion.div>

            {/* Actions */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35 }}
              className="flex items-center justify-between pt-4 border-t border-gray-100"
            >
              <Link href="/dashboard">
                <Button type="button" variant="ghost">
                  Annuler
                </Button>
              </Link>
              <Button
                type="submit"
                variant="gradient"
                disabled={isLoading}
                className="group"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Creation...
                  </>
                ) : (
                  <>
                    Creer la marque
                    <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </Button>
            </motion.div>
          </form>
        </CardContent>
      </Card>
    </motion.div>
  );
}

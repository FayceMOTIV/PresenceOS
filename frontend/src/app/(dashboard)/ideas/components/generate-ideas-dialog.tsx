"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Sparkles, Loader2, AlertCircle } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { aiApi } from "@/lib/api";
import { ContentIdea } from "@/types";
import { toast } from "@/hooks/use-toast";

interface GenerateIdeasDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onIdeasGenerated: (ideas: ContentIdea[]) => void;
}

const countOptions = [
  { value: "3", label: "3 idees" },
  { value: "5", label: "5 idees" },
  { value: "10", label: "10 idees" },
];

const platformOptions = [
  { value: "all", label: "Toutes les plateformes" },
  { value: "instagram_post", label: "Instagram" },
  { value: "linkedin", label: "LinkedIn" },
  { value: "tiktok", label: "TikTok" },
  { value: "facebook", label: "Facebook" },
];

export function GenerateIdeasDialog({
  open,
  onOpenChange,
  onIdeasGenerated,
}: GenerateIdeasDialogProps) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [count, setCount] = useState("5");
  const [theme, setTheme] = useState("");
  const [platform, setPlatform] = useState("all");
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    const brandId = localStorage.getItem("brand_id");
    if (!brandId) {
      toast({
        title: "Erreur",
        description: "Marque non trouvee",
        variant: "destructive",
      });
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      // Generate ideas
      const generateResponse = await aiApi.generateIdeas(brandId, {
        count: parseInt(count),
        context: theme || undefined,
        platforms: platform !== "all" ? [platform] : undefined,
      });

      const generatedIdeas = generateResponse.data.ideas;

      if (!generatedIdeas || generatedIdeas.length === 0) {
        throw new Error("Aucune idee generee");
      }

      // Save ideas to database
      const saveResponse = await aiApi.saveIdeas(brandId, generatedIdeas);
      const savedIdeas = saveResponse.data;

      toast({
        title: "Idees generees",
        description: `${savedIdeas.length} idees ont ete generees avec succes`,
      });

      onIdeasGenerated(savedIdeas);
      onOpenChange(false);

      // Reset form
      setTheme("");
      setCount("5");
      setPlatform("all");
    } catch (err: any) {
      console.error("Error generating ideas:", err);

      // Check for specific error types
      if (err.response?.status === 401) {
        setError("Session expiree. Veuillez vous reconnecter.");
      } else if (err.response?.status === 429) {
        setError("Trop de requetes. Veuillez patienter quelques minutes.");
      } else if (err.response?.data?.detail?.includes("API key")) {
        setError("Cle API IA non configuree. Ajoutez votre cle OpenAI ou Anthropic dans les parametres.");
      } else {
        setError("La generation a echoue. Veuillez reessayer.");
      }

      toast({
        title: "Erreur",
        description: "La generation a echoue, reessayez",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-500" />
            Generer des idees avec l&apos;IA
          </DialogTitle>
          <DialogDescription>
            L&apos;IA va analyser votre marque et generer des idees de contenu personnalisees.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Count selection */}
          <div className="space-y-2">
            <Label htmlFor="count">Nombre d&apos;idees</Label>
            <Select value={count} onValueChange={setCount}>
              <SelectTrigger id="count">
                <SelectValue placeholder="Selectionnez" />
              </SelectTrigger>
              <SelectContent>
                {countOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Theme input */}
          <div className="space-y-2">
            <Label htmlFor="theme">Theme (optionnel)</Label>
            <Input
              id="theme"
              placeholder="Ex: ete, promotions, recettes..."
              value={theme}
              onChange={(e) => setTheme(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Laissez vide pour des idees variees
            </p>
          </div>

          {/* Platform selection */}
          <div className="space-y-2">
            <Label htmlFor="platform">Plateforme cible</Label>
            <Select value={platform} onValueChange={setPlatform}>
              <SelectTrigger id="platform">
                <SelectValue placeholder="Selectionnez" />
              </SelectTrigger>
              <SelectContent>
                {platformOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Error message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-2 p-3 rounded-lg bg-destructive/10 text-destructive text-sm"
            >
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <p>{error}</p>
            </motion.div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isGenerating}
          >
            Annuler
          </Button>
          <Button
            variant="gradient"
            onClick={handleGenerate}
            disabled={isGenerating}
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Generation...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                Generer
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Skeleton loader component for the table
export function IdeasTableSkeleton({ count }: { count: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: count }).map((_, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.1 }}
          className="flex items-center gap-4 p-4 rounded-lg border bg-card"
        >
          <div className="flex-1 space-y-2">
            <div className="h-4 w-3/4 bg-muted animate-pulse rounded" />
            <div className="h-3 w-1/2 bg-muted animate-pulse rounded" />
          </div>
          <div className="h-6 w-16 bg-muted animate-pulse rounded-full" />
          <div className="h-6 w-20 bg-muted animate-pulse rounded-full" />
          <div className="flex gap-1">
            <div className="h-6 w-6 bg-muted animate-pulse rounded-full" />
            <div className="h-6 w-6 bg-muted animate-pulse rounded-full" />
          </div>
        </motion.div>
      ))}
    </div>
  );
}

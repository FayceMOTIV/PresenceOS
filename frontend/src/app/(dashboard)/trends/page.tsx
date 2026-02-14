"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  TrendingUp,
  Plus,
  X,
  Sparkles,
  Loader2,
  Save,
  Globe,
  Hash,
  Target,
  Lightbulb,
} from "lucide-react";
import { HelpTooltip } from "@/components/ui/help-tooltip";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { toast } from "@/hooks/use-toast";
import { aiApi } from "@/lib/api";
import { cn } from "@/lib/utils";

interface TrendInput {
  id: string;
  description: string;
  url: string;
  platform: string;
}

interface GeneratedIdea {
  title: string;
  description: string;
  content_pillar: string;
  target_platforms: string[];
  hooks: string[];
  ai_reasoning: string;
}

interface AnalysisResult {
  summary: string;
  key_themes: string[];
  ideas?: GeneratedIdea[];
}

export default function TrendsPage() {
  const [trends, setTrends] = useState<TrendInput[]>([
    { id: "1", description: "", url: "", platform: "" },
  ]);
  const [generateIdeas, setGenerateIdeas] = useState(true);
  const [ideaCount, setIdeaCount] = useState("5");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);

  const addTrend = () => {
    const newId = (Math.max(...trends.map((t) => parseInt(t.id)), 0) + 1).toString();
    setTrends([...trends, { id: newId, description: "", url: "", platform: "" }]);
  };

  const removeTrend = (id: string) => {
    if (trends.length > 1) {
      setTrends(trends.filter((t) => t.id !== id));
    }
  };

  const updateTrend = (id: string, field: keyof TrendInput, value: string) => {
    setTrends(trends.map((t) => (t.id === id ? { ...t, [field]: value } : t)));
  };

  const handleAnalyze = async () => {
    const brandId = localStorage.getItem("brand_id");
    if (!brandId) {
      toast({
        title: "Erreur",
        description: "Aucune marque sélectionnée",
        variant: "destructive",
      });
      return;
    }

    const validTrends = trends.filter((t) => t.description.trim() !== "");
    if (validTrends.length === 0) {
      toast({
        title: "Erreur",
        description: "Veuillez décrire au moins une tendance",
        variant: "destructive",
      });
      return;
    }

    setIsAnalyzing(true);
    try {
      const payload = {
        trends: validTrends.map((t) => ({
          description: t.description,
          url: t.url || undefined,
          platform: t.platform || undefined,
        })),
        generate_ideas: generateIdeas,
        idea_count: parseInt(ideaCount),
      };

      const response = await aiApi.analyzeTrends(brandId, payload);
      setAnalysisResult(response.data);
      toast({
        title: "Analyse terminée",
        description: generateIdeas
          ? `${response.data.ideas?.length || 0} idée(s) générée(s)`
          : "Tendances analysées avec succès",
      });
    } catch (error: any) {
      console.error("Error analyzing trends:", error);
      toast({
        title: "Erreur",
        description: error.response?.data?.detail || "Impossible d'analyser les tendances",
        variant: "destructive",
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSaveIdeas = async () => {
    const brandId = localStorage.getItem("brand_id");
    if (!brandId || !analysisResult?.ideas) return;

    setIsSaving(true);
    try {
      await aiApi.saveIdeas(brandId, analysisResult.ideas);
      toast({
        title: "Idées sauvegardées",
        description: `${analysisResult.ideas.length} idée(s) ajoutée(s) à votre liste`,
      });
    } catch (error: any) {
      console.error("Error saving ideas:", error);
      toast({
        title: "Erreur",
        description: error.response?.data?.detail || "Impossible de sauvegarder les idées",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold">Tendances <HelpTooltip content="Découvrez les sujets populaires du moment pour créer des posts qui intéressent les gens." /></h1>
        <p className="text-muted-foreground">
          Analysez les tendances et générez des idées de contenu
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Ajouter des tendances</CardTitle>
          <CardDescription>
            Décrivez les tendances que vous souhaitez analyser pour générer des idées de contenu adaptées
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-4">
            <AnimatePresence mode="popLayout">
              {trends.map((trend, index) => (
                <motion.div
                  key={trend.id}
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.2 }}
                  className="space-y-3 p-4 border rounded-lg bg-card"
                >
                  <div className="flex items-start justify-between gap-2">
                    <Label className="text-sm font-medium">Tendance {index + 1}</Label>
                    {trends.length > 1 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeTrend(trend.id)}
                        className="h-6 w-6 p-0"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                  </div>

                  <div className="space-y-3">
                    <div>
                      <Input
                        placeholder="Décrivez la tendance..."
                        value={trend.description}
                        onChange={(e) => updateTrend(trend.id, "description", e.target.value)}
                        className="w-full"
                      />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div>
                        <Input
                          placeholder="URL de référence (optionnel)"
                          value={trend.url}
                          onChange={(e) => updateTrend(trend.id, "url", e.target.value)}
                          className="w-full"
                        />
                      </div>

                      <div>
                        <Select
                          value={trend.platform}
                          onValueChange={(value) => updateTrend(trend.id, "platform", value)}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Plateforme (optionnel)" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value=" ">Aucune</SelectItem>
                            <SelectItem value="Instagram">Instagram</SelectItem>
                            <SelectItem value="TikTok">TikTok</SelectItem>
                            <SelectItem value="LinkedIn">LinkedIn</SelectItem>
                            <SelectItem value="Facebook">Facebook</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            <Button
              variant="outline"
              onClick={addTrend}
              className="w-full"
            >
              <Plus className="w-4 h-4 mr-2" />
              Ajouter une tendance
            </Button>
          </div>

          <Separator />

          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="generate-ideas"
                checked={generateIdeas}
                onCheckedChange={(checked) => setGenerateIdeas(checked as boolean)}
              />
              <Label htmlFor="generate-ideas" className="text-sm font-normal cursor-pointer">
                Générer des idées de contenu
              </Label>
            </div>

            {generateIdeas && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-2"
              >
                <Label htmlFor="idea-count" className="text-sm">
                  Nombre d&apos;idées à générer
                </Label>
                <Select value={ideaCount} onValueChange={setIdeaCount}>
                  <SelectTrigger id="idea-count" className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="3">3</SelectItem>
                    <SelectItem value="5">5</SelectItem>
                    <SelectItem value="10">10</SelectItem>
                  </SelectContent>
                </Select>
              </motion.div>
            )}
          </div>

          <Button
            onClick={handleAnalyze}
            disabled={isAnalyzing}
            className="w-full"
            size="lg"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Analyse en cours...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                Analyser
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      <AnimatePresence>
        {analysisResult && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
            className="space-y-6"
          >
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  Analyse des tendances
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h3 className="font-semibold mb-2">Résumé</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {analysisResult.summary}
                  </p>
                </div>

                {analysisResult.key_themes && analysisResult.key_themes.length > 0 && (
                  <div>
                    <h3 className="font-semibold mb-3">Thèmes clés</h3>
                    <div className="flex flex-wrap gap-2">
                      {analysisResult.key_themes.map((theme, index) => (
                        <Badge key={index} variant="secondary" className="text-sm">
                          <Hash className="w-3 h-3 mr-1" />
                          {theme}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {analysisResult.ideas && analysisResult.ideas.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-bold flex items-center gap-2">
                      <Lightbulb className="w-6 h-6" />
                      Idées générées
                    </h2>
                    <p className="text-sm text-muted-foreground">
                      {analysisResult.ideas.length} idée(s) basée(s) sur les tendances analysées
                    </p>
                  </div>
                  <Button onClick={handleSaveIdeas} disabled={isSaving}>
                    {isSaving ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Sauvegarde...
                      </>
                    ) : (
                      <>
                        <Save className="w-4 h-4 mr-2" />
                        Sauvegarder les idées
                      </>
                    )}
                  </Button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {analysisResult.ideas.map((idea, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ duration: 0.2, delay: index * 0.05 }}
                    >
                      <Card className="h-full hover:shadow-md transition-shadow">
                        <CardHeader>
                          <CardTitle className="text-lg">{idea.title}</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          <p className="text-sm text-muted-foreground">
                            {idea.description}
                          </p>

                          <div className="space-y-3">
                            <div>
                              <div className="flex items-center gap-2 mb-2">
                                <Hash className="w-4 h-4 text-muted-foreground" />
                                <span className="text-xs font-medium text-muted-foreground">
                                  Pilier de contenu
                                </span>
                              </div>
                              <Badge variant="outline">{idea.content_pillar}</Badge>
                            </div>

                            {idea.target_platforms && idea.target_platforms.length > 0 && (
                              <div>
                                <div className="flex items-center gap-2 mb-2">
                                  <Target className="w-4 h-4 text-muted-foreground" />
                                  <span className="text-xs font-medium text-muted-foreground">
                                    Plateformes cibles
                                  </span>
                                </div>
                                <div className="flex flex-wrap gap-1.5">
                                  {idea.target_platforms.map((platform, i) => (
                                    <Badge key={i} variant="secondary" className="text-xs">
                                      {platform}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}

                            {idea.hooks && idea.hooks.length > 0 && (
                              <div>
                                <div className="flex items-center gap-2 mb-2">
                                  <Sparkles className="w-4 h-4 text-muted-foreground" />
                                  <span className="text-xs font-medium text-muted-foreground">
                                    Accroches suggérées
                                  </span>
                                </div>
                                <ul className="space-y-1">
                                  {idea.hooks.slice(0, 3).map((hook, i) => (
                                    <li key={i} className="text-xs text-muted-foreground flex items-start gap-1.5">
                                      <span className="text-primary mt-0.5">•</span>
                                      <span className="flex-1">{hook}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {idea.ai_reasoning && (
                              <div className="pt-3 border-t">
                                <div className="flex items-center gap-2 mb-1.5">
                                  <Globe className="w-3.5 h-3.5 text-muted-foreground" />
                                  <span className="text-xs font-medium text-muted-foreground">
                                    Raisonnement IA
                                  </span>
                                </div>
                                <p className="text-xs text-muted-foreground italic">
                                  {idea.ai_reasoning}
                                </p>
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {!analysisResult && !isAnalyzing && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <div className="w-16 h-16 rounded-2xl bg-muted mx-auto mb-4 flex items-center justify-center">
            <TrendingUp className="w-8 h-8 text-muted-foreground" />
          </div>
          <h3 className="font-semibold mb-2">Analysez les tendances</h3>
          <p className="text-sm text-muted-foreground max-w-md mx-auto">
            Ajoutez des tendances que vous avez repérées sur les réseaux sociaux ou dans votre
            industrie. Notre IA les analysera et générera des idées de contenu adaptées à votre
            marque.
          </p>
        </motion.div>
      )}
    </motion.div>
  );
}

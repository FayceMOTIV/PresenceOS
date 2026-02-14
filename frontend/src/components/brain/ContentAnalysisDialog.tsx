"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Instagram,
  Search,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Sparkles,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { toast } from "@/hooks/use-toast";
import { contentAnalysisApi } from "@/lib/api";
import { fireSuccessConfetti } from "@/lib/confetti";

interface ToneResult {
  tone_formal: number;
  tone_playful: number;
  tone_bold: number;
  tone_emotional: number;
  humor_level: number;
}

interface VocabularyResult {
  favorite_words: string[];
  favorite_emojis: string[];
  cta_style: string;
  sentence_style: string;
  hashtag_style: string;
  words_to_prefer: string[];
}

interface AnalysisResult {
  success: boolean;
  posts_found: number;
  posts_analyzed: number;
  summary: string;
  tone: ToneResult | null;
  vocabulary: VocabularyResult | null;
  custom_instructions: string;
  error?: string;
}

interface ContentAnalysisDialogProps {
  onKnowledgeUpdated: () => void;
}

const toneLabels: Record<string, { label: string; low: string; high: string }> = {
  tone_formal: { label: "Formalite", low: "Casual", high: "Formel" },
  tone_playful: { label: "Ludique", low: "Serieux", high: "Joueur" },
  tone_bold: { label: "Audace", low: "Subtil", high: "Audacieux" },
  tone_emotional: { label: "Emotion", low: "Rationnel", high: "Emotionnel" },
  humor_level: { label: "Humour", low: "Aucun", high: "Tres drole" },
};

export function ContentAnalysisDialog({
  onKnowledgeUpdated,
}: ContentAnalysisDialogProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [username, setUsername] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressLabel, setProgressLabel] = useState("");
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const handleAnalyze = async () => {
    const brandId = localStorage.getItem("brand_id");
    if (!brandId || !username.trim()) return;

    setIsAnalyzing(true);
    setResult(null);
    setProgress(10);
    setProgressLabel("Recherche du profil Instagram...");

    try {
      // Simulate progress steps while the API processes
      const progressTimer = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 85) {
            clearInterval(progressTimer);
            return 85;
          }
          const step = prev < 30 ? 8 : prev < 60 ? 5 : 3;
          return prev + step;
        });
        setProgressLabel((prev) => {
          if (prev.includes("Recherche")) return "Récupération des posts...";
          if (prev.includes("Récupération")) return "Analyse du ton avec l'IA...";
          if (prev.includes("ton")) return "Extraction du vocabulaire...";
          return "Sauvegarde des résultats...";
        });
      }, 2000);

      const response = await contentAnalysisApi.analyze(
        brandId,
        username.trim()
      );

      clearInterval(progressTimer);
      setProgress(100);
      setProgressLabel("Analyse terminée !");

      const data = response.data as AnalysisResult;
      setResult(data);

      if (data.success) {
        fireSuccessConfetti();
        toast({
          title: "Analyse terminée",
          description: `${data.posts_analyzed} posts analysés. Ton et vocabulaire extraits.`,
        });
        onKnowledgeUpdated();
      } else {
        toast({
          title: "Echec de l'analyse",
          description: data.error || "Erreur inconnue",
          variant: "destructive",
        });
      }
    } catch (error: any) {
      setProgress(0);
      setProgressLabel("");
      const errMsg =
        error?.response?.data?.detail || "Erreur lors de l'analyse";
      setResult({
        success: false,
        posts_found: 0,
        posts_analyzed: 0,
        summary: "",
        tone: null,
        vocabulary: null,
        custom_instructions: "",
        error: errMsg,
      });
      toast({
        title: "Erreur",
        description: errMsg,
        variant: "destructive",
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleClose = () => {
    if (!isAnalyzing) {
      setIsOpen(false);
      // Reset after close animation
      setTimeout(() => {
        setResult(null);
        setProgress(0);
        setProgressLabel("");
      }, 300);
    }
  };

  return (
    <>
      {/* Trigger Card */}
      <Card
        className="border-dashed border-purple-500/30 bg-purple-500/5 cursor-pointer hover:bg-purple-500/10 transition-colors"
        onClick={() => setIsOpen(true)}
      >
        <CardContent className="flex items-center gap-4 py-4">
          <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center shrink-0">
            <Instagram className="w-5 h-5 text-purple-500" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-sm">
              Analyser un compte Instagram
            </h3>
            <p className="text-xs text-muted-foreground">
              Extraire le ton et le vocabulaire d&apos;un compte pour calibrer
              votre voix de marque
            </p>
          </div>
          <Sparkles className="w-5 h-5 text-purple-500 shrink-0" />
        </CardContent>
      </Card>

      {/* Analysis Dialog */}
      <Dialog open={isOpen} onOpenChange={handleClose}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Instagram className="w-5 h-5 text-purple-500" />
              Analyse de contenu Instagram
            </DialogTitle>
            <DialogDescription>
              Entrez un nom d&apos;utilisateur Instagram pour analyser le ton et
              le style de ses publications.
            </DialogDescription>
          </DialogHeader>

          {/* Input */}
          <div className="flex gap-2 mt-2">
            <div className="relative flex-1">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">
                @
              </span>
              <Input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="nom_utilisateur"
                className="pl-8"
                disabled={isAnalyzing}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && username.trim() && !isAnalyzing) {
                    handleAnalyze();
                  }
                }}
              />
            </div>
            <Button
              onClick={handleAnalyze}
              disabled={!username.trim() || isAnalyzing}
            >
              {isAnalyzing ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Search className="w-4 h-4 mr-2" />
              )}
              Analyser
            </Button>
          </div>

          {/* Progress Bar */}
          <AnimatePresence>
            {isAnalyzing && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-2"
              >
                <Progress value={progress} className="h-2" />
                <p className="text-xs text-muted-foreground text-center">
                  {progressLabel}
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Results */}
          <AnimatePresence>
            {result && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                {/* Status */}
                {result.success ? (
                  <div className="flex items-center gap-2 text-green-500">
                    <CheckCircle2 className="w-4 h-4" />
                    <span className="text-sm font-medium">
                      {result.posts_analyzed} posts analyses avec succes
                    </span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-destructive">
                    <AlertCircle className="w-4 h-4" />
                    <span className="text-sm">{result.error}</span>
                  </div>
                )}

                {/* Summary */}
                {result.summary && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Resume</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground">
                        {result.summary}
                      </p>
                    </CardContent>
                  </Card>
                )}

                {/* Tone Metrics */}
                {result.tone && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">
                        Metriques de ton
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {Object.entries(result.tone).map(([key, value]) => {
                        const meta = toneLabels[key];
                        if (!meta) return null;
                        return (
                          <div key={key} className="space-y-1">
                            <div className="flex justify-between text-xs">
                              <span className="text-muted-foreground">
                                {meta.low}
                              </span>
                              <span className="font-medium">{meta.label}</span>
                              <span className="text-muted-foreground">
                                {meta.high}
                              </span>
                            </div>
                            <div className="relative">
                              <Progress value={value} className="h-2" />
                              <span className="absolute right-0 -top-5 text-xs font-mono">
                                {value}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </CardContent>
                  </Card>
                )}

                {/* Vocabulary */}
                {result.vocabulary && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">
                        Vocabulaire et style
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {/* Favorite words */}
                      {result.vocabulary.favorite_words.length > 0 && (
                        <div>
                          <p className="text-xs font-medium mb-1">
                            Mots favoris
                          </p>
                          <div className="flex flex-wrap gap-1">
                            {result.vocabulary.favorite_words.map(
                              (word, idx) => (
                                <Badge
                                  key={idx}
                                  variant="secondary"
                                  className="text-xs"
                                >
                                  {word}
                                </Badge>
                              )
                            )}
                          </div>
                        </div>
                      )}

                      {/* Favorite emojis */}
                      {result.vocabulary.favorite_emojis.length > 0 && (
                        <div>
                          <p className="text-xs font-medium mb-1">
                            Emojis favoris
                          </p>
                          <div className="flex gap-1 text-lg">
                            {result.vocabulary.favorite_emojis.map(
                              (emoji, idx) => (
                                <span key={idx}>{emoji}</span>
                              )
                            )}
                          </div>
                        </div>
                      )}

                      {/* CTA style */}
                      {result.vocabulary.cta_style && (
                        <div>
                          <p className="text-xs font-medium mb-1">Style CTA</p>
                          <p className="text-xs text-muted-foreground">
                            {result.vocabulary.cta_style}
                          </p>
                        </div>
                      )}

                      {/* Sentence style */}
                      {result.vocabulary.sentence_style && (
                        <div>
                          <p className="text-xs font-medium mb-1">
                            Style de phrases
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {result.vocabulary.sentence_style}
                          </p>
                        </div>
                      )}

                      {/* Words to prefer */}
                      {result.vocabulary.words_to_prefer.length > 0 && (
                        <div>
                          <p className="text-xs font-medium mb-1">
                            Expressions signatures
                          </p>
                          <div className="flex flex-wrap gap-1">
                            {result.vocabulary.words_to_prefer.map(
                              (word, idx) => (
                                <Badge
                                  key={idx}
                                  variant="secondary"
                                  className="text-xs bg-green-500/10 text-green-500"
                                >
                                  {word}
                                </Badge>
                              )
                            )}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}

                {/* Custom Instructions */}
                {result.custom_instructions && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">
                        Instructions IA generees
                      </CardTitle>
                      <CardDescription className="text-xs">
                        Ces instructions ont ete sauvegardees dans votre voix de
                        marque
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm italic text-muted-foreground">
                        &quot;{result.custom_instructions}&quot;
                      </p>
                    </CardContent>
                  </Card>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </DialogContent>
      </Dialog>
    </>
  );
}

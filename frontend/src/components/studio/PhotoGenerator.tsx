"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, Loader2, Camera, Wand2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { studioAiApi } from "@/lib/api";
import { toast } from "@/hooks/use-toast";

interface PhotoGeneratorProps {
  onPhotoGenerated: (url: string, revisedPrompt?: string) => void;
}

const styles = [
  { id: "natural", label: "Naturel", emoji: "🌿", description: "Lumière douce, authentique" },
  { id: "cinematic", label: "Cinéma", emoji: "🎬", description: "Dramatique, profondeur" },
  { id: "vibrant", label: "Vibrant", emoji: "🌈", description: "Couleurs vives, accrocheur" },
  { id: "minimalist", label: "Minimaliste", emoji: "⚪", description: "Épuré, élégant" },
];

const examplePrompts = [
  "Burger artisanal avec frites maison sur table en bois",
  "Plat de pâtes fraîches à la truffe, vue plongeante",
  "Salade colorée avec légumes de saison, lumière naturelle",
  "Cocktail tropical au coucher du soleil, ambiance bar",
];

export default function PhotoGenerator({ onPhotoGenerated }: PhotoGeneratorProps) {
  const [prompt, setPrompt] = useState("");
  const [style, setStyle] = useState("natural");
  const [loading, setLoading] = useState(false);
  const [variations, setVariations] = useState<Array<{
    image_url: string;
    revised_prompt?: string;
    style: string;
  }>>([]);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;

    setLoading(true);
    setVariations([]);
    try {
      const res = await studioAiApi.generateVariations({
        prompt,
        style,
        niche: "restaurant",
      });

      const data = res.data;
      const vars = data.variations || [];
      setVariations(vars);

      if (vars.length > 0) {
        onPhotoGenerated(vars[0].image_url, vars[0].revised_prompt);
        toast({
          title: "Photos générées !",
          description: `${vars.length} variation${vars.length > 1 ? "s" : ""} créée${vars.length > 1 ? "s" : ""} avec succès`,
        });
      }
    } catch (error: unknown) {
      const msg =
        (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Vérifiez que la clé OpenAI est configurée dans le backend.";
      toast({
        title: "Erreur de génération",
        description: msg,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="border-violet-200/60">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-lg">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-pink-500 flex items-center justify-center">
            <Camera className="w-4 h-4 text-white" />
          </div>
          Générer une photo IA
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* Prompt */}
        <div>
          <label className="text-sm font-medium text-gray-700 mb-2 block">
            Décrivez votre photo
          </label>
          <Textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Ex : Burger artisanal avec frites maison..."
            className="min-h-[80px] resize-none border-gray-200 focus:border-violet-400 focus:ring-violet-400/20"
            rows={3}
          />
        </div>

        {/* Example prompts */}
        <div className="flex flex-wrap gap-2">
          <span className="text-xs text-gray-400 self-center">Exemples :</span>
          {examplePrompts.map((ex) => (
            <button
              key={ex}
              onClick={() => setPrompt(ex)}
              className="text-xs px-3 py-1.5 rounded-full border border-gray-200 bg-gray-50 hover:bg-violet-50 hover:border-violet-200 text-gray-600 hover:text-violet-700 transition-colors"
            >
              {ex.length > 40 ? ex.slice(0, 37) + "..." : ex}
            </button>
          ))}
        </div>

        {/* Style selector */}
        <div>
          <label className="text-sm font-medium text-gray-700 mb-3 block">
            Style visuel
          </label>
          <div className="grid grid-cols-2 gap-3">
            {styles.map((s) => (
              <motion.button
                key={s.id}
                onClick={() => setStyle(s.id)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className={`p-3 rounded-xl text-left transition-all ${
                  style === s.id
                    ? "ring-2 ring-violet-500 bg-violet-50 border-violet-200"
                    : "border border-gray-200 bg-white hover:bg-gray-50"
                }`}
              >
                <div className="text-lg mb-0.5">{s.emoji}</div>
                <div className="text-sm font-medium text-gray-900">{s.label}</div>
                <div className="text-xs text-gray-500">{s.description}</div>
              </motion.button>
            ))}
          </div>
        </div>

        {/* Generate button */}
        <Button
          onClick={handleGenerate}
          disabled={!prompt.trim() || loading}
          className="w-full gap-2 bg-gradient-to-r from-violet-600 to-pink-500 hover:from-violet-700 hover:to-pink-600 text-white shadow-lg shadow-violet-500/20"
          size="lg"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Génération en cours...
            </>
          ) : (
            <>
              <Wand2 className="w-5 h-5" />
              Générer 4 variations
            </>
          )}
        </Button>

        {/* Variations grid */}
        <AnimatePresence>
          {variations.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="grid grid-cols-2 gap-3"
            >
              {variations.map((variation, index) => (
                <motion.button
                  key={index}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.1 }}
                  onClick={() => onPhotoGenerated(variation.image_url, variation.revised_prompt)}
                  whileHover={{ scale: 1.03 }}
                  className="relative aspect-square rounded-xl overflow-hidden group border-2 border-transparent hover:border-violet-400 transition-colors"
                >
                  <img
                    src={variation.image_url}
                    alt={`Variation ${index + 1}`}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end justify-center p-3">
                    <span className="text-white text-xs font-semibold bg-violet-600/80 px-3 py-1 rounded-full">
                      Sélectionner
                    </span>
                  </div>
                  <div className="absolute top-2 left-2">
                    <span className="text-xs bg-white/90 backdrop-blur-sm px-2 py-0.5 rounded-full text-gray-700 font-medium">
                      {styles.find(s => s.id === variation.style)?.emoji || ""}{" "}
                      {styles.find(s => s.id === variation.style)?.label || variation.style}
                    </span>
                  </div>
                </motion.button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </CardContent>
    </Card>
  );
}

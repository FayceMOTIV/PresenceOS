"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, ArrowRight, Loader2, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import type { OnboardingData } from "../page";

interface StepBrandVoiceProps {
  data: OnboardingData;
  updateData: (updates: Partial<OnboardingData>) => void;
  onNext: () => void;
  onBack: () => void;
  isLoading: boolean;
}

const TONE_SLIDERS = [
  {
    key: "tone_formal" as const,
    label: "Formalite",
    leftLabel: "Decontracte",
    rightLabel: "Formel",
    description: "Le niveau de formalite dans vos communications",
  },
  {
    key: "tone_playful" as const,
    label: "Ton",
    leftLabel: "Serieux",
    rightLabel: "Joueur",
    description: "L'aspect ludique de votre communication",
  },
  {
    key: "tone_bold" as const,
    label: "Audace",
    leftLabel: "Subtil",
    rightLabel: "Audacieux",
    description: "Osez-vous les formulations percutantes?",
  },
  {
    key: "tone_emotional" as const,
    label: "Emotion",
    leftLabel: "Rationnel",
    rightLabel: "Emotionnel",
    description: "Faites-vous appel aux emotions?",
  },
];

export function StepBrandVoice({
  data,
  updateData,
  onNext,
  onBack,
  isLoading,
}: StepBrandVoiceProps) {
  const [newAvoidWord, setNewAvoidWord] = useState("");
  const [newPreferWord, setNewPreferWord] = useState("");

  const handleAddWord = (
    type: "words_to_avoid" | "words_to_prefer",
    word: string,
    setWord: (v: string) => void
  ) => {
    if (word.trim()) {
      const current = data[type] || [];
      if (!current.includes(word.trim().toLowerCase())) {
        updateData({ [type]: [...current, word.trim().toLowerCase()] });
      }
      setWord("");
    }
  };

  const handleRemoveWord = (type: "words_to_avoid" | "words_to_prefer", word: string) => {
    updateData({ [type]: (data[type] || []).filter((w) => w !== word) });
  };

  const handleKeyDown = (
    e: React.KeyboardEvent,
    type: "words_to_avoid" | "words_to_prefer",
    word: string,
    setWord: (v: string) => void
  ) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddWord(type, word, setWord);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onNext();
  };

  return (
    <Card className="glass-card">
      <CardHeader>
        <CardTitle className="text-2xl">Ton & Personnalite</CardTitle>
        <CardDescription>
          Definissez la voix de votre marque. L&apos;IA utilisera ces parametres
          pour generer du contenu qui vous ressemble.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Tone sliders */}
          <div className="space-y-6">
            <Label className="text-base font-semibold">Curseurs de ton</Label>
            {TONE_SLIDERS.map((slider) => (
              <div key={slider.key} className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{slider.label}</span>
                  <span className="text-xs text-muted-foreground">
                    {data[slider.key]}%
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-xs text-muted-foreground w-20 text-right">
                    {slider.leftLabel}
                  </span>
                  <Slider
                    value={[data[slider.key]]}
                    onValueChange={([value]) => updateData({ [slider.key]: value })}
                    max={100}
                    step={5}
                    className="flex-1"
                  />
                  <span className="text-xs text-muted-foreground w-20">
                    {slider.rightLabel}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">{slider.description}</p>
              </div>
            ))}
          </div>

          {/* Words to avoid */}
          <div className="space-y-3">
            <Label>Mots a eviter</Label>
            <p className="text-xs text-muted-foreground">
              Mots ou expressions que l&apos;IA ne doit jamais utiliser
            </p>
            <div className="flex gap-2">
              <Input
                placeholder="Ex: prix bas, discount..."
                value={newAvoidWord}
                onChange={(e) => setNewAvoidWord(e.target.value)}
                onKeyDown={(e) =>
                  handleKeyDown(e, "words_to_avoid", newAvoidWord, setNewAvoidWord)
                }
              />
              <Button
                type="button"
                variant="outline"
                onClick={() =>
                  handleAddWord("words_to_avoid", newAvoidWord, setNewAvoidWord)
                }
              >
                Ajouter
              </Button>
            </div>
            {data.words_to_avoid.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {data.words_to_avoid.map((word) => (
                  <Badge
                    key={word}
                    variant="secondary"
                    className="cursor-pointer hover:bg-destructive hover:text-destructive-foreground"
                    onClick={() => handleRemoveWord("words_to_avoid", word)}
                  >
                    {word}
                    <X className="w-3 h-3 ml-1" />
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Words to prefer */}
          <div className="space-y-3">
            <Label>Mots a privilegier</Label>
            <p className="text-xs text-muted-foreground">
              Termes ou expressions propres a votre marque
            </p>
            <div className="flex gap-2">
              <Input
                placeholder="Ex: premium, artisanal..."
                value={newPreferWord}
                onChange={(e) => setNewPreferWord(e.target.value)}
                onKeyDown={(e) =>
                  handleKeyDown(e, "words_to_prefer", newPreferWord, setNewPreferWord)
                }
              />
              <Button
                type="button"
                variant="outline"
                onClick={() =>
                  handleAddWord("words_to_prefer", newPreferWord, setNewPreferWord)
                }
              >
                Ajouter
              </Button>
            </div>
            {data.words_to_prefer.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {data.words_to_prefer.map((word) => (
                  <Badge
                    key={word}
                    variant="secondary"
                    className="cursor-pointer hover:bg-primary hover:text-primary-foreground"
                    onClick={() => handleRemoveWord("words_to_prefer", word)}
                  >
                    {word}
                    <X className="w-3 h-3 ml-1" />
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Custom instructions */}
          <div className="space-y-2">
            <Label htmlFor="custom_instructions">Instructions personnalisees (optionnel)</Label>
            <Textarea
              id="custom_instructions"
              placeholder="Ex: Toujours tutoyer le lecteur, utiliser des references a la cuisine francaise..."
              value={data.custom_instructions}
              onChange={(e) => updateData({ custom_instructions: e.target.value })}
              rows={3}
            />
            <p className="text-xs text-muted-foreground">
              Ajoutez des consignes specifiques pour l&apos;IA.
            </p>
          </div>

          {/* Navigation */}
          <div className="flex justify-between pt-4">
            <Button type="button" variant="ghost" onClick={onBack}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Retour
            </Button>
            <Button type="submit" variant="gradient" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Sauvegarde...
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

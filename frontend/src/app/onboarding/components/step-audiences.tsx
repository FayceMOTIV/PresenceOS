"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ArrowLeft, ArrowRight, Loader2, MapPin, Target, X, Users } from "lucide-react";
import type { OnboardingData } from "../page";

interface StepAudiencesProps {
  data: OnboardingData;
  updateData: (updates: Partial<OnboardingData>) => void;
  onNext: () => void;
  onBack: () => void;
  isLoading: boolean;
}

const AGE_RANGES = [
  { value: "18-24", label: "18-24 ans (Gen Z)" },
  { value: "25-34", label: "25-34 ans (Millennials)" },
  { value: "35-44", label: "35-44 ans" },
  { value: "45-54", label: "45-54 ans" },
  { value: "55+", label: "55+ ans" },
  { value: "all", label: "Tous ages" },
];

const CONTENT_PILLARS = [
  {
    key: "education" as const,
    label: "Education",
    description: "Tutoriels, conseils, how-to",
    icon: "📚",
  },
  {
    key: "entertainment" as const,
    label: "Divertissement",
    description: "Humour, trends, fun",
    icon: "🎭",
  },
  {
    key: "engagement" as const,
    label: "Engagement",
    description: "Questions, sondages, UGC",
    icon: "💬",
  },
  {
    key: "promotion" as const,
    label: "Promotion",
    description: "Offres, produits, CTAs",
    icon: "📢",
  },
  {
    key: "behind_scenes" as const,
    label: "Coulisses",
    description: "Equipe, processus, authenticite",
    icon: "🎬",
  },
];

export function StepAudiences({
  data,
  updateData,
  onNext,
  onBack,
  isLoading,
}: StepAudiencesProps) {
  const [newInterest, setNewInterest] = useState("");
  const [newLocation, setNewLocation] = useState("");

  const handleAddInterest = () => {
    if (newInterest.trim()) {
      const current = data.target_persona.interests || [];
      if (!current.includes(newInterest.trim())) {
        updateData({
          target_persona: {
            ...data.target_persona,
            interests: [...current, newInterest.trim()],
          },
        });
      }
      setNewInterest("");
    }
  };

  const handleRemoveInterest = (interest: string) => {
    updateData({
      target_persona: {
        ...data.target_persona,
        interests: (data.target_persona.interests || []).filter((i) => i !== interest),
      },
    });
  };

  const handleAddLocation = () => {
    if (newLocation.trim()) {
      const current = data.locations || [];
      if (!current.includes(newLocation.trim())) {
        updateData({ locations: [...current, newLocation.trim()] });
      }
      setNewLocation("");
    }
  };

  const handleRemoveLocation = (location: string) => {
    updateData({
      locations: (data.locations || []).filter((l) => l !== location),
    });
  };

  const handlePillarChange = (key: keyof typeof data.content_pillars, value: number) => {
    updateData({
      content_pillars: {
        ...data.content_pillars,
        [key]: value,
      },
    });
  };

  const totalPillars = Object.values(data.content_pillars).reduce((a, b) => a + b, 0);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onNext();
  };

  return (
    <Card className="glass-card">
      <CardHeader>
        <CardTitle className="text-2xl">Vos audiences</CardTitle>
        <CardDescription>
          Definissez vos cibles et la repartition de votre contenu.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Target persona */}
          <div className="space-y-6">
            <div className="flex items-center gap-2">
              <Target className="w-5 h-5 text-primary" />
              <Label className="text-base font-semibold">Persona cible</Label>
            </div>

            {/* Persona name */}
            <div className="space-y-2">
              <Label htmlFor="persona_name">Nom du persona</Label>
              <Input
                id="persona_name"
                placeholder="Ex: Familles CSP+, Entrepreneurs tech..."
                value={data.target_persona.name}
                onChange={(e) =>
                  updateData({
                    target_persona: { ...data.target_persona, name: e.target.value },
                  })
                }
              />
            </div>

            {/* Age range */}
            <div className="space-y-2">
              <Label>Tranche d&apos;age</Label>
              <Select
                value={data.target_persona.age_range}
                onValueChange={(value) =>
                  updateData({
                    target_persona: { ...data.target_persona, age_range: value },
                  })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selectionnez une tranche d'age" />
                </SelectTrigger>
                <SelectContent>
                  {AGE_RANGES.map((range) => (
                    <SelectItem key={range.value} value={range.value}>
                      {range.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Interests */}
            <div className="space-y-2">
              <Label>Centres d&apos;interet</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="Ex: gastronomie, tech, voyages..."
                  value={newInterest}
                  onChange={(e) => setNewInterest(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleAddInterest();
                    }
                  }}
                />
                <Button type="button" variant="outline" onClick={handleAddInterest}>
                  Ajouter
                </Button>
              </div>
              {(data.target_persona.interests || []).length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {data.target_persona.interests?.map((interest) => (
                    <Badge
                      key={interest}
                      variant="secondary"
                      className="cursor-pointer"
                      onClick={() => handleRemoveInterest(interest)}
                    >
                      {interest}
                      <X className="w-3 h-3 ml-1" />
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Locations */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <MapPin className="w-5 h-5 text-primary" />
              <Label className="text-base font-semibold">Zones geographiques</Label>
            </div>
            <div className="flex gap-2">
              <Input
                placeholder="Ex: Paris, Lyon, France entiere..."
                value={newLocation}
                onChange={(e) => setNewLocation(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddLocation();
                  }
                }}
              />
              <Button type="button" variant="outline" onClick={handleAddLocation}>
                Ajouter
              </Button>
            </div>
            {data.locations.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {data.locations.map((location) => (
                  <Badge
                    key={location}
                    variant="secondary"
                    className="cursor-pointer"
                    onClick={() => handleRemoveLocation(location)}
                  >
                    <MapPin className="w-3 h-3 mr-1" />
                    {location}
                    <X className="w-3 h-3 ml-1" />
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Content pillars */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="w-5 h-5 text-primary" />
                <Label className="text-base font-semibold">Piliers de contenu</Label>
              </div>
              <span
                className={`text-sm ${
                  totalPillars === 100 ? "text-green-500" : "text-muted-foreground"
                }`}
              >
                Total: {totalPillars}%
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              Repartissez votre contenu entre ces 5 piliers (total = 100%)
            </p>

            <div className="space-y-4">
              {CONTENT_PILLARS.map((pillar) => (
                <div key={pillar.key} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span>{pillar.icon}</span>
                      <span className="text-sm font-medium">{pillar.label}</span>
                    </div>
                    <span className="text-sm text-muted-foreground">
                      {data.content_pillars[pillar.key]}%
                    </span>
                  </div>
                  <Slider
                    value={[data.content_pillars[pillar.key]]}
                    onValueChange={([value]) => handlePillarChange(pillar.key, value)}
                    max={100}
                    step={5}
                  />
                  <p className="text-xs text-muted-foreground">{pillar.description}</p>
                </div>
              ))}
            </div>
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

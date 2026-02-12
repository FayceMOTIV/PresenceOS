"use client";

import { useState, useEffect } from "react";
import { Loader2 } from "lucide-react";

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
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ContentIdea } from "@/types";
import { ideasApi } from "@/lib/api";
import { toast } from "@/hooks/use-toast";

interface EditIdeaDialogProps {
  idea: ContentIdea | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onIdeaUpdated: (idea: ContentIdea) => void;
}

const pillarOptions = [
  { value: "education", label: "Education" },
  { value: "entertainment", label: "Divertissement" },
  { value: "engagement", label: "Engagement" },
  { value: "promotion", label: "Promotion" },
  { value: "behind_scenes", label: "Coulisses" },
];

const platformOptions = [
  { value: "instagram_post", label: "Instagram" },
  { value: "linkedin", label: "LinkedIn" },
  { value: "tiktok", label: "TikTok" },
  { value: "facebook", label: "Facebook" },
];

export function EditIdeaDialog({
  idea,
  open,
  onOpenChange,
  onIdeaUpdated,
}: EditIdeaDialogProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [pillar, setPillar] = useState("");
  const [platforms, setPlatforms] = useState<string[]>([]);

  // Sync form with idea when dialog opens
  useEffect(() => {
    if (idea && open) {
      setTitle(idea.title);
      setDescription(idea.description || "");
      setPillar(idea.content_pillar || "");
      setPlatforms(idea.target_platforms || []);
    }
  }, [idea, open]);

  const handleSubmit = async () => {
    if (!idea) return;

    setIsSubmitting(true);
    try {
      const response = await ideasApi.update(idea.id, {
        title,
        description,
        content_pillar: pillar || undefined,
        target_platforms: platforms.length > 0 ? platforms : undefined,
      });

      const updatedIdea = response.data;
      onIdeaUpdated(updatedIdea);
      onOpenChange(false);

      toast({
        title: "Idee modifiee",
        description: `"${title}" a ete mise a jour`,
      });
    } catch (error) {
      console.error("Error updating idea:", error);
      toast({
        title: "Erreur",
        description: "Impossible de modifier l'idee",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const togglePlatform = (platform: string) => {
    setPlatforms((prev) =>
      prev.includes(platform)
        ? prev.filter((p) => p !== platform)
        : [...prev, platform]
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Modifier l&apos;idee</DialogTitle>
          <DialogDescription>
            Modifiez les details de votre idee de contenu.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="edit-title">Titre</Label>
            <Input
              id="edit-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Titre de l'idee"
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="edit-description">Description</Label>
            <Textarea
              id="edit-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Decrivez votre idee..."
              rows={3}
            />
          </div>

          {/* Pillar */}
          <div className="space-y-2">
            <Label htmlFor="edit-pillar">Pilier de contenu</Label>
            <Select value={pillar} onValueChange={setPillar}>
              <SelectTrigger id="edit-pillar">
                <SelectValue placeholder="Selectionnez un pilier" />
              </SelectTrigger>
              <SelectContent>
                {pillarOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Platforms */}
          <div className="space-y-2">
            <Label>Plateformes cibles</Label>
            <div className="flex flex-wrap gap-2">
              {platformOptions.map((option) => (
                <Button
                  key={option.value}
                  type="button"
                  variant={platforms.includes(option.value) ? "default" : "outline"}
                  size="sm"
                  onClick={() => togglePlatform(option.value)}
                >
                  {option.label}
                </Button>
              ))}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isSubmitting}
          >
            Annuler
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting || !title.trim()}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Enregistrement...
              </>
            ) : (
              "Enregistrer"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

"use client";

import { useState, useEffect } from "react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import { Loader2, Instagram, Linkedin, Facebook, Image, Video, FileText } from "lucide-react";

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
import { cn } from "@/lib/utils";
import { Platform, SocialConnector } from "@/types";

interface QuickCreateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedDate: Date | null;
  connectors: SocialConnector[];
  onSubmit: (data: QuickCreateData) => Promise<void>;
}

export interface QuickCreateData {
  title: string;
  caption: string;
  platform: Platform;
  mediaType: "image" | "video" | "text";
  scheduledDate: Date;
  connectorId: string;
}

const platforms = [
  { id: "instagram_post" as Platform, label: "Instagram", icon: Instagram, color: "from-purple-500 to-pink-500" },
  { id: "linkedin" as Platform, label: "LinkedIn", icon: Linkedin, color: "bg-[#0A66C2]" },
  { id: "facebook" as Platform, label: "Facebook", icon: Facebook, color: "bg-[#1877F2]" },
];

const mediaTypes = [
  { id: "image" as const, label: "Image", icon: Image },
  { id: "video" as const, label: "Video", icon: Video },
  { id: "text" as const, label: "Texte", icon: FileText },
];

function TikTokIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z" />
    </svg>
  );
}

export function QuickCreateDialog({
  open,
  onOpenChange,
  selectedDate,
  connectors,
  onSubmit,
}: QuickCreateDialogProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [title, setTitle] = useState("");
  const [caption, setCaption] = useState("");
  const [selectedPlatform, setSelectedPlatform] = useState<Platform>("instagram_post");
  const [selectedMediaType, setSelectedMediaType] = useState<"image" | "video" | "text">("image");

  // Reset form when dialog opens
  useEffect(() => {
    if (open) {
      setTitle("");
      setCaption("");
      setSelectedPlatform("instagram_post");
      setSelectedMediaType("image");
    }
  }, [open]);

  // Get available connectors for selected platform
  const platformMap: Record<string, string> = {
    instagram_post: "instagram",
    instagram_reel: "instagram",
    instagram_story: "instagram",
    tiktok: "tiktok",
    linkedin: "linkedin",
    facebook: "facebook",
  };

  const availableConnector = connectors.find(
    (c) => c.platform === platformMap[selectedPlatform] && c.status === "connected"
  );

  const handleSubmit = async () => {
    if (!selectedDate || !title.trim() || !caption.trim() || !availableConnector) return;

    setIsSubmitting(true);
    try {
      await onSubmit({
        title,
        caption,
        platform: selectedPlatform,
        mediaType: selectedMediaType,
        scheduledDate: selectedDate,
        connectorId: availableConnector.id,
      });
      onOpenChange(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  const formattedDate = selectedDate
    ? format(selectedDate, "EEEE d MMMM yyyy", { locale: fr })
    : "";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Nouveau post</DialogTitle>
          <DialogDescription className="capitalize">
            {formattedDate}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Platform selection */}
          <div className="space-y-2">
            <Label>Plateforme</Label>
            <div className="grid grid-cols-4 gap-2">
              {platforms.map((platform) => {
                const Icon = platform.icon;
                const isSelected = selectedPlatform === platform.id;
                const hasConnector = connectors.some(
                  (c) => c.platform === platformMap[platform.id] && c.status === "connected"
                );

                return (
                  <button
                    key={platform.id}
                    type="button"
                    onClick={() => setSelectedPlatform(platform.id)}
                    disabled={!hasConnector}
                    className={cn(
                      "flex flex-col items-center gap-1.5 p-3 rounded-lg border-2 transition-all",
                      isSelected
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-muted-foreground/50",
                      !hasConnector && "opacity-50 cursor-not-allowed"
                    )}
                  >
                    <div
                      className={cn(
                        "w-8 h-8 rounded-lg flex items-center justify-center",
                        isSelected ? "bg-gradient-to-r " + platform.color : "bg-muted"
                      )}
                    >
                      <Icon className={cn("w-4 h-4", isSelected ? "text-white" : "text-muted-foreground")} />
                    </div>
                    <span className="text-xs font-medium">{platform.label}</span>
                    {!hasConnector && (
                      <span className="text-[10px] text-muted-foreground">Non connecte</span>
                    )}
                  </button>
                );
              })}
              {/* TikTok */}
              <button
                type="button"
                onClick={() => setSelectedPlatform("tiktok" as Platform)}
                disabled={!connectors.some((c) => c.platform === "tiktok" && c.status === "connected")}
                className={cn(
                  "flex flex-col items-center gap-1.5 p-3 rounded-lg border-2 transition-all",
                  selectedPlatform === "tiktok"
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-muted-foreground/50",
                  !connectors.some((c) => c.platform === "tiktok" && c.status === "connected") &&
                    "opacity-50 cursor-not-allowed"
                )}
              >
                <div
                  className={cn(
                    "w-8 h-8 rounded-lg flex items-center justify-center",
                    selectedPlatform === "tiktok" ? "bg-black" : "bg-muted"
                  )}
                >
                  <TikTokIcon
                    className={cn(
                      "w-4 h-4",
                      selectedPlatform === "tiktok" ? "text-white" : "text-muted-foreground"
                    )}
                  />
                </div>
                <span className="text-xs font-medium">TikTok</span>
              </button>
            </div>
          </div>

          {/* Media type selection */}
          <div className="space-y-2">
            <Label>Format</Label>
            <div className="flex gap-2">
              {mediaTypes.map((type) => {
                const Icon = type.icon;
                const isSelected = selectedMediaType === type.id;

                return (
                  <button
                    key={type.id}
                    type="button"
                    onClick={() => setSelectedMediaType(type.id)}
                    className={cn(
                      "flex-1 flex items-center justify-center gap-2 p-2.5 rounded-lg border transition-all",
                      isSelected
                        ? "border-primary bg-primary/5 text-primary"
                        : "border-border hover:border-muted-foreground/50"
                    )}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="text-sm font-medium">{type.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title">Titre (interne)</Label>
            <Input
              id="title"
              placeholder="Ex: Promo weekend, Nouveau produit..."
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          {/* Caption */}
          <div className="space-y-2">
            <Label htmlFor="caption">Contenu</Label>
            <Textarea
              id="caption"
              placeholder="Ecrivez votre post ici..."
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              rows={4}
            />
            <p className="text-xs text-muted-foreground">
              {caption.length} caracteres
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Annuler
          </Button>
          <Button
            variant="gradient"
            onClick={handleSubmit}
            disabled={isSubmitting || !title.trim() || !caption.trim() || !availableConnector}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Creation...
              </>
            ) : (
              "Planifier"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

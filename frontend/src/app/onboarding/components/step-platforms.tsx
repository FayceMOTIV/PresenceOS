"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  ExternalLink,
  Instagram,
  Linkedin,
  Facebook,
  Key,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { connectorsApi } from "@/lib/api";
import { toast } from "@/hooks/use-toast";

interface StepPlatformsProps {
  brandId: string | null;
  onComplete: () => void;
  onBack: () => void;
}

// TikTok icon component
function TikTokIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="currentColor"
    >
      <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z" />
    </svg>
  );
}

type AuthMode = "oauth" | "apikey";

interface Platform {
  id: string;
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  connected: boolean;
  available: boolean;
  authMode: AuthMode;
  comingSoonMessage?: string;
}

export function StepPlatforms({ brandId, onComplete, onBack }: StepPlatformsProps) {
  const [platforms, setPlatforms] = useState<Platform[]>([
    {
      id: "linkedin",
      name: "LinkedIn",
      icon: Linkedin,
      color: "bg-[#0A66C2]",
      connected: false,
      available: true,
      authMode: "oauth",
    },
    {
      id: "facebook",
      name: "Facebook",
      icon: Facebook,
      color: "bg-[#1877F2]",
      connected: false,
      available: true,
      authMode: "apikey",
    },
    {
      id: "instagram",
      name: "Instagram",
      icon: Instagram,
      color: "bg-gradient-to-br from-[#833AB4] via-[#FD1D1D] to-[#F77737]",
      connected: false,
      available: true,
      authMode: "apikey",
    },
    {
      id: "tiktok",
      name: "TikTok",
      icon: TikTokIcon,
      color: "bg-black",
      connected: false,
      available: true,
      authMode: "apikey",
    },
  ]);
  const [connecting, setConnecting] = useState<string | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState<string>("");
  const [showApiKeyFor, setShowApiKeyFor] = useState<string | null>(null);

  const handleConnectOAuth = async (platformId: string) => {
    if (!brandId) {
      toast({
        title: "Erreur",
        description: "Brand ID manquant",
        variant: "destructive",
      });
      return;
    }

    setConnecting(platformId);

    try {
      const response = await connectorsApi.getOAuthUrl(platformId, brandId);
      const { oauth_url } = response.data;

      const popup = window.open(oauth_url, "oauth", "width=600,height=700");

      const handleMessage = (event: MessageEvent) => {
        if (event.data?.type === "oauth_callback") {
          if (event.data.success) {
            setPlatforms((prev) =>
              prev.map((p) =>
                p.id === platformId ? { ...p, connected: true } : p
              )
            );
            toast({
              title: "Connecte!",
              description: `Votre compte ${platformId} est connecte.`,
            });
          } else {
            toast({
              title: "Erreur de connexion",
              description: event.data.error || "La connexion a echoue",
              variant: "destructive",
            });
          }
          popup?.close();
          window.removeEventListener("message", handleMessage);
        }
      };

      window.addEventListener("message", handleMessage);

      setTimeout(() => {
        window.removeEventListener("message", handleMessage);
        setConnecting(null);
      }, 120000);
    } catch (error: any) {
      toast({
        title: "Erreur",
        description: error.response?.data?.detail || "Impossible de demarrer la connexion",
        variant: "destructive",
      });
    } finally {
      setConnecting(null);
    }
  };

  const handleSaveApiKey = async (platformId: string) => {
    if (!brandId || !apiKeyInput.trim()) {
      toast({
        title: "Erreur",
        description: "Cle API requise",
        variant: "destructive",
      });
      return;
    }

    setConnecting(platformId);

    try {
      await connectorsApi.connectWithApiKey(platformId, brandId, apiKeyInput.trim());

      setPlatforms((prev) =>
        prev.map((p) =>
          p.id === platformId ? { ...p, connected: true } : p
        )
      );
      toast({
        title: "Connecte!",
        description: `${platformId.charAt(0).toUpperCase() + platformId.slice(1)} connecte via Upload-Post.`,
      });
      setShowApiKeyFor(null);
      setApiKeyInput("");
    } catch (error: any) {
      toast({
        title: "Erreur",
        description: error.response?.data?.detail || "Impossible de sauvegarder la cle API",
        variant: "destructive",
      });
    } finally {
      setConnecting(null);
    }
  };

  const handleConnect = (platformId: string) => {
    const platform = platforms.find((p) => p.id === platformId);
    if (!platform) return;

    if (platform.authMode === "oauth") {
      handleConnectOAuth(platformId);
    } else {
      setShowApiKeyFor(platformId);
    }
  };

  const connectedCount = platforms.filter((p) => p.connected).length;

  return (
    <Card className="glass-card">
      <CardHeader>
        <CardTitle className="text-2xl">Connectez vos reseaux</CardTitle>
        <CardDescription>
          Liez vos comptes pour publier automatiquement. Vous pourrez ajouter
          d&apos;autres comptes plus tard.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Platform cards */}
        <div className="grid gap-4 sm:grid-cols-2">
          {platforms.map((platform) => {
            const Icon = platform.icon;
            const isConnecting = connecting === platform.id;
            const isShowingApiKey = showApiKeyFor === platform.id;

            return (
              <div
                key={platform.id}
                className={cn(
                  "relative rounded-xl border p-4 transition-all",
                  platform.connected
                    ? "border-green-500/50 bg-green-500/5"
                    : "border-border hover:border-primary/50"
                )}
              >
                {/* Connected badge */}
                {platform.connected && (
                  <Badge
                    variant="secondary"
                    className="absolute -top-2 -right-2 bg-green-500/10 text-green-500 border-green-500/20"
                  >
                    <Check className="w-3 h-3 mr-1" />
                    Connecte
                  </Badge>
                )}

                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className={cn(
                        "w-12 h-12 rounded-xl flex items-center justify-center",
                        platform.color
                      )}
                    >
                      <Icon className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h3 className="font-medium">
                        {platform.name}
                      </h3>
                      {platform.connected ? (
                        <p className="text-sm text-green-500 flex items-center gap-1">
                          <Check className="w-3 h-3" />
                          Connecte
                        </p>
                      ) : (
                        <p className="text-sm text-muted-foreground">
                          {platform.authMode === "apikey" ? "Via Upload-Post" : "OAuth"}
                        </p>
                      )}
                    </div>
                  </div>

                  {!platform.connected && !isShowingApiKey && (
                    <Button
                      size="sm"
                      variant="default"
                      onClick={() => handleConnect(platform.id)}
                      disabled={isConnecting}
                    >
                      {isConnecting ? (
                        "Connexion..."
                      ) : platform.authMode === "apikey" ? (
                        <>
                          <Key className="w-4 h-4 mr-1" />
                          Cle API
                        </>
                      ) : (
                        <>
                          <ExternalLink className="w-4 h-4 mr-1" />
                          Connecter
                        </>
                      )}
                    </Button>
                  )}

                  {platform.connected && (
                    <Button
                      size="sm"
                      variant="outline"
                      disabled
                    >
                      <Check className="w-4 h-4 mr-1" />
                      OK
                    </Button>
                  )}
                </div>

                {/* API Key input (for Upload-Post platforms) */}
                {isShowingApiKey && !platform.connected && (
                  <div className="mt-3 space-y-2">
                    <Input
                      type="password"
                      placeholder="Cle API Upload-Post"
                      value={apiKeyInput}
                      onChange={(e) => setApiKeyInput(e.target.value)}
                      autoFocus
                    />
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="default"
                        onClick={() => handleSaveApiKey(platform.id)}
                        disabled={isConnecting || !apiKeyInput.trim()}
                        className="flex-1"
                      >
                        {isConnecting ? "Enregistrement..." : "Enregistrer"}
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setShowApiKeyFor(null);
                          setApiKeyInput("");
                        }}
                      >
                        Annuler
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Info message */}
        <div className="bg-muted/50 rounded-lg p-4">
          <p className="text-sm text-muted-foreground">
            <strong>Conseil:</strong> Vous pouvez passer cette etape et connecter
            vos reseaux plus tard depuis les parametres. Au moins une connexion
            est recommandee pour profiter pleinement de PresenceOS.
          </p>
        </div>

        {/* Navigation */}
        <div className="flex justify-between pt-4">
          <Button type="button" variant="ghost" onClick={onBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Retour
          </Button>
          <Button variant="gradient" onClick={onComplete}>
            {connectedCount > 0 ? (
              <>
                Terminer
                <Check className="w-4 h-4 ml-2" />
              </>
            ) : (
              <>
                Passer pour l&apos;instant
                <ArrowRight className="w-4 h-4 ml-2" />
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

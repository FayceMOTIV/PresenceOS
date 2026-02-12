"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Zap,
  Play,
  Loader2,
  Check,
  X,
  MessageSquare,
  Clock,
  Sparkles,
  RefreshCw,
  Settings2,
  Eye,
} from "lucide-react";
import { autopilotApi } from "@/lib/api";
import { toast } from "@/hooks/use-toast";
import type { AutopilotConfig, PendingPost as PendingPostType } from "@/types";
import { cn } from "@/lib/utils";

const PLATFORM_OPTIONS = [
  { value: "instagram", label: "Instagram" },
  { value: "linkedin", label: "LinkedIn" },
  { value: "tiktok", label: "TikTok" },
  { value: "facebook", label: "Facebook" },
];

const FREQUENCY_OPTIONS = [
  { value: "daily", label: "Tous les jours" },
  { value: "weekdays", label: "Jours ouvres (Lun-Ven)" },
  { value: "3_per_week", label: "3x par semaine" },
  { value: "weekly", label: "1x par semaine" },
];

export default function AutopilotPage() {
  const [config, setConfig] = useState<AutopilotConfig | null>(null);
  const [pendingPosts, setPendingPosts] = useState<PendingPostType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // Form state
  const [platforms, setPlatforms] = useState<string[]>(["instagram"]);
  const [frequency, setFrequency] = useState("daily");
  const [autoPublish, setAutoPublish] = useState(false);
  const [approvalWindow, setApprovalWindow] = useState(4);
  const [whatsappEnabled, setWhatsappEnabled] = useState(false);
  const [whatsappPhone, setWhatsappPhone] = useState("");
  const [preferredTime, setPreferredTime] = useState("10:00");
  const [topics, setTopics] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    const brandId = localStorage.getItem("brand_id");
    if (!brandId) return;

    setIsLoading(true);
    try {
      // Load config
      try {
        const configRes = await autopilotApi.getConfig(brandId);
        const cfg = configRes.data;
        setConfig(cfg);
        // Populate form
        setPlatforms(cfg.platforms || ["instagram"]);
        setFrequency(cfg.frequency);
        setAutoPublish(cfg.auto_publish);
        setApprovalWindow(cfg.approval_window_hours);
        setWhatsappEnabled(cfg.whatsapp_enabled);
        setWhatsappPhone(cfg.whatsapp_phone || "");
        setPreferredTime(cfg.preferred_posting_time || "10:00");
        setTopics((cfg.topics || []).join(", "));
      } catch {
        // No config yet — show setup
        setConfig(null);
        setShowSettings(true);
      }

      // Load pending posts
      try {
        const pendingRes = await autopilotApi.listPending(brandId, { limit: 50 });
        setPendingPosts(pendingRes.data);
      } catch {
        setPendingPosts([]);
      }
    } catch (error) {
      console.error("Error loading autopilot data:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveConfig = async () => {
    const brandId = localStorage.getItem("brand_id");
    if (!brandId) return;

    setIsSaving(true);
    try {
      const data = {
        platforms,
        frequency,
        auto_publish: autoPublish,
        approval_window_hours: approvalWindow,
        whatsapp_enabled: whatsappEnabled,
        whatsapp_phone: whatsappPhone || undefined,
        preferred_posting_time: preferredTime || undefined,
        topics: topics ? topics.split(",").map((t) => t.trim()).filter(Boolean) : undefined,
      };

      if (config) {
        const res = await autopilotApi.updateConfig(brandId, data);
        setConfig(res.data);
      } else {
        const res = await autopilotApi.createConfig(brandId, data);
        setConfig(res.data);
      }

      toast({ title: "Configuration sauvegardee !" });
      setShowSettings(false);
    } catch (error: any) {
      toast({
        title: "Erreur",
        description: error.response?.data?.detail || "Impossible de sauvegarder",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleToggle = async () => {
    const brandId = localStorage.getItem("brand_id");
    if (!brandId || !config) return;

    try {
      const res = await autopilotApi.toggle(brandId);
      setConfig(res.data);
      toast({
        title: res.data.is_enabled ? "Autopilote active !" : "Autopilote desactive",
      });
    } catch (error: any) {
      toast({
        title: "Erreur",
        description: error.response?.data?.detail || "Impossible de basculer",
        variant: "destructive",
      });
    }
  };

  const handleGenerate = async () => {
    const brandId = localStorage.getItem("brand_id");
    if (!brandId) return;

    setIsGenerating(true);
    try {
      const res = await autopilotApi.triggerGeneration(brandId);
      const newPosts = res.data;
      setPendingPosts((prev) => [...newPosts, ...prev]);
      toast({
        title: "Contenu genere !",
        description: `${newPosts.length} post(s) en attente d'approbation.`,
      });
    } catch (error: any) {
      toast({
        title: "Erreur",
        description: error.response?.data?.detail || "Generation echouee",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleAction = async (postId: string, action: "approve" | "reject") => {
    try {
      const res = await autopilotApi.actionPending(postId, { action });
      setPendingPosts((prev) =>
        prev.map((p) => (p.id === postId ? res.data : p))
      );
      toast({
        title: action === "approve" ? "Post approuve !" : "Post rejete",
      });
    } catch (error: any) {
      toast({
        title: "Erreur",
        description: error.response?.data?.detail || "Action echouee",
        variant: "destructive",
      });
    }
  };

  const pendingCount = pendingPosts.filter((p) => p.status === "pending").length;
  const approvedCount = pendingPosts.filter(
    (p) => p.status === "approved" || p.status === "auto_published"
  ).length;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Zap className="w-8 h-8 text-green-500" />
            Mode Autopilote
          </h1>
          <p className="text-muted-foreground mt-1">
            Generation automatique de contenu avec approbation WhatsApp
          </p>
        </div>
        <div className="flex items-center gap-3">
          {config && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSettings(!showSettings)}
              >
                <Settings2 className="w-4 h-4 mr-2" />
                Parametres
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleGenerate}
                disabled={isGenerating || !config.is_enabled}
              >
                {isGenerating ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Sparkles className="w-4 h-4 mr-2" />
                )}
                Generer maintenant
              </Button>
              <div className="flex items-center gap-2 pl-3 border-l">
                <Switch
                  checked={config.is_enabled}
                  onCheckedChange={handleToggle}
                />
                <span className="text-sm font-medium">
                  {config.is_enabled ? "Actif" : "Inactif"}
                </span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Stats */}
      {config && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            {
              label: "Statut",
              value: config.is_enabled ? "Actif" : "Inactif",
              color: config.is_enabled ? "text-green-500" : "text-muted-foreground",
              icon: Zap,
            },
            {
              label: "En attente",
              value: pendingCount,
              color: pendingCount > 0 ? "text-amber-500" : "text-muted-foreground",
              icon: Clock,
            },
            {
              label: "Generes",
              value: config.total_generated,
              color: "text-primary",
              icon: Sparkles,
            },
            {
              label: "Publies",
              value: config.total_published,
              color: "text-green-500",
              icon: Check,
            },
          ].map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              <Card className="bento-card">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">{stat.label}</p>
                      <p className={cn("text-2xl font-bold mt-1", stat.color)}>
                        {stat.value}
                      </p>
                    </div>
                    <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center">
                      <stat.icon className={cn("w-5 h-5", stat.color)} />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      {/* Settings Panel */}
      <AnimatePresence>
        {(showSettings || !config) && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Card>
              <CardHeader>
                <CardTitle>Configuration Autopilote</CardTitle>
                <CardDescription>
                  Definissez comment l&apos;IA genere et publie votre contenu
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Platforms */}
                <div className="space-y-2">
                  <Label>Plateformes cibles</Label>
                  <div className="flex flex-wrap gap-2">
                    {PLATFORM_OPTIONS.map((p) => (
                      <Button
                        key={p.value}
                        variant={platforms.includes(p.value) ? "default" : "outline"}
                        size="sm"
                        onClick={() =>
                          setPlatforms((prev) =>
                            prev.includes(p.value)
                              ? prev.filter((v) => v !== p.value)
                              : [...prev, p.value]
                          )
                        }
                      >
                        {p.label}
                      </Button>
                    ))}
                  </div>
                </div>

                {/* Frequency */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Frequence de generation</Label>
                    <Select value={frequency} onValueChange={setFrequency}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {FREQUENCY_OPTIONS.map((f) => (
                          <SelectItem key={f.value} value={f.value}>
                            {f.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Heure de publication preferee</Label>
                    <Input
                      type="time"
                      value={preferredTime}
                      onChange={(e) => setPreferredTime(e.target.value)}
                    />
                  </div>
                </div>

                {/* Auto-publish */}
                <div className="flex items-center justify-between rounded-lg border p-4">
                  <div>
                    <Label>Auto-publication</Label>
                    <p className="text-sm text-muted-foreground">
                      Publier automatiquement si pas de reponse dans le delai
                    </p>
                  </div>
                  <Switch checked={autoPublish} onCheckedChange={setAutoPublish} />
                </div>

                {autoPublish && (
                  <div className="space-y-2">
                    <Label>Delai avant auto-publication (heures)</Label>
                    <Select
                      value={approvalWindow.toString()}
                      onValueChange={(v) => setApprovalWindow(parseInt(v))}
                    >
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {[1, 2, 3, 4, 6, 8, 12, 24].map((h) => (
                          <SelectItem key={h} value={h.toString()}>
                            {h}h
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                {/* WhatsApp */}
                <div className="flex items-center justify-between rounded-lg border p-4">
                  <div>
                    <Label className="flex items-center gap-2">
                      <MessageSquare className="w-4 h-4 text-green-500" />
                      Notifications WhatsApp
                    </Label>
                    <p className="text-sm text-muted-foreground">
                      Recevoir les posts pour approbation sur WhatsApp
                    </p>
                  </div>
                  <Switch
                    checked={whatsappEnabled}
                    onCheckedChange={setWhatsappEnabled}
                  />
                </div>

                {whatsappEnabled && (
                  <div className="space-y-2">
                    <Label>Numero WhatsApp (format international)</Label>
                    <Input
                      placeholder="+33612345678"
                      value={whatsappPhone}
                      onChange={(e) => setWhatsappPhone(e.target.value)}
                    />
                  </div>
                )}

                {/* Topics */}
                <div className="space-y-2">
                  <Label>Themes/sujets (optionnel, separes par virgule)</Label>
                  <Input
                    placeholder="marketing digital, growth hacking, IA"
                    value={topics}
                    onChange={(e) => setTopics(e.target.value)}
                  />
                </div>

                <Button
                  onClick={handleSaveConfig}
                  disabled={isSaving || platforms.length === 0}
                  className="w-full"
                  variant="gradient"
                >
                  {isSaving ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Check className="w-4 h-4 mr-2" />
                  )}
                  {config ? "Mettre a jour" : "Activer l'autopilote"}
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Pending Posts */}
      {pendingPosts.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Posts en file d&apos;attente</h2>
            <Button variant="ghost" size="sm" onClick={loadData}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Actualiser
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {pendingPosts.map((post, index) => (
              <motion.div
                key={post.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card
                  className={cn(
                    "overflow-hidden",
                    post.status === "pending" && "border-amber-500/30",
                    post.status === "approved" && "border-green-500/30",
                    post.status === "rejected" && "border-red-500/30",
                    post.status === "auto_published" && "border-blue-500/30"
                  )}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={
                            post.status === "pending"
                              ? "outline"
                              : post.status === "approved" ||
                                post.status === "auto_published"
                              ? "default"
                              : "destructive"
                          }
                        >
                          {post.status === "pending" && "En attente"}
                          {post.status === "approved" && "Approuve"}
                          {post.status === "rejected" && "Rejete"}
                          {post.status === "auto_published" && "Auto-publie"}
                          {post.status === "expired" && "Expire"}
                        </Badge>
                        <Badge variant="secondary">{post.platform}</Badge>
                      </div>
                      {post.virality_score && (
                        <span className="text-xs text-muted-foreground">
                          Score: {post.virality_score}/10
                        </span>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <p className="text-sm whitespace-pre-wrap line-clamp-6">
                      {post.caption}
                    </p>

                    {post.hashtags && post.hashtags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {post.hashtags.slice(0, 5).map((tag) => (
                          <span
                            key={tag}
                            className="text-xs text-primary bg-primary/10 px-2 py-0.5 rounded-full"
                          >
                            #{tag}
                          </span>
                        ))}
                      </div>
                    )}

                    {post.ai_reasoning && (
                      <p className="text-xs text-muted-foreground italic">
                        {post.ai_reasoning}
                      </p>
                    )}

                    {post.status === "pending" && (
                      <div className="flex items-center gap-2 pt-2 border-t">
                        <Button
                          size="sm"
                          variant="default"
                          className="flex-1 bg-green-600 hover:bg-green-700"
                          onClick={() => handleAction(post.id, "approve")}
                        >
                          <Check className="w-4 h-4 mr-1" />
                          Approuver
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="flex-1"
                          onClick={() => handleAction(post.id, "reject")}
                        >
                          <X className="w-4 h-4 mr-1" />
                          Rejeter
                        </Button>
                      </div>
                    )}

                    {post.expires_at && post.status === "pending" && (
                      <p className="text-xs text-muted-foreground text-center">
                        Expire le{" "}
                        {new Date(post.expires_at).toLocaleString("fr-FR", {
                          dateStyle: "short",
                          timeStyle: "short",
                        })}
                      </p>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {config && pendingPosts.length === 0 && !showSettings && (
        <Card className="text-center py-12">
          <CardContent>
            <Zap className="w-12 h-12 mx-auto text-muted-foreground/50 mb-4" />
            <h3 className="text-lg font-semibold mb-2">
              Aucun post en attente
            </h3>
            <p className="text-muted-foreground mb-4">
              {config.is_enabled
                ? "Les posts seront generes automatiquement selon votre planning."
                : "Activez l'autopilote pour commencer la generation automatique."}
            </p>
            {config.is_enabled && (
              <Button
                variant="outline"
                onClick={handleGenerate}
                disabled={isGenerating}
              >
                {isGenerating ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Play className="w-4 h-4 mr-2" />
                )}
                Generer un post maintenant
              </Button>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

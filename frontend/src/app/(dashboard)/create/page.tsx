"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, Camera, MessageSquare, Loader2, AlertCircle, RotateCcw } from "lucide-react";

import { useContentCreator } from "@/hooks/useContentCreator";
import { usePhotoCaptions } from "@/hooks/usePhotoCaptions";
import { DropZone } from "@/components/create/DropZone";
import { AIMessageStream } from "@/components/create/AIMessageStream";
import { ChatInput } from "@/components/create/ChatInput";
import { PostPreview } from "@/components/create/PostPreview";
import { PlatformSelector } from "@/components/create/PlatformSelector";
import { PublishCelebration } from "@/components/create/PublishCelebration";
import { CaptionSuggestions } from "@/components/create/CaptionSuggestions";
import { CaptionEditor } from "@/components/create/CaptionEditor";
import { MultiPlatformPreview } from "@/components/create/MultiPlatformPreview";
import { BrandOnboardingWizard } from "@/components/onboarding";
import { workspacesApi, brandsApi } from "@/lib/api";

type CreateMode = "visual" | "chat";

// UUID v4 format check
const isValidUUID = (s: string) =>
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(s);

export default function CreatePage() {
  const [mode, setMode] = useState<CreateMode>("visual");
  const [brandName, setBrandName] = useState("Restaurant");
  const [showMobilePreview, setShowMobilePreview] = useState(false);
  const [brandId, setBrandId] = useState<string | null>(null);
  const [needsOnboarding, setNeedsOnboarding] = useState(false);
  const [brandLoading, setBrandLoading] = useState(true);

  // Chat mode hook
  const chatHook = useContentCreator();

  // Visual mode hook
  const visualHook = usePhotoCaptions();

  // Resolve brand_id on mount: check localStorage, then fetch from workspace
  useEffect(() => {
    async function resolveBrand() {
      // 1. Check localStorage for existing brand_id
      const saved = localStorage.getItem("brand_id");
      if (saved && isValidUUID(saved)) {
        try {
          const res = await brandsApi.get(saved);
          setBrandId(saved);
          setBrandName(res.data.name || "Restaurant");
          // Check if brand needs onboarding (no description = never onboarded)
          if (!res.data.description) {
            setNeedsOnboarding(true);
          }
          setBrandLoading(false);
          return;
        } catch {
          // Brand doesn't exist anymore, clear and fall through
          localStorage.removeItem("brand_id");
        }
      }

      // 2. Try to find a brand from the workspace
      const wsId = localStorage.getItem("workspace_id");
      if (wsId) {
        try {
          const res = await workspacesApi.getBrands(wsId);
          const brands = res.data;
          if (Array.isArray(brands) && brands.length > 0) {
            const first = brands[0];
            if (first.id && isValidUUID(first.id)) {
              localStorage.setItem("brand_id", first.id);
              setBrandId(first.id);
              setBrandName(first.name || "Restaurant");
              if (!first.description) {
                setNeedsOnboarding(true);
              }
              setBrandLoading(false);
              return;
            }
          }
        } catch {
          // Fall through
        }
      }

      // 3. No valid brand found — need onboarding or show error
      setNeedsOnboarding(true);
      setBrandLoading(false);
    }

    resolveBrand();
  }, []);

  // Chat mode helpers
  const handleTogglePlatform = (platform: string) => {
    chatHook.setPlatforms((prev: string[]) =>
      prev.includes(platform)
        ? prev.filter((p: string) => p !== platform)
        : [...prev, platform]
    );
  };

  const showChat = chatHook.step !== "upload" || chatHook.messages.length > 0;
  const showPreview = chatHook.step === "preview" || chatHook.step === "publishing" || chatHook.caption;

  // Visual mode: handle file drop
  const handleVisualFileDrop = useCallback(
    (file: File) => {
      visualHook.uploadAndAnalyze(file);
    },
    [visualHook.uploadAndAnalyze]
  );

  // Visual mode: save draft (placeholder)
  const handleSaveDraft = useCallback(() => {
    // TODO: integrate with content draft API
    alert("Brouillon sauvegarde !");
    visualHook.reset();
  }, [visualHook.reset]);

  // Brand onboarding completed
  const handleOnboardingComplete = useCallback((brandData: any) => {
    localStorage.setItem("brand_id", brandData.id);
    setBrandId(brandData.id);
    setBrandName(brandData.name || "Restaurant");
    setNeedsOnboarding(false);
  }, []);

  // Loading state
  if (brandLoading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  // Onboarding needed
  if (needsOnboarding && brandId) {
    return <BrandOnboardingWizard brandId={brandId} onComplete={handleOnboardingComplete} />;
  }

  // No brand at all (no workspace, no brands created)
  if (!brandId) {
    return (
      <div className="max-w-md mx-auto py-20 text-center space-y-4">
        <AlertCircle className="w-12 h-12 text-muted-foreground mx-auto" />
        <h2 className="text-xl font-bold text-foreground">Aucune marque configuree</h2>
        <p className="text-sm text-muted-foreground">
          Creez un workspace et une marque pour commencer a publier.
        </p>
      </div>
    );
  }

  return (
    <>
      {/* Celebration overlay (chat mode) */}
      <AnimatePresence>
        {mode === "chat" && chatHook.step === "published" && (
          <PublishCelebration onReset={chatHook.reset} />
        )}
      </AnimatePresence>

      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-8"
        >
          <div>
            <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-primary" />
              Creer une publication
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              {mode === "visual"
                ? "Depose une photo, choisis ton style, publie"
                : "Depose une photo, l'IA fait le reste"}
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Mode toggle */}
            <div className="flex items-center bg-secondary rounded-xl p-1">
              <button
                onClick={() => setMode("visual")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  mode === "visual"
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Camera className="w-4 h-4" />
                Visuel
              </button>
              <button
                onClick={() => setMode("chat")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  mode === "chat"
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <MessageSquare className="w-4 h-4" />
                Chat
              </button>
            </div>

            {/* Mobile preview toggle (chat mode only) */}
            {mode === "chat" && showPreview && (
              <button
                onClick={() => setShowMobilePreview(!showMobilePreview)}
                className="lg:hidden px-3 py-1.5 rounded-lg bg-secondary text-sm font-medium text-foreground"
              >
                {showMobilePreview ? "Chat" : "Preview"}
              </button>
            )}
          </div>
        </motion.div>

        {/* ============ VISUAL MODE ============ */}
        {mode === "visual" && (
          <AnimatePresence mode="wait">
            {/* Step: Upload */}
            {visualHook.step === "upload" && (
              <motion.div
                key="visual-upload"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="max-w-2xl mx-auto"
              >
                <DropZone
                  photoUrls={[]}
                  onFileDrop={handleVisualFileDrop}
                  disabled={false}
                />
                {visualHook.error && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="mt-4 flex items-center gap-2 text-sm text-red-500 bg-red-500/10 rounded-xl px-4 py-3"
                  >
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    {visualHook.error}
                  </motion.div>
                )}
              </motion.div>
            )}

            {/* Step: Analyzing */}
            {visualHook.step === "analyzing" && (
              <motion.div
                key="visual-analyzing"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex gap-6 items-start max-w-5xl mx-auto"
              >
                {/* Photo preview */}
                <div className="w-[280px] flex-shrink-0">
                  {visualHook.photoPreviewUrl && (
                    <div className="rounded-2xl overflow-hidden border border-border/50 shadow-lg">
                      <img
                        src={visualHook.photoPreviewUrl}
                        alt="Photo"
                        className="w-full h-auto object-cover"
                      />
                    </div>
                  )}
                </div>
                {/* Skeleton loading */}
                <div className="flex-1 space-y-4">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Analyse de la photo en cours...
                  </div>
                  {[1, 2, 3].map((i) => (
                    <div
                      key={i}
                      className="rounded-2xl border border-border/50 p-4 space-y-3 animate-pulse"
                    >
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-muted" />
                        <div className="h-4 w-32 rounded bg-muted" />
                        <div className="ml-auto h-5 w-14 rounded-full bg-muted" />
                      </div>
                      <div className="space-y-2">
                        <div className="h-3 w-full rounded bg-muted" />
                        <div className="h-3 w-3/4 rounded bg-muted" />
                      </div>
                      <div className="flex justify-between">
                        <div className="h-3 w-20 rounded bg-muted" />
                        <div className="h-3 w-32 rounded bg-muted" />
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Step: Suggestions */}
            {visualHook.step === "suggestions" && visualHook.imageAnalysis && (
              <motion.div
                key="visual-suggestions"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="max-w-5xl mx-auto"
              >
                <CaptionSuggestions
                  suggestions={visualHook.suggestions}
                  engagementScores={visualHook.engagementScores}
                  imageAnalysis={visualHook.imageAnalysis}
                  photoPreviewUrl={visualHook.photoPreviewUrl}
                  onSelect={visualHook.selectSuggestion}
                  onRegenerateAll={visualHook.regenerateAll}
                  isAnalyzing={visualHook.isAnalyzing}
                />
              </motion.div>
            )}

            {/* Step: Editing */}
            {visualHook.step === "editing" && visualHook.selectedStyle && (
              <motion.div
                key="visual-editing"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="max-w-5xl mx-auto"
              >
                <div className="flex gap-8 items-start">
                  {/* Left: Editor */}
                  <div className="flex-1 min-w-0">
                    <CaptionEditor
                      caption={visualHook.editedCaption}
                      hashtags={visualHook.editedHashtags}
                      selectedStyle={visualHook.selectedStyle}
                      currentTone={visualHook.currentTone}
                      onCaptionChange={visualHook.setEditedCaption}
                      onHashtagsChange={visualHook.setEditedHashtags}
                      onRegenerateHashtags={visualHook.regenerateHashtags}
                      onChangeTone={visualHook.changeTone}
                      onSuggestEmojis={visualHook.suggestEmojis}
                      onValidate={visualHook.goToValidation}
                      onBack={visualHook.goBackToSuggestions}
                      isRegeneratingHashtags={visualHook.isRegeneratingHashtags}
                      isChangingTone={visualHook.isChangingTone}
                      isSuggestingEmojis={visualHook.isSuggestingEmojis}
                      platform={visualHook.platforms[0]}
                    />
                  </div>

                  {/* Right: Live preview */}
                  <div className="w-[380px] flex-shrink-0 sticky top-8 hidden lg:block">
                    <PostPreview
                      photoUrl={visualHook.photoPreviewUrl}
                      caption={visualHook.editedCaption}
                      brandName={brandName}
                      platform={visualHook.platforms[0]}
                    />
                  </div>
                </div>
              </motion.div>
            )}

            {/* Step: Validating */}
            {visualHook.step === "validating" && (
              <motion.div
                key="visual-validating"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="max-w-4xl mx-auto"
              >
                <MultiPlatformPreview
                  photoUrl={visualHook.photoPreviewUrl}
                  caption={visualHook.editedCaption}
                  hashtags={visualHook.editedHashtags}
                  brandName={brandName}
                  platforms={visualHook.platforms.length > 0 ? visualHook.platforms : ["instagram_post", "facebook", "linkedin"]}
                  engagementScore={visualHook.engagementScores.current}
                  onBack={visualHook.goBackToEditing}
                  onSave={handleSaveDraft}
                />
              </motion.div>
            )}
          </AnimatePresence>
        )}

        {/* ============ CHAT MODE ============ */}
        {mode === "chat" && (
          <div className="flex gap-8 items-start">
            {/* LEFT -- Upload & Chat */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className={`flex-1 min-w-0 space-y-6 ${showMobilePreview ? "hidden lg:block" : ""}`}
            >
              {/* Drop Zone */}
              <DropZone
                photoUrls={chatHook.photoUrls}
                onFileDrop={chatHook.uploadPhoto}
                disabled={chatHook.isLoading}
              />

              {/* AI Message Stream */}
              {showChat && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="glass-card rounded-2xl p-4 space-y-4"
                >
                  <div className="max-h-[400px] flex flex-col">
                    <AIMessageStream
                      messages={chatHook.messages}
                      isLoading={chatHook.isLoading}
                      onClickButton={chatHook.clickButton}
                    />
                  </div>
                </motion.div>
              )}

              {/* Chat input */}
              <ChatInput
                onSend={chatHook.sendText}
                disabled={chatHook.isLoading}
                placeholder={
                  chatHook.step === "upload"
                    ? "Depose une photo ou decris ce que tu veux publier..."
                    : chatHook.step === "enriching"
                    ? "Ajoute un prix, une promo, des horaires..."
                    : chatHook.step === "preview"
                    ? "Dis-moi ce que tu veux modifier..."
                    : "Ecris un message..."
                }
              />
            </motion.div>

            {/* RIGHT -- Preview */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className={`w-[400px] flex-shrink-0 space-y-6 sticky top-8 ${
                showMobilePreview ? "" : "hidden lg:block"
              }`}
            >
              <PostPreview
                photoUrl={chatHook.photoUrls[0] || null}
                caption={chatHook.caption}
                brandName={brandName}
                platform={chatHook.platforms[0] || "instagram"}
              />

              {/* Platform selector */}
              <div className="space-y-2">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Plateformes
                </p>
                <PlatformSelector
                  platforms={chatHook.platforms}
                  onToggle={handleTogglePlatform}
                />
              </div>

              {/* Stats */}
              {chatHook.caption && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="grid grid-cols-2 gap-3"
                >
                  <div className="glass-card rounded-xl p-3 text-center">
                    <p className="text-lg font-bold text-foreground">
                      {chatHook.caption.split(/\s+/).length}
                    </p>
                    <p className="text-[10px] text-muted-foreground uppercase">Mots</p>
                  </div>
                  <div className="glass-card rounded-xl p-3 text-center">
                    <p className="text-lg font-bold text-foreground">
                      {(chatHook.caption.match(/#\w+/g) || []).length}
                    </p>
                    <p className="text-[10px] text-muted-foreground uppercase">Hashtags</p>
                  </div>
                </motion.div>
              )}
            </motion.div>
          </div>
        )}
      </div>
    </>
  );
}

"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles } from "lucide-react";

import { useContentCreator } from "@/hooks/useContentCreator";
import { DropZone } from "@/components/create/DropZone";
import { AIMessageStream } from "@/components/create/AIMessageStream";
import { ChatInput } from "@/components/create/ChatInput";
import { PostPreview } from "@/components/create/PostPreview";
import { PlatformSelector } from "@/components/create/PlatformSelector";
import { PublishCelebration } from "@/components/create/PublishCelebration";

export default function CreatePage() {
  const {
    step,
    photoUrls,
    messages,
    caption,
    platforms,
    setPlatforms,
    isLoading,
    uploadPhoto,
    sendText,
    clickButton,
    reset,
  } = useContentCreator();

  const [brandName, setBrandName] = useState("Restaurant");
  const [showMobilePreview, setShowMobilePreview] = useState(false);

  useEffect(() => {
    // Read brand name from localStorage or default
    const savedBrandId = localStorage.getItem("brand_id");
    if (savedBrandId) {
      // We'll use a simple approach — brand name shown in preview
      setBrandName("Family's");
    }
  }, []);

  const handleTogglePlatform = (platform: string) => {
    setPlatforms((prev: string[]) =>
      prev.includes(platform)
        ? prev.filter((p: string) => p !== platform)
        : [...prev, platform]
    );
  };

  const showChat = step !== "upload" || messages.length > 0;
  const showPreview = step === "preview" || step === "publishing" || caption;

  return (
    <>
      {/* Celebration overlay */}
      <AnimatePresence>
        {step === "published" && <PublishCelebration onReset={reset} />}
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
              Depose une photo, l&apos;IA fait le reste
            </p>
          </div>

          {/* Mobile preview toggle */}
          {showPreview && (
            <button
              onClick={() => setShowMobilePreview(!showMobilePreview)}
              className="lg:hidden px-3 py-1.5 rounded-lg bg-secondary text-sm font-medium text-foreground"
            >
              {showMobilePreview ? "Chat" : "Preview"}
            </button>
          )}
        </motion.div>

        {/* Main layout */}
        <div className="flex gap-8 items-start">
          {/* LEFT — Upload & Chat */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className={`flex-1 min-w-0 space-y-6 ${showMobilePreview ? "hidden lg:block" : ""}`}
          >
            {/* Drop Zone */}
            <DropZone
              photoUrls={photoUrls}
              onFileDrop={uploadPhoto}
              disabled={isLoading}
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
                    messages={messages}
                    isLoading={isLoading}
                    onClickButton={clickButton}
                  />
                </div>
              </motion.div>
            )}

            {/* Chat input — always visible */}
            <ChatInput
              onSend={sendText}
              disabled={isLoading}
              placeholder={
                step === "upload"
                  ? "Depose une photo ou decris ce que tu veux publier..."
                  : step === "enriching"
                  ? "Ajoute un prix, une promo, des horaires..."
                  : step === "preview"
                  ? "Dis-moi ce que tu veux modifier..."
                  : "Ecris un message..."
              }
            />
          </motion.div>

          {/* RIGHT — Preview */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className={`w-[400px] flex-shrink-0 space-y-6 sticky top-8 ${
              showMobilePreview ? "" : "hidden lg:block"
            }`}
          >
            <PostPreview
              photoUrl={photoUrls[0] || null}
              caption={caption}
              brandName={brandName}
              platform={platforms[0] || "instagram"}
            />

            {/* Platform selector */}
            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Plateformes
              </p>
              <PlatformSelector
                platforms={platforms}
                onToggle={handleTogglePlatform}
              />
            </div>

            {/* Stats */}
            {caption && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="grid grid-cols-2 gap-3"
              >
                <div className="glass-card rounded-xl p-3 text-center">
                  <p className="text-lg font-bold text-foreground">
                    {caption.split(/\s+/).length}
                  </p>
                  <p className="text-[10px] text-muted-foreground uppercase">Mots</p>
                </div>
                <div className="glass-card rounded-xl p-3 text-center">
                  <p className="text-lg font-bold text-foreground">
                    {(caption.match(/#\w+/g) || []).length}
                  </p>
                  <p className="text-[10px] text-muted-foreground uppercase">Hashtags</p>
                </div>
              </motion.div>
            )}
          </motion.div>
        </div>
      </div>
    </>
  );
}

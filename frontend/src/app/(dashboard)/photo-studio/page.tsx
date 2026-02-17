"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Camera, Sparkles } from "lucide-react";
import PhotoGenerator from "@/components/studio/PhotoGenerator";
import PostPreview from "@/components/studio/PostPreview";
import { HelpTooltip } from "@/components/ui/help-tooltip";

export default function PhotoStudioPage() {
  const [generatedPhoto, setGeneratedPhoto] = useState<string | null>(null);
  const [caption, setCaption] = useState("");
  const [revisedPrompt, setRevisedPrompt] = useState<string>("");

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center gap-3 mb-1">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-pink-500 flex items-center justify-center shadow-lg shadow-violet-500/20">
            <Camera className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              Photo Studio IA
              <HelpTooltip content="Décrivez la photo souhaitée, choisissez un style, et l'IA génère 4 variations haute qualité avec DALL-E 3" />
            </h1>
            <p className="text-sm text-gray-500">
              Créez des visuels professionnels en quelques secondes avec DALL-E 3
            </p>
          </div>
        </div>
      </motion.div>

      {/* Content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Generator */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
        >
          <PhotoGenerator
            onPhotoGenerated={(url, revised) => {
              setGeneratedPhoto(url);
              setRevisedPrompt(revised || "");
              if (!caption) {
                setCaption("✨ Créé avec l'IA\n\n#food #restaurant #foodphotography #instafood");
              }
            }}
          />
        </motion.div>

        {/* Right: Preview */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="lg:sticky lg:top-6 self-start"
        >
          <PostPreview
            photo={generatedPhoto}
            caption={caption}
            onCaptionChange={setCaption}
          />

          {/* Revised prompt info */}
          {revisedPrompt && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-4 p-4 rounded-xl bg-violet-50 border border-violet-200/60"
            >
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-4 h-4 text-violet-600" />
                <span className="text-sm font-medium text-violet-700">Prompt enrichi par DALL-E</span>
              </div>
              <p className="text-xs text-violet-600/80 leading-relaxed">
                {revisedPrompt}
              </p>
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  );
}

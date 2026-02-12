"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Heart, MessageCircle, Send, Bookmark } from "lucide-react";

interface PostPreviewProps {
  photoUrl: string | null;
  caption: string;
  brandName: string;
  platform: string;
}

export function PostPreview({ photoUrl, caption, brandName, platform }: PostPreviewProps) {
  const brandInitial = brandName.charAt(0).toUpperCase();

  // Split caption into text and hashtags
  const parts = caption.split(/(#\w+)/g);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-[360px] mx-auto"
    >
      {/* Phone frame */}
      <div className="bg-secondary/50 rounded-[2rem] p-3 border border-border/50 shadow-2xl">
        {/* Status bar */}
        <div className="flex justify-between items-center px-4 py-1.5 text-[10px] text-muted-foreground">
          <span>9:41</span>
          <div className="w-20 h-5 bg-black rounded-full" />
          <span className="flex gap-0.5 items-center">
            <span>5G</span>
          </span>
        </div>

        {/* Instagram post card */}
        <div className="bg-background rounded-2xl overflow-hidden border border-border/30">
          {/* Header */}
          <div className="flex items-center gap-2.5 px-3 py-2.5">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-orange-600 flex items-center justify-center text-white text-xs font-bold">
              {brandInitial}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-foreground truncate">
                {brandName.toLowerCase().replace(/['\s]/g, "")}
              </p>
              <p className="text-[10px] text-muted-foreground">
                {platform === "instagram" ? "Instagram" : platform}
              </p>
            </div>
            <div className="text-muted-foreground text-lg leading-none">...</div>
          </div>

          {/* Image */}
          <div className="aspect-square bg-secondary relative overflow-hidden">
            <AnimatePresence mode="wait">
              {photoUrl ? (
                <motion.img
                  key={photoUrl}
                  initial={{ opacity: 0, scale: 1.05 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  src={photoUrl}
                  alt="Preview"
                  className="w-full h-full object-cover"
                />
              ) : (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="w-full h-full flex items-center justify-center"
                >
                  <div className="text-center text-muted-foreground">
                    <div className="w-12 h-12 rounded-xl bg-secondary/80 flex items-center justify-center mx-auto mb-2">
                      <Send className="w-6 h-6 opacity-30" />
                    </div>
                    <p className="text-xs">Preview apparaitra ici</p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Actions */}
          <div className="px-3 py-2 flex items-center justify-between">
            <div className="flex gap-4">
              <Heart className="w-5 h-5 text-foreground" />
              <MessageCircle className="w-5 h-5 text-foreground" />
              <Send className="w-5 h-5 text-foreground" />
            </div>
            <Bookmark className="w-5 h-5 text-foreground" />
          </div>

          {/* Caption */}
          <div className="px-3 pb-3">
            <AnimatePresence mode="wait">
              <motion.div
                key={caption || "empty"}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                {caption ? (
                  <p className="text-xs leading-relaxed">
                    <span className="font-semibold mr-1">
                      {brandName.toLowerCase().replace(/['\s]/g, "")}
                    </span>
                    {parts.map((part, i) =>
                      part.startsWith("#") ? (
                        <span key={i} className="text-primary/70">
                          {part}
                        </span>
                      ) : (
                        <span key={i}>{part}</span>
                      )
                    )}
                  </p>
                ) : (
                  <p className="text-xs text-muted-foreground italic">
                    La caption apparaitra ici...
                  </p>
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

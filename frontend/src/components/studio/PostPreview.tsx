"use client";

import { motion } from "framer-motion";
import { Heart, MessageCircle, Send, Bookmark, Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface PostPreviewProps {
  photo: string | null;
  caption: string;
  onCaptionChange?: (caption: string) => void;
}

export default function PostPreview({ photo, caption, onCaptionChange }: PostPreviewProps) {
  return (
    <Card className="border-violet-200/60">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-lg">
          <span className="text-xl">📱</span>
          Aperçu Instagram
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Instagram mock */}
        <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm">
          {/* IG Header */}
          <div className="p-3 flex items-center gap-3 border-b border-gray-100">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-pink-500 flex items-center justify-center">
              <span className="text-white text-xs font-bold">P</span>
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-900">votre_restaurant</p>
              <p className="text-xs text-gray-500">Paris, France</p>
            </div>
          </div>

          {/* Image */}
          <div className="aspect-square bg-gray-100 flex items-center justify-center">
            {photo ? (
              <motion.img
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                src={photo}
                alt="Post preview"
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="text-center text-gray-400">
                <div className="w-16 h-16 mx-auto mb-3 rounded-2xl bg-gray-200 flex items-center justify-center">
                  <Sparkles className="w-8 h-8 text-gray-300" />
                </div>
                <p className="text-sm font-medium">Générez une photo</p>
                <p className="text-xs mt-1">L&apos;aperçu apparaîtra ici</p>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="p-3 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Heart className="w-6 h-6 text-gray-800 hover:text-red-500 cursor-pointer transition-colors" />
                <MessageCircle className="w-6 h-6 text-gray-800" />
                <Send className="w-6 h-6 text-gray-800" />
              </div>
              <Bookmark className="w-6 h-6 text-gray-800" />
            </div>
            <p className="text-sm font-semibold text-gray-900">1 234 J&apos;aime</p>

            {/* Caption */}
            {caption ? (
              <div className="text-sm text-gray-800">
                <span className="font-semibold mr-1.5">votre_restaurant</span>
                <span className="whitespace-pre-wrap">{caption}</span>
              </div>
            ) : (
              <p className="text-sm text-gray-400 italic">
                La légende sera générée automatiquement...
              </p>
            )}
            <p className="text-xs text-gray-400 uppercase">Il y a quelques secondes</p>
          </div>
        </div>

        {/* Caption editor */}
        {photo && onCaptionChange && (
          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">
              Modifier la légende
            </label>
            <textarea
              value={caption}
              onChange={(e) => onCaptionChange(e.target.value)}
              className="w-full min-h-[100px] p-3 text-sm border border-gray-200 rounded-xl resize-none focus:border-violet-400 focus:ring-1 focus:ring-violet-400/20 focus:outline-none"
              placeholder="Écrivez votre légende..."
            />
          </div>
        )}

        {/* Publish button placeholder */}
        {photo && caption && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
            <Button
              className="w-full gap-2 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white"
              size="lg"
              onClick={() => {
                // Will be wired to publishing flow later
                alert("La publication sera connectée au flow de scheduling.");
              }}
            >
              🚀 Planifier la publication
            </Button>
          </motion.div>
        )}
      </CardContent>
    </Card>
  );
}

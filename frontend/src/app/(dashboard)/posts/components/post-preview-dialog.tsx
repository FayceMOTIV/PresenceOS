"use client";

import { useState } from "react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import {
  Instagram,
  Linkedin,
  Facebook,
  Heart,
  MessageCircle,
  Send,
  Bookmark,
  MoreHorizontal,
  Share2,
  ThumbsUp,
  Repeat2,
  X,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ScheduledPost, SocialConnector, PostStatus } from "@/types";

function TikTokIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z" />
    </svg>
  );
}

const statusConfig: Record<PostStatus, { label: string; color: string }> = {
  scheduled: { label: "Planifie", color: "bg-purple-500" },
  queued: { label: "En file", color: "bg-blue-500" },
  publishing: { label: "Publication", color: "bg-orange-500" },
  published: { label: "Publie", color: "bg-green-500" },
  failed: { label: "Echec", color: "bg-red-500" },
  cancelled: { label: "Annule", color: "bg-gray-500" },
};

interface PostPreviewDialogProps {
  post: ScheduledPost | null;
  connector: SocialConnector | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onEdit?: (post: ScheduledPost) => void;
  onPublishNow?: (post: ScheduledPost) => void;
}

export function PostPreviewDialog({
  post,
  connector,
  open,
  onOpenChange,
  onEdit,
  onPublishNow,
}: PostPreviewDialogProps) {
  const [activeTab, setActiveTab] = useState("preview");

  if (!post || !connector) return null;

  const caption = post.content_snapshot?.caption || "";
  const hashtags = post.content_snapshot?.hashtags || [];
  const mediaUrls = post.content_snapshot?.media_urls || [];
  const platform = connector.platform;
  const status = statusConfig[post.status];
  const canEdit = post.status === "scheduled" || post.status === "queued";
  const canPublish = post.status === "scheduled" || post.status === "failed";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle>Apercu du post</DialogTitle>
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="gap-1">
                <span className={cn("w-2 h-2 rounded-full", status.color)} />
                {status.label}
              </Badge>
            </div>
          </div>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-4">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="preview" className="gap-2">
              {platform === "instagram" && <Instagram className="w-4 h-4" />}
              {platform === "linkedin" && <Linkedin className="w-4 h-4" />}
              {platform === "facebook" && <Facebook className="w-4 h-4" />}
              {platform === "tiktok" && <TikTokIcon className="w-4 h-4" />}
              Apercu
            </TabsTrigger>
            <TabsTrigger value="instagram" className="gap-2">
              <Instagram className="w-4 h-4" />
              Instagram
            </TabsTrigger>
            <TabsTrigger value="linkedin" className="gap-2">
              <Linkedin className="w-4 h-4" />
              LinkedIn
            </TabsTrigger>
            <TabsTrigger value="tiktok" className="gap-2">
              <TikTokIcon className="w-4 h-4" />
              TikTok
            </TabsTrigger>
          </TabsList>

          {/* Original Preview */}
          <TabsContent value="preview" className="mt-4">
            <div className="space-y-4">
              <div className="text-sm text-muted-foreground">
                Publie le {format(new Date(post.scheduled_at), "d MMMM yyyy 'a' HH'h'mm", { locale: fr })}
              </div>

              {/* Media Preview */}
              {mediaUrls.length > 0 && (
                <div className="grid grid-cols-2 gap-2">
                  {mediaUrls.map((url, i) => (
                    <div
                      key={i}
                      className="aspect-square bg-muted rounded-lg overflow-hidden"
                    >
                      <img
                        src={url}
                        alt={`Media ${i + 1}`}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  ))}
                </div>
              )}

              {/* Caption */}
              <div className="space-y-2">
                <p className="text-sm whitespace-pre-wrap">{caption}</p>
                {hashtags.length > 0 && (
                  <p className="text-sm text-primary">
                    {hashtags.map((h) => `#${h}`).join(" ")}
                  </p>
                )}
              </div>
            </div>
          </TabsContent>

          {/* Instagram Preview */}
          <TabsContent value="instagram" className="mt-4">
            <InstagramPreview
              caption={caption}
              hashtags={hashtags}
              mediaUrls={mediaUrls}
              accountName={connector.account_name || "Votre compte"}
            />
          </TabsContent>

          {/* LinkedIn Preview */}
          <TabsContent value="linkedin" className="mt-4">
            <LinkedInPreview
              caption={caption}
              hashtags={hashtags}
              mediaUrls={mediaUrls}
              accountName={connector.account_name || "Votre compte"}
            />
          </TabsContent>

          {/* TikTok Preview */}
          <TabsContent value="tiktok" className="mt-4">
            <TikTokPreview
              caption={caption}
              hashtags={hashtags}
              mediaUrls={mediaUrls}
              accountName={connector.account_name || "Votre compte"}
            />
          </TabsContent>
        </Tabs>

        {/* Actions */}
        <div className="flex justify-end gap-2 mt-6 pt-4 border-t">
          {canEdit && onEdit && (
            <Button variant="outline" onClick={() => onEdit(post)}>
              Modifier
            </Button>
          )}
          {canPublish && onPublishNow && (
            <Button onClick={() => onPublishNow(post)}>
              Publier maintenant
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

// Instagram Preview Component
function InstagramPreview({
  caption,
  hashtags,
  mediaUrls,
  accountName,
}: {
  caption: string;
  hashtags: string[];
  mediaUrls: string[];
  accountName: string;
}) {
  return (
    <div className="max-w-sm mx-auto bg-background border rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-3">
        <div className="flex items-center gap-2">
          <Avatar className="w-8 h-8">
            <AvatarFallback>{accountName[0]?.toUpperCase()}</AvatarFallback>
          </Avatar>
          <span className="text-sm font-medium">{accountName}</span>
        </div>
        <MoreHorizontal className="w-5 h-5 text-muted-foreground" />
      </div>

      {/* Media */}
      <div className="aspect-square bg-muted">
        {mediaUrls.length > 0 ? (
          <img
            src={mediaUrls[0]}
            alt="Post"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-muted-foreground">
            Aucun media
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="p-3 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Heart className="w-6 h-6" />
            <MessageCircle className="w-6 h-6" />
            <Send className="w-6 h-6" />
          </div>
          <Bookmark className="w-6 h-6" />
        </div>
        <div className="text-sm font-medium">0 J&apos;aime</div>
        <div className="text-sm">
          <span className="font-medium">{accountName}</span>{" "}
          {caption.substring(0, 100)}
          {caption.length > 100 && "..."}
        </div>
        {hashtags.length > 0 && (
          <div className="text-sm text-primary">
            {hashtags.slice(0, 5).map((h) => `#${h}`).join(" ")}
          </div>
        )}
      </div>
    </div>
  );
}

// LinkedIn Preview Component
function LinkedInPreview({
  caption,
  hashtags,
  mediaUrls,
  accountName,
}: {
  caption: string;
  hashtags: string[];
  mediaUrls: string[];
  accountName: string;
}) {
  return (
    <div className="max-w-lg mx-auto bg-background border rounded-lg overflow-hidden">
      {/* Header */}
      <div className="p-4">
        <div className="flex items-start gap-3">
          <Avatar className="w-12 h-12">
            <AvatarFallback>{accountName[0]?.toUpperCase()}</AvatarFallback>
          </Avatar>
          <div className="flex-1">
            <div className="font-medium">{accountName}</div>
            <div className="text-xs text-muted-foreground">
              A l&apos;instant
            </div>
          </div>
          <MoreHorizontal className="w-5 h-5 text-muted-foreground" />
        </div>
      </div>

      {/* Content */}
      <div className="px-4 pb-3">
        <p className="text-sm whitespace-pre-wrap">
          {caption.substring(0, 200)}
          {caption.length > 200 && "... voir plus"}
        </p>
        {hashtags.length > 0 && (
          <p className="text-sm text-primary mt-2">
            {hashtags.map((h) => `#${h}`).join(" ")}
          </p>
        )}
      </div>

      {/* Media */}
      {mediaUrls.length > 0 && (
        <div className="aspect-video bg-muted">
          <img
            src={mediaUrls[0]}
            alt="Post"
            className="w-full h-full object-cover"
          />
        </div>
      )}

      {/* Engagement */}
      <div className="p-4 space-y-3">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <ThumbsUp className="w-4 h-4 text-blue-500" />
            0
          </span>
          <span>0 commentaires</span>
        </div>
        <div className="flex items-center justify-around border-t pt-3">
          <Button variant="ghost" size="sm" className="gap-2">
            <ThumbsUp className="w-4 h-4" />
            J&apos;aime
          </Button>
          <Button variant="ghost" size="sm" className="gap-2">
            <MessageCircle className="w-4 h-4" />
            Commenter
          </Button>
          <Button variant="ghost" size="sm" className="gap-2">
            <Repeat2 className="w-4 h-4" />
            Republier
          </Button>
          <Button variant="ghost" size="sm" className="gap-2">
            <Send className="w-4 h-4" />
            Envoyer
          </Button>
        </div>
      </div>
    </div>
  );
}

// TikTok Preview Component
function TikTokPreview({
  caption,
  hashtags,
  mediaUrls,
  accountName,
}: {
  caption: string;
  hashtags: string[];
  mediaUrls: string[];
  accountName: string;
}) {
  return (
    <div className="max-w-xs mx-auto bg-black rounded-2xl overflow-hidden aspect-[9/16] relative">
      {/* Video/Image Background */}
      {mediaUrls.length > 0 ? (
        <img
          src={mediaUrls[0]}
          alt="Post"
          className="w-full h-full object-cover"
        />
      ) : (
        <div className="w-full h-full bg-gradient-to-b from-gray-800 to-gray-900" />
      )}

      {/* Overlay Content */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/70">
        {/* Right Side Actions */}
        <div className="absolute right-3 bottom-32 flex flex-col items-center gap-5">
          <div className="flex flex-col items-center">
            <Avatar className="w-10 h-10 border-2 border-white">
              <AvatarFallback className="bg-gray-600 text-white">
                {accountName[0]?.toUpperCase()}
              </AvatarFallback>
            </Avatar>
          </div>
          <div className="flex flex-col items-center">
            <Heart className="w-7 h-7 text-white" />
            <span className="text-xs text-white mt-1">0</span>
          </div>
          <div className="flex flex-col items-center">
            <MessageCircle className="w-7 h-7 text-white" />
            <span className="text-xs text-white mt-1">0</span>
          </div>
          <div className="flex flex-col items-center">
            <Bookmark className="w-7 h-7 text-white" />
            <span className="text-xs text-white mt-1">0</span>
          </div>
          <div className="flex flex-col items-center">
            <Share2 className="w-7 h-7 text-white" />
            <span className="text-xs text-white mt-1">0</span>
          </div>
        </div>

        {/* Bottom Content */}
        <div className="absolute bottom-4 left-3 right-16">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-white font-semibold text-sm">
              @{accountName.toLowerCase().replace(/\s/g, "")}
            </span>
          </div>
          <p className="text-white text-xs line-clamp-2">
            {caption.substring(0, 100)}
          </p>
          {hashtags.length > 0 && (
            <p className="text-white/80 text-xs mt-1">
              {hashtags.slice(0, 3).map((h) => `#${h}`).join(" ")}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

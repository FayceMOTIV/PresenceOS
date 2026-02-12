"use client";

import { format } from "date-fns";
import { fr } from "date-fns/locale";
import {
  Instagram,
  Linkedin,
  Facebook,
  MoreVertical,
  Eye,
  Pencil,
  Copy,
  Trash2,
  Send,
  ExternalLink,
  Heart,
  MessageCircle,
  Share2,
} from "lucide-react";
import { motion } from "framer-motion";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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

const platformIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  instagram: Instagram,
  tiktok: TikTokIcon,
  linkedin: Linkedin,
  facebook: Facebook,
};

const platformColors: Record<string, string> = {
  instagram: "from-purple-500 to-pink-500",
  tiktok: "bg-black",
  linkedin: "bg-[#0A66C2]",
  facebook: "bg-[#1877F2]",
};

interface PostsMobileCardProps {
  post: ScheduledPost;
  connector: SocialConnector | null;
  onView: (post: ScheduledPost) => void;
  onEdit: (post: ScheduledPost) => void;
  onDuplicate: (post: ScheduledPost) => void;
  onDelete: (post: ScheduledPost) => void;
  onPublishNow: (post: ScheduledPost) => void;
}

export function PostsMobileCard({
  post,
  connector,
  onView,
  onEdit,
  onDuplicate,
  onDelete,
  onPublishNow,
}: PostsMobileCardProps) {
  const caption = post.content_snapshot?.caption || "";
  const truncated = caption.length > 80 ? caption.substring(0, 80) + "..." : caption;
  const hashtags = post.content_snapshot?.hashtags || [];
  const mediaUrls = post.content_snapshot?.media_urls || [];
  const status = statusConfig[post.status];

  const platform = connector?.platform || "instagram";
  const Icon = platformIcons[platform] || Instagram;
  const color = platformColors[platform] || "bg-gray-500";

  const canPublish = post.status === "scheduled" || post.status === "failed";
  const canEdit = post.status === "scheduled" || post.status === "queued";
  const canDelete = post.status !== "publishing";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      layout
    >
      <Card className="overflow-hidden">
        <CardContent className="p-0">
          <div className="flex gap-3 p-4">
            {/* Media Thumbnail */}
            <div
              className="w-20 h-20 flex-shrink-0 rounded-lg bg-muted overflow-hidden cursor-pointer"
              onClick={() => onView(post)}
            >
              {mediaUrls.length > 0 ? (
                <img
                  src={mediaUrls[0]}
                  alt="Post media"
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <Icon className="w-8 h-8 text-muted-foreground" />
                </div>
              )}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              {/* Header */}
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div
                    className={cn(
                      "w-6 h-6 rounded flex items-center justify-center",
                      platform === "instagram" ? "bg-gradient-to-r " + color : color
                    )}
                  >
                    <Icon className="w-3.5 h-3.5 text-white" />
                  </div>
                  <Badge variant="secondary" className="gap-1 text-xs">
                    <span className={cn("w-1.5 h-1.5 rounded-full", status.color)} />
                    {status.label}
                  </Badge>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <MoreVertical className="w-4 h-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onView(post)}>
                      <Eye className="mr-2 h-4 w-4" />
                      Voir
                    </DropdownMenuItem>
                    {canEdit && (
                      <DropdownMenuItem onClick={() => onEdit(post)}>
                        <Pencil className="mr-2 h-4 w-4" />
                        Modifier
                      </DropdownMenuItem>
                    )}
                    <DropdownMenuItem onClick={() => onDuplicate(post)}>
                      <Copy className="mr-2 h-4 w-4" />
                      Dupliquer
                    </DropdownMenuItem>
                    {canPublish && (
                      <DropdownMenuItem onClick={() => onPublishNow(post)}>
                        <Send className="mr-2 h-4 w-4 text-green-500" />
                        Publier maintenant
                      </DropdownMenuItem>
                    )}
                    {post.platform_post_url && (
                      <DropdownMenuItem asChild>
                        <a
                          href={post.platform_post_url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <ExternalLink className="mr-2 h-4 w-4" />
                          Voir sur la plateforme
                        </a>
                      </DropdownMenuItem>
                    )}
                    <DropdownMenuSeparator />
                    {canDelete && (
                      <DropdownMenuItem
                        onClick={() => onDelete(post)}
                        className="text-destructive focus:text-destructive"
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Supprimer
                      </DropdownMenuItem>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              {/* Caption */}
              <p
                className="text-sm mt-2 line-clamp-2 cursor-pointer"
                onClick={() => onView(post)}
              >
                {truncated || "Sans contenu"}
              </p>

              {/* Hashtags */}
              {hashtags.length > 0 && (
                <p className="text-xs text-muted-foreground mt-1 truncate">
                  {hashtags.slice(0, 3).map((h) => `#${h}`).join(" ")}
                </p>
              )}

              {/* Footer */}
              <div className="flex items-center justify-between mt-3">
                <span className="text-xs text-muted-foreground">
                  {format(new Date(post.scheduled_at), "d MMM 'a' HH'h'mm", { locale: fr })}
                </span>

                {/* Engagement (only for published) */}
                {post.status === "published" && (
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Heart className="w-3 h-3" />
                      <span>0</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <MessageCircle className="w-3 h-3" />
                      <span>0</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

interface PostsMobileListProps {
  posts: ScheduledPost[];
  connectors: SocialConnector[];
  onView: (post: ScheduledPost) => void;
  onEdit: (post: ScheduledPost) => void;
  onDuplicate: (post: ScheduledPost) => void;
  onDelete: (post: ScheduledPost) => void;
  onPublishNow: (post: ScheduledPost) => void;
}

export function PostsMobileList({
  posts,
  connectors,
  onView,
  onEdit,
  onDuplicate,
  onDelete,
  onPublishNow,
}: PostsMobileListProps) {
  if (posts.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Aucun post trouve.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {posts.map((post) => {
        const connector = connectors.find((c) => c.id === post.connector_id) || null;
        return (
          <PostsMobileCard
            key={post.id}
            post={post}
            connector={connector}
            onView={onView}
            onEdit={onEdit}
            onDuplicate={onDuplicate}
            onDelete={onDelete}
            onPublishNow={onPublishNow}
          />
        );
      })}
    </div>
  );
}

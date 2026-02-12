"use client";

import { ScheduledPost, PostStatus } from "@/types";
import { cn } from "@/lib/utils";
import { Instagram, Linkedin, Facebook, Clock, Check, AlertCircle, X } from "lucide-react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";

interface CalendarPostCardProps {
  post: ScheduledPost;
  onClick?: () => void;
  isDragging?: boolean;
}

const platformIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  instagram: Instagram,
  linkedin: Linkedin,
  facebook: Facebook,
};

const platformColors: Record<string, string> = {
  instagram: "bg-gradient-to-r from-purple-500 to-pink-500",
  linkedin: "bg-[#0A66C2]",
  facebook: "bg-[#1877F2]",
};

const statusConfig: Record<PostStatus, { icon: React.ComponentType<{ className?: string }>; color: string; label: string }> = {
  scheduled: { icon: Clock, color: "text-yellow-500", label: "Planifie" },
  queued: { icon: Clock, color: "text-blue-500", label: "En attente" },
  publishing: { icon: Clock, color: "text-blue-500", label: "Publication..." },
  published: { icon: Check, color: "text-green-500", label: "Publie" },
  failed: { icon: AlertCircle, color: "text-red-500", label: "Echec" },
  cancelled: { icon: X, color: "text-muted-foreground", label: "Annule" },
};

function TikTokIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z" />
    </svg>
  );
}

export function CalendarPostCard({ post, onClick, isDragging }: CalendarPostCardProps) {
  // Extract platform from connector or content
  const platform = post.content_snapshot?.platform_data?.platform || "instagram";
  const PlatformIcon = platform === "tiktok" ? TikTokIcon : (platformIcons[platform] || Instagram);
  const platformColor = platformColors[platform] || platformColors.instagram;
  const status = statusConfig[post.status];
  const StatusIcon = status.icon;

  const caption = post.content_snapshot?.caption || "";
  const truncatedCaption = caption.length > 40 ? caption.slice(0, 40) + "..." : caption;
  const time = format(new Date(post.scheduled_at), "HH:mm", { locale: fr });

  return (
    <div
      onClick={onClick}
      className={cn(
        "group relative p-2 rounded-lg border bg-card cursor-pointer transition-all",
        "hover:shadow-md hover:border-primary/50",
        isDragging && "opacity-50 shadow-lg ring-2 ring-primary",
        post.status === "cancelled" && "opacity-50"
      )}
    >
      <div className="flex items-start gap-2">
        {/* Platform badge */}
        <div
          className={cn(
            "flex-shrink-0 w-6 h-6 rounded flex items-center justify-center",
            platformColor
          )}
        >
          <PlatformIcon className="w-3.5 h-3.5 text-white" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1 text-xs text-muted-foreground mb-0.5">
            <span>{time}</span>
            <StatusIcon className={cn("w-3 h-3", status.color)} />
          </div>
          <p className="text-xs font-medium truncate">{truncatedCaption}</p>
        </div>
      </div>
    </div>
  );
}

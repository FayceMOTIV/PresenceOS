"use client";

import { ColumnDef } from "@tanstack/react-table";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import {
  ArrowUpDown,
  MoreHorizontal,
  Eye,
  Pencil,
  Copy,
  Trash2,
  Send,
  Instagram,
  Linkedin,
  Facebook,
  ExternalLink,
  Heart,
  MessageCircle,
  Share2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { ScheduledPost, PostStatus, SocialConnector } from "@/types";

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

interface ColumnsProps {
  connectors: SocialConnector[];
  onView: (post: ScheduledPost) => void;
  onEdit: (post: ScheduledPost) => void;
  onDuplicate: (post: ScheduledPost) => void;
  onDelete: (post: ScheduledPost) => void;
  onPublishNow: (post: ScheduledPost) => void;
}

export const createPostsColumns = ({
  connectors,
  onView,
  onEdit,
  onDuplicate,
  onDelete,
  onPublishNow,
}: ColumnsProps): ColumnDef<ScheduledPost>[] => [
  {
    id: "select",
    header: ({ table }) => (
      <Checkbox
        checked={
          table.getIsAllPageRowsSelected() ||
          (table.getIsSomePageRowsSelected() && "indeterminate")
        }
        onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
        aria-label="Selectionner tout"
      />
    ),
    cell: ({ row }) => (
      <Checkbox
        checked={row.getIsSelected()}
        onCheckedChange={(value) => row.toggleSelected(!!value)}
        aria-label="Selectionner la ligne"
      />
    ),
    enableSorting: false,
    enableHiding: false,
  },
  {
    accessorKey: "content_snapshot.caption",
    header: ({ column }) => (
      <Button
        variant="ghost"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        className="-ml-4"
      >
        Contenu
        <ArrowUpDown className="ml-2 h-4 w-4" />
      </Button>
    ),
    cell: ({ row }) => {
      const post = row.original;
      const caption = post.content_snapshot?.caption || "";
      const truncated = caption.length > 60 ? caption.substring(0, 60) + "..." : caption;
      return (
        <div className="max-w-[300px]">
          <p className="font-medium truncate">{truncated || "Sans titre"}</p>
          {post.content_snapshot?.hashtags && post.content_snapshot.hashtags.length > 0 && (
            <p className="text-xs text-muted-foreground truncate">
              {post.content_snapshot.hashtags.slice(0, 3).map((h) => `#${h}`).join(" ")}
              {post.content_snapshot.hashtags.length > 3 && " ..."}
            </p>
          )}
        </div>
      );
    },
  },
  {
    accessorKey: "connector_id",
    header: "Plateforme",
    cell: ({ row }) => {
      const post = row.original;
      const connector = connectors.find((c) => c.id === post.connector_id);
      if (!connector) return <span className="text-muted-foreground">-</span>;

      const Icon = platformIcons[connector.platform] || Instagram;
      const color = platformColors[connector.platform] || "bg-gray-500";

      return (
        <div className="flex items-center gap-2">
          <div
            className={cn(
              "w-7 h-7 rounded-lg flex items-center justify-center",
              connector.platform === "instagram" ? "bg-gradient-to-r " + color : color
            )}
          >
            <Icon className="w-4 h-4 text-white" />
          </div>
          <span className="text-sm capitalize">{connector.platform}</span>
        </div>
      );
    },
  },
  {
    accessorKey: "status",
    header: "Statut",
    cell: ({ row }) => {
      const status = row.getValue("status") as PostStatus;
      const config = statusConfig[status];
      if (!config) return null;
      return (
        <div className="flex items-center gap-2">
          <span className={cn("w-2 h-2 rounded-full", config.color)} />
          <span className="text-sm">{config.label}</span>
        </div>
      );
    },
    filterFn: (row, id, value) => {
      return value.includes(row.getValue(id));
    },
  },
  {
    accessorKey: "scheduled_at",
    header: ({ column }) => (
      <Button
        variant="ghost"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        className="-ml-4"
      >
        Date
        <ArrowUpDown className="ml-2 h-4 w-4" />
      </Button>
    ),
    cell: ({ row }) => {
      const date = row.getValue("scheduled_at") as string;
      return (
        <span className="text-sm">
          {format(new Date(date), "d MMM yyyy 'a' HH'h'mm", { locale: fr })}
        </span>
      );
    },
  },
  {
    id: "engagement",
    header: "Engagement",
    cell: ({ row }) => {
      const post = row.original;
      // Only show engagement for published posts
      if (post.status !== "published") {
        return <span className="text-muted-foreground text-sm">-</span>;
      }

      // Mock engagement data (would come from metrics in real app)
      return (
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          <div className="flex items-center gap-1">
            <Heart className="w-3.5 h-3.5" />
            <span>0</span>
          </div>
          <div className="flex items-center gap-1">
            <MessageCircle className="w-3.5 h-3.5" />
            <span>0</span>
          </div>
          <div className="flex items-center gap-1">
            <Share2 className="w-3.5 h-3.5" />
            <span>0</span>
          </div>
        </div>
      );
    },
  },
  {
    id: "actions",
    cell: ({ row }) => {
      const post = row.original;
      const canPublish = post.status === "scheduled" || post.status === "failed";
      const canEdit = post.status === "scheduled" || post.status === "queued";
      const canDelete = post.status !== "publishing";

      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <span className="sr-only">Menu</span>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Actions</DropdownMenuLabel>
            <DropdownMenuSeparator />
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
                <a href={post.platform_post_url} target="_blank" rel="noopener noreferrer">
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
      );
    },
  },
];

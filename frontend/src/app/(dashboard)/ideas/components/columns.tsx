"use client";

import { ColumnDef } from "@tanstack/react-table";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import {
  ArrowUpDown,
  MoreHorizontal,
  Sparkles,
  TrendingUp,
  User,
  RefreshCw,
  Calendar,
  Check,
  X,
  FileText,
  Instagram,
  Linkedin,
  Facebook,
  Pencil,
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
import { ContentIdea, IdeaSource, IdeaStatus } from "@/types";

function TikTokIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z" />
    </svg>
  );
}

const sourceConfig: Record<
  IdeaSource,
  { label: string; icon: React.ComponentType<{ className?: string }>; color: string }
> = {
  ai_generated: {
    label: "IA",
    icon: Sparkles,
    color: "bg-purple-500/10 text-purple-500",
  },
  trend_inspired: {
    label: "Tendance",
    icon: TrendingUp,
    color: "bg-orange-500/10 text-orange-500",
  },
  user_created: {
    label: "Manuel",
    icon: User,
    color: "bg-blue-500/10 text-blue-500",
  },
  repurposed: {
    label: "Recycle",
    icon: RefreshCw,
    color: "bg-green-500/10 text-green-500",
  },
  calendar_event: {
    label: "Evenement",
    icon: Calendar,
    color: "bg-pink-500/10 text-pink-500",
  },
};

const statusConfig: Record<IdeaStatus, { label: string; color: string }> = {
  new: { label: "Nouveau", color: "bg-blue-500" },
  approved: { label: "Approuve", color: "bg-green-500" },
  in_progress: { label: "En cours", color: "bg-yellow-500" },
  drafted: { label: "Redige", color: "bg-purple-500" },
  rejected: { label: "Rejete", color: "bg-red-500" },
  archived: { label: "Archive", color: "bg-gray-500" },
};

const platformIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  instagram_post: Instagram,
  instagram_story: Instagram,
  instagram_reel: Instagram,
  instagram: Instagram,
  tiktok: TikTokIcon,
  linkedin: Linkedin,
  facebook: Facebook,
};

interface ColumnsProps {
  onApprove: (idea: ContentIdea) => void;
  onReject: (idea: ContentIdea) => void;
  onEdit: (idea: ContentIdea) => void;
  onConvertToDraft: (idea: ContentIdea) => void;
}

export const createColumns = ({
  onApprove,
  onReject,
  onEdit,
  onConvertToDraft,
}: ColumnsProps): ColumnDef<ContentIdea>[] => [
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
    accessorKey: "title",
    header: ({ column }) => (
      <Button
        variant="ghost"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        className="-ml-4"
      >
        Titre
        <ArrowUpDown className="ml-2 h-4 w-4" />
      </Button>
    ),
    cell: ({ row }) => {
      const idea = row.original;
      return (
        <div className="max-w-[300px]">
          <p className="font-medium truncate">{idea.title}</p>
          {idea.description && (
            <p className="text-sm text-muted-foreground truncate">
              {idea.description}
            </p>
          )}
        </div>
      );
    },
  },
  {
    accessorKey: "source",
    header: "Source",
    cell: ({ row }) => {
      const source = row.getValue("source") as IdeaSource;
      const config = sourceConfig[source];
      if (!config) return null;
      const Icon = config.icon;
      return (
        <Badge variant="secondary" className={cn("gap-1", config.color)}>
          <Icon className="w-3 h-3" />
          {config.label}
        </Badge>
      );
    },
  },
  {
    accessorKey: "status",
    header: "Statut",
    cell: ({ row }) => {
      const status = row.getValue("status") as IdeaStatus;
      const config = statusConfig[status];
      if (!config) return null;
      return (
        <div className="flex items-center gap-2">
          <span className={cn("w-2 h-2 rounded-full", config.color)} />
          <span className="text-sm">{config.label}</span>
        </div>
      );
    },
  },
  {
    accessorKey: "target_platforms",
    header: "Plateformes",
    cell: ({ row }) => {
      const platforms = row.getValue("target_platforms") as string[] | undefined;
      if (!platforms || platforms.length === 0) {
        return <span className="text-muted-foreground text-sm">-</span>;
      }
      return (
        <div className="flex items-center gap-1">
          {platforms.slice(0, 3).map((platform) => {
            const Icon = platformIcons[platform] || platformIcons[platform.split("_")[0]];
            if (!Icon) return null;
            return (
              <div
                key={platform}
                className="w-6 h-6 rounded-full bg-muted flex items-center justify-center"
              >
                <Icon className="w-3.5 h-3.5" />
              </div>
            );
          })}
          {platforms.length > 3 && (
            <span className="text-xs text-muted-foreground">
              +{platforms.length - 3}
            </span>
          )}
        </div>
      );
    },
  },
  {
    accessorKey: "content_pillar",
    header: "Pilier",
    cell: ({ row }) => {
      const pillar = row.getValue("content_pillar") as string | undefined;
      if (!pillar) return <span className="text-muted-foreground text-sm">-</span>;
      return <Badge variant="outline">{pillar}</Badge>;
    },
  },
  {
    accessorKey: "created_at",
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
      const date = row.getValue("created_at") as string;
      return (
        <span className="text-sm text-muted-foreground">
          {format(new Date(date), "d MMM yyyy", { locale: fr })}
        </span>
      );
    },
  },
  {
    id: "actions",
    cell: ({ row }) => {
      const idea = row.original;
      const canApprove = idea.status === "new";
      const canReject = idea.status === "new" || idea.status === "approved";
      const canConvert = idea.status === "approved";
      const canEdit = idea.status !== "drafted" && idea.status !== "archived";

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
            {canEdit && (
              <DropdownMenuItem onClick={() => onEdit(idea)}>
                <Pencil className="mr-2 h-4 w-4 text-blue-500" />
                Modifier
              </DropdownMenuItem>
            )}
            {canApprove && (
              <DropdownMenuItem onClick={() => onApprove(idea)}>
                <Check className="mr-2 h-4 w-4 text-green-500" />
                Approuver
              </DropdownMenuItem>
            )}
            {canReject && (
              <DropdownMenuItem onClick={() => onReject(idea)}>
                <X className="mr-2 h-4 w-4 text-red-500" />
                Rejeter
              </DropdownMenuItem>
            )}
            {canConvert && (
              <DropdownMenuItem onClick={() => onConvertToDraft(idea)}>
                <FileText className="mr-2 h-4 w-4 text-purple-500" />
                Creer le contenu
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      );
    },
  },
];

"use client";

import { useState } from "react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import {
  Filter,
  X,
  Check,
  Calendar as CalendarIcon,
  Instagram,
  Linkedin,
  Facebook,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { PostStatus, SocialPlatform } from "@/types";

function TikTokIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z" />
    </svg>
  );
}

export interface PostsFilters {
  platforms: SocialPlatform[];
  statuses: PostStatus[];
  dateFrom: Date | undefined;
  dateTo: Date | undefined;
}

interface PostsFiltersProps {
  filters: PostsFilters;
  onFiltersChange: (filters: PostsFilters) => void;
}

const platformOptions: {
  id: SocialPlatform;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}[] = [
  { id: "instagram", label: "Instagram", icon: Instagram },
  { id: "linkedin", label: "LinkedIn", icon: Linkedin },
  { id: "facebook", label: "Facebook", icon: Facebook },
  { id: "tiktok", label: "TikTok", icon: TikTokIcon },
];

const statusOptions: {
  id: PostStatus;
  label: string;
  color: string;
}[] = [
  { id: "scheduled", label: "Planifie", color: "bg-purple-500" },
  { id: "queued", label: "En file", color: "bg-blue-500" },
  { id: "publishing", label: "Publication", color: "bg-orange-500" },
  { id: "published", label: "Publie", color: "bg-green-500" },
  { id: "failed", label: "Echec", color: "bg-red-500" },
  { id: "cancelled", label: "Annule", color: "bg-gray-500" },
];

export function PostsFiltersComponent({
  filters,
  onFiltersChange,
}: PostsFiltersProps) {
  const [open, setOpen] = useState(false);
  const [datePickerOpen, setDatePickerOpen] = useState(false);

  const activeFiltersCount =
    filters.platforms.length +
    filters.statuses.length +
    (filters.dateFrom ? 1 : 0) +
    (filters.dateTo ? 1 : 0);

  const togglePlatform = (platform: SocialPlatform) => {
    const newPlatforms = filters.platforms.includes(platform)
      ? filters.platforms.filter((p) => p !== platform)
      : [...filters.platforms, platform];
    onFiltersChange({ ...filters, platforms: newPlatforms });
  };

  const toggleStatus = (status: PostStatus) => {
    const newStatuses = filters.statuses.includes(status)
      ? filters.statuses.filter((s) => s !== status)
      : [...filters.statuses, status];
    onFiltersChange({ ...filters, statuses: newStatuses });
  };

  const clearFilters = () => {
    onFiltersChange({
      platforms: [],
      statuses: [],
      dateFrom: undefined,
      dateTo: undefined,
    });
  };

  const clearDateRange = () => {
    onFiltersChange({
      ...filters,
      dateFrom: undefined,
      dateTo: undefined,
    });
  };

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {/* Main filters popover */}
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            className={cn("gap-2", activeFiltersCount > 0 && "border-primary")}
          >
            <Filter className="w-4 h-4" />
            Filtres
            {activeFiltersCount > 0 && (
              <Badge
                variant="secondary"
                className="ml-1 h-5 px-1.5 text-xs bg-primary text-primary-foreground"
              >
                {activeFiltersCount}
              </Badge>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-80 p-4" align="start">
          <div className="space-y-4">
            {/* Platforms */}
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Plateformes</h4>
              <div className="flex flex-wrap gap-2">
                {platformOptions.map((platform) => {
                  const Icon = platform.icon;
                  const isSelected = filters.platforms.includes(platform.id);
                  return (
                    <button
                      key={platform.id}
                      onClick={() => togglePlatform(platform.id)}
                      className={cn(
                        "flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-xs font-medium transition-all",
                        isSelected
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted hover:bg-muted/80"
                      )}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      {platform.label}
                      {isSelected && <Check className="w-3 h-3 ml-0.5" />}
                    </button>
                  );
                })}
              </div>
            </div>

            <Separator />

            {/* Statuses */}
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Statut</h4>
              <div className="flex flex-wrap gap-2">
                {statusOptions.map((status) => {
                  const isSelected = filters.statuses.includes(status.id);
                  return (
                    <button
                      key={status.id}
                      onClick={() => toggleStatus(status.id)}
                      className={cn(
                        "flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-xs font-medium transition-all",
                        isSelected
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted hover:bg-muted/80"
                      )}
                    >
                      <span
                        className={cn("w-2 h-2 rounded-full", status.color)}
                      />
                      {status.label}
                      {isSelected && <Check className="w-3 h-3 ml-0.5" />}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Clear button */}
            {activeFiltersCount > 0 && (
              <>
                <Separator />
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full text-muted-foreground"
                  onClick={clearFilters}
                >
                  <X className="w-4 h-4 mr-2" />
                  Effacer les filtres
                </Button>
              </>
            )}
          </div>
        </PopoverContent>
      </Popover>

      {/* Date range picker */}
      <Popover open={datePickerOpen} onOpenChange={setDatePickerOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            className={cn(
              "gap-2",
              (filters.dateFrom || filters.dateTo) && "border-primary"
            )}
          >
            <CalendarIcon className="w-4 h-4" />
            {filters.dateFrom && filters.dateTo ? (
              <span className="text-xs">
                {format(filters.dateFrom, "d MMM", { locale: fr })} -{" "}
                {format(filters.dateTo, "d MMM", { locale: fr })}
              </span>
            ) : filters.dateFrom ? (
              <span className="text-xs">
                Depuis {format(filters.dateFrom, "d MMM", { locale: fr })}
              </span>
            ) : filters.dateTo ? (
              <span className="text-xs">
                Jusqu&apos;au {format(filters.dateTo, "d MMM", { locale: fr })}
              </span>
            ) : (
              "Periode"
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <div className="p-3 space-y-3">
            <div className="space-y-1">
              <p className="text-sm font-medium">Du</p>
              <Calendar
                mode="single"
                selected={filters.dateFrom}
                onSelect={(date) =>
                  onFiltersChange({ ...filters, dateFrom: date })
                }
                locale={fr}
              />
            </div>
            <Separator />
            <div className="space-y-1">
              <p className="text-sm font-medium">Au</p>
              <Calendar
                mode="single"
                selected={filters.dateTo}
                onSelect={(date) =>
                  onFiltersChange({ ...filters, dateTo: date })
                }
                locale={fr}
              />
            </div>
            {(filters.dateFrom || filters.dateTo) && (
              <>
                <Separator />
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full"
                  onClick={clearDateRange}
                >
                  Effacer les dates
                </Button>
              </>
            )}
          </div>
        </PopoverContent>
      </Popover>

      {/* Active filter badges */}
      <AnimatePresence>
        {filters.platforms.map((platformId) => {
          const platform = platformOptions.find((p) => p.id === platformId);
          if (!platform) return null;
          const Icon = platform.icon;
          return (
            <motion.div
              key={platformId}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
            >
              <Badge
                variant="secondary"
                className="gap-1 cursor-pointer hover:bg-destructive/10"
                onClick={() => togglePlatform(platformId)}
              >
                <Icon className="w-3 h-3" />
                {platform.label}
                <X className="w-3 h-3 ml-0.5" />
              </Badge>
            </motion.div>
          );
        })}
        {filters.statuses.map((statusId) => {
          const status = statusOptions.find((s) => s.id === statusId);
          if (!status) return null;
          return (
            <motion.div
              key={statusId}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
            >
              <Badge
                variant="secondary"
                className="gap-1 cursor-pointer hover:bg-destructive/10"
                onClick={() => toggleStatus(statusId)}
              >
                <span className={cn("w-2 h-2 rounded-full", status.color)} />
                {status.label}
                <X className="w-3 h-3 ml-0.5" />
              </Badge>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}

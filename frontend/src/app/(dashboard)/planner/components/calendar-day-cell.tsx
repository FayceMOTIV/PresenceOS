"use client";

import { ScheduledPost } from "@/types";
import { CalendarPostCard } from "./calendar-post-card";
import { cn } from "@/lib/utils";
import { format, isToday, isSameMonth } from "date-fns";
import { Plus } from "lucide-react";
import { motion } from "framer-motion";

interface CalendarDayCellProps {
  date: Date;
  currentMonth: Date;
  posts: ScheduledPost[];
  onDayClick?: (date: Date) => void;
  onPostClick?: (post: ScheduledPost) => void;
}

export function CalendarDayCell({
  date,
  currentMonth,
  posts,
  onDayClick,
  onPostClick,
}: CalendarDayCellProps) {
  const isCurrentMonth = isSameMonth(date, currentMonth);
  const isCurrentDay = isToday(date);
  const dayNumber = format(date, "d");

  return (
    <div
      className={cn(
        "min-h-[120px] p-2 border-b border-r bg-card/50 transition-colors",
        !isCurrentMonth && "bg-muted/30 opacity-50",
        isCurrentDay && "bg-primary/5 ring-1 ring-primary/20"
      )}
    >
      {/* Day header */}
      <div className="flex items-center justify-between mb-2">
        <span
          className={cn(
            "inline-flex items-center justify-center w-7 h-7 text-sm font-medium rounded-full",
            isCurrentDay && "bg-primary text-primary-foreground"
          )}
        >
          {dayNumber}
        </span>
        {isCurrentMonth && (
          <button
            onClick={() => onDayClick?.(date)}
            className="opacity-0 group-hover:opacity-100 hover:bg-muted p-1 rounded transition-opacity"
          >
            <Plus className="w-4 h-4 text-muted-foreground" />
          </button>
        )}
      </div>

      {/* Posts */}
      <div className="space-y-1.5">
        {posts.slice(0, 3).map((post, index) => (
          <motion.div
            key={post.id}
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <CalendarPostCard post={post} onClick={() => onPostClick?.(post)} />
          </motion.div>
        ))}
        {posts.length > 3 && (
          <button
            onClick={() => onDayClick?.(date)}
            className="w-full text-xs text-center py-1 text-muted-foreground hover:text-foreground transition-colors"
          >
            +{posts.length - 3} autres
          </button>
        )}
      </div>

      {/* Empty state - click to add */}
      {posts.length === 0 && isCurrentMonth && (
        <button
          onClick={() => onDayClick?.(date)}
          className="w-full h-full min-h-[60px] flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <span className="text-xs text-muted-foreground">+ Ajouter</span>
        </button>
      )}
    </div>
  );
}

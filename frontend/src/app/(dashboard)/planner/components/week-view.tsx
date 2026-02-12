"use client";

import { useMemo } from "react";
import { ScheduledPost, CalendarDay } from "@/types";
import { CalendarPostCard } from "./calendar-post-card";
import {
  startOfWeek,
  endOfWeek,
  eachDayOfInterval,
  format,
  isToday,
  isSameDay,
} from "date-fns";
import { fr } from "date-fns/locale";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Plus } from "lucide-react";

interface WeekViewProps {
  currentDate: Date;
  calendarDays: CalendarDay[];
  onDayClick?: (date: Date) => void;
  onPostClick?: (post: ScheduledPost) => void;
}

export function WeekView({
  currentDate,
  calendarDays,
  onDayClick,
  onPostClick,
}: WeekViewProps) {
  // Get the week's days
  const weekDays = useMemo(() => {
    const weekStart = startOfWeek(currentDate, { weekStartsOn: 1 });
    const weekEnd = endOfWeek(currentDate, { weekStartsOn: 1 });
    return eachDayOfInterval({ start: weekStart, end: weekEnd });
  }, [currentDate]);

  // Create a map of posts by date for quick lookup
  const postsByDate = useMemo(() => {
    const map = new Map<string, ScheduledPost[]>();
    calendarDays.forEach((day) => {
      const dateKey = format(new Date(day.date), "yyyy-MM-dd");
      map.set(dateKey, day.scheduled_posts);
    });
    return map;
  }, [calendarDays]);

  const getPostsForDate = (date: Date): ScheduledPost[] => {
    const dateKey = format(date, "yyyy-MM-dd");
    return postsByDate.get(dateKey) || [];
  };

  return (
    <motion.div
      key={format(currentDate, "yyyy-ww")}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.2 }}
      className="space-y-4"
    >
      {weekDays.map((day, index) => {
        const posts = getPostsForDate(day);
        const isCurrentDay = isToday(day);

        return (
          <motion.div
            key={day.toISOString()}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.03 }}
            className={cn(
              "rounded-lg border bg-card overflow-hidden",
              isCurrentDay && "ring-2 ring-primary/20"
            )}
          >
            {/* Day header */}
            <div
              className={cn(
                "flex items-center justify-between px-4 py-3 border-b",
                isCurrentDay && "bg-primary/5"
              )}
            >
              <div className="flex items-center gap-3">
                <span
                  className={cn(
                    "inline-flex items-center justify-center w-10 h-10 rounded-full text-lg font-semibold",
                    isCurrentDay
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted"
                  )}
                >
                  {format(day, "d")}
                </span>
                <div>
                  <p className="font-medium capitalize">
                    {format(day, "EEEE", { locale: fr })}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {format(day, "d MMMM yyyy", { locale: fr })}
                  </p>
                </div>
              </div>
              <button
                onClick={() => onDayClick?.(day)}
                className="flex items-center gap-1 px-3 py-1.5 rounded-md text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              >
                <Plus className="w-4 h-4" />
                Ajouter
              </button>
            </div>

            {/* Posts */}
            <div className="p-4">
              {posts.length > 0 ? (
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {posts.map((post, postIndex) => (
                    <motion.div
                      key={post.id}
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: postIndex * 0.05 }}
                    >
                      <CalendarPostCard
                        post={post}
                        onClick={() => onPostClick?.(post)}
                      />
                    </motion.div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <p className="text-sm">Aucun post prevu</p>
                  <button
                    onClick={() => onDayClick?.(day)}
                    className="text-sm text-primary hover:underline mt-1"
                  >
                    Ajouter un post
                  </button>
                </div>
              )}
            </div>
          </motion.div>
        );
      })}
    </motion.div>
  );
}

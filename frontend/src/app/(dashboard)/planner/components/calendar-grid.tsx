"use client";

import { useMemo, useState } from "react";
import {
  DndContext,
  DragOverlay,
  DragStartEvent,
  DragEndEvent,
  pointerWithin,
  useSensor,
  useSensors,
  PointerSensor,
} from "@dnd-kit/core";
import { ScheduledPost, CalendarDay } from "@/types";
import { DroppableDay } from "./droppable-day";
import { CalendarPostCard } from "./calendar-post-card";
import {
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  eachDayOfInterval,
  format,
} from "date-fns";
import { motion } from "framer-motion";

interface CalendarGridProps {
  currentDate: Date;
  calendarDays: CalendarDay[];
  onDayClick?: (date: Date) => void;
  onPostClick?: (post: ScheduledPost) => void;
  onPostMove?: (postId: string, newDate: Date, post: ScheduledPost) => Promise<boolean>;
}

const weekDays = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"];

export function CalendarGrid({
  currentDate,
  calendarDays,
  onDayClick,
  onPostClick,
  onPostMove,
}: CalendarGridProps) {
  const [activePost, setActivePost] = useState<ScheduledPost | null>(null);

  // Configure sensors for better drag experience
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // Minimum drag distance before activation
      },
    })
  );

  // Generate all days to display in the calendar grid
  const days = useMemo(() => {
    const monthStart = startOfMonth(currentDate);
    const monthEnd = endOfMonth(currentDate);
    const calendarStart = startOfWeek(monthStart, { weekStartsOn: 1 });
    const calendarEnd = endOfWeek(monthEnd, { weekStartsOn: 1 });

    return eachDayOfInterval({ start: calendarStart, end: calendarEnd });
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

  // Handle drag start
  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event;
    const post = active.data.current?.post as ScheduledPost | undefined;
    if (post) {
      setActivePost(post);
    }
  };

  // Handle drag end
  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActivePost(null);

    if (!over) return;

    const post = active.data.current?.post as ScheduledPost | undefined;
    const targetDate = over.data.current?.date as Date | undefined;

    if (!post || !targetDate) return;

    // Check if the post is moving to a different day
    const originalDate = format(new Date(post.scheduled_at), "yyyy-MM-dd");
    const newDateStr = format(targetDate, "yyyy-MM-dd");

    if (originalDate === newDateStr) return; // Same day, no move needed

    // Call the move handler (with optimistic update + rollback)
    if (onPostMove) {
      await onPostMove(post.id, targetDate, post);
    }
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={pointerWithin}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <motion.div
        key={format(currentDate, "yyyy-MM")}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
        transition={{ duration: 0.2 }}
        className="border rounded-lg overflow-hidden bg-card"
      >
        {/* Week day headers */}
        <div className="grid grid-cols-7 border-b bg-muted/50">
          {weekDays.map((day) => (
            <div
              key={day}
              className="p-3 text-center text-sm font-medium text-muted-foreground"
            >
              {day}
            </div>
          ))}
        </div>

        {/* Calendar grid */}
        <div className="grid grid-cols-7">
          {days.map((day) => (
            <div key={day.toISOString()} className="group">
              <DroppableDay
                date={day}
                currentMonth={currentDate}
                posts={getPostsForDate(day)}
                onDayClick={onDayClick}
                onPostClick={onPostClick}
              />
            </div>
          ))}
        </div>
      </motion.div>

      {/* Drag overlay - shows the post being dragged */}
      <DragOverlay dropAnimation={null}>
        {activePost ? (
          <div className="opacity-90 shadow-xl rotate-2 scale-105">
            <CalendarPostCard post={activePost} isDragging />
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}

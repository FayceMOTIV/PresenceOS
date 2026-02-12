"use client";

import { useDraggable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { ScheduledPost } from "@/types";
import { CalendarPostCard } from "./calendar-post-card";
import { GripVertical } from "lucide-react";
import { cn } from "@/lib/utils";

interface DraggablePostProps {
  post: ScheduledPost;
  onClick?: () => void;
  disabled?: boolean;
}

export function DraggablePost({ post, onClick, disabled }: DraggablePostProps) {
  const canDrag = post.status === "scheduled" || post.status === "queued";

  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: post.id,
    data: {
      post,
      type: "post",
    },
    disabled: disabled || !canDrag,
  });

  const style = transform
    ? {
        transform: CSS.Translate.toString(transform),
        zIndex: isDragging ? 50 : undefined,
      }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        "relative group",
        isDragging && "opacity-50"
      )}
    >
      {/* Drag handle - only visible on hover for draggable posts */}
      {canDrag && (
        <div
          {...listeners}
          {...attributes}
          className={cn(
            "absolute -left-1 top-1/2 -translate-y-1/2 p-0.5 rounded cursor-grab",
            "opacity-0 group-hover:opacity-100 transition-opacity",
            "hover:bg-muted active:cursor-grabbing",
            isDragging && "opacity-100 cursor-grabbing"
          )}
        >
          <GripVertical className="w-3 h-3 text-muted-foreground" />
        </div>
      )}

      <CalendarPostCard
        post={post}
        onClick={onClick}
        isDragging={isDragging}
      />
    </div>
  );
}

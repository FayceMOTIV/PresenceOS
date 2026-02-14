"use client";

import { ReactNode } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";

interface EmptyStateProps {
  emoji: string;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
    icon?: ReactNode;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
    icon?: ReactNode;
  };
}

export function EmptyState({
  emoji,
  title,
  description,
  action,
  secondaryAction,
}: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-16 px-4"
    >
      <span className="text-7xl mb-6" role="img" aria-hidden>
        {emoji}
      </span>

      <h3 className="text-xl font-bold text-gray-900 mb-2 text-center">
        {title}
      </h3>

      <p className="text-base text-gray-500 mb-8 text-center max-w-md leading-relaxed">
        {description}
      </p>

      <div className="flex items-center gap-3">
        {secondaryAction && (
          <Button variant="outline" size="lg" onClick={secondaryAction.onClick}>
            {secondaryAction.icon}
            {secondaryAction.label}
          </Button>
        )}
        {action && (
          <Button variant="gradient" size="lg" onClick={action.onClick}>
            {action.icon}
            {action.label}
          </Button>
        )}
      </div>
    </motion.div>
  );
}

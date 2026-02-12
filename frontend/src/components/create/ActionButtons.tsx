"use client";

import { motion } from "framer-motion";
import { Rocket, Pencil, X } from "lucide-react";

interface ActionButtonsProps {
  buttons: { id: string; title: string }[];
  onClickButton: (id: string, title: string) => void;
  disabled?: boolean;
}

const buttonStyles: Record<string, { icon: any; variant: string }> = {
  enrich_publish: { icon: Rocket, variant: "primary" },
  confirm_publish: { icon: Rocket, variant: "primary" },
  enrich_add: { icon: Pencil, variant: "outline" },
  confirm_edit: { icon: Pencil, variant: "outline" },
  confirm_cancel: { icon: X, variant: "ghost" },
};

export function ActionButtons({ buttons, onClickButton, disabled }: ActionButtonsProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-wrap gap-2 mt-2"
    >
      {buttons.map((btn, i) => {
        const style = buttonStyles[btn.id] || { icon: null, variant: "outline" };
        const Icon = style.icon;
        const isPrimary = style.variant === "primary";
        const isGhost = style.variant === "ghost";

        return (
          <motion.button
            key={btn.id}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.08, type: "spring", stiffness: 300 }}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            disabled={disabled}
            onClick={() => onClickButton(btn.id, btn.title)}
            className={`
              inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium
              transition-all duration-200 disabled:opacity-50
              ${
                isPrimary
                  ? "bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg shadow-amber-500/20 hover:shadow-amber-500/40"
                  : isGhost
                  ? "text-muted-foreground hover:text-foreground hover:bg-secondary"
                  : "border border-border bg-secondary/50 text-foreground hover:bg-secondary hover:border-primary/30"
              }
            `}
          >
            {Icon && <Icon className="w-4 h-4" />}
            {btn.title}
          </motion.button>
        );
      })}
    </motion.div>
  );
}

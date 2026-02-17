"use client";

import { motion } from "framer-motion";
import { ReactNode, CSSProperties } from "react";
import { gradients, glass, shadows } from "@/lib/design-system/colors";

interface GradientCardProps {
  children: ReactNode;
  gradient?: keyof typeof gradients;
  hover?: boolean;
  glow?: boolean;
  className?: string;
}

export default function GradientCard({
  children,
  gradient = "cardPurple",
  hover = true,
  glow = false,
  className = "",
}: GradientCardProps) {
  const cardStyle: CSSProperties = {
    background: gradients[gradient],
    backdropFilter: glass.backdrop,
    boxShadow: glow ? shadows.glow : shadows.md,
    border: `1px solid ${glass.border}`,
  };

  return (
    <motion.div
      whileHover={hover ? { scale: 1.01, y: -2 } : {}}
      transition={{ duration: 0.2 }}
      className={`relative overflow-hidden rounded-2xl ${className}`}
      style={cardStyle}
    >
      <div className="relative z-10 p-6">{children}</div>

      {glow && (
        <motion.div
          className="absolute inset-0 pointer-events-none"
          animate={{ opacity: [0, 0.15, 0] }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          style={{
            background:
              "radial-gradient(circle at 50% 50%, rgba(139, 92, 246, 0.2), transparent 70%)",
          }}
        />
      )}
    </motion.div>
  );
}

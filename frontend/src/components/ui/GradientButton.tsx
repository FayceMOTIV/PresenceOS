"use client";

import { motion } from "framer-motion";
import { ReactNode, CSSProperties } from "react";
import { gradients } from "@/lib/design-system/colors";

interface GradientButtonProps {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "success";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  loading?: boolean;
  className?: string;
  type?: "button" | "submit";
}

export default function GradientButton({
  children,
  onClick,
  variant = "primary",
  size = "md",
  disabled = false,
  loading = false,
  className = "",
  type = "button",
}: GradientButtonProps) {
  const gradientMap = {
    primary: gradients.primaryButton,
    secondary: gradients.secondaryButton,
    success: gradients.successButton,
  };

  const sizeMap = {
    sm: "px-4 py-2 text-sm",
    md: "px-6 py-3 text-base",
    lg: "px-8 py-4 text-lg",
  };

  const buttonStyle: CSSProperties = {
    background: gradientMap[variant],
  };

  return (
    <motion.button
      type={type}
      whileHover={disabled ? {} : { scale: 1.03 }}
      whileTap={disabled ? {} : { scale: 0.97 }}
      onClick={onClick}
      disabled={disabled || loading}
      className={`
        relative overflow-hidden rounded-xl font-semibold text-white
        shadow-lg transition-shadow duration-200 hover:shadow-xl
        disabled:opacity-50 disabled:cursor-not-allowed
        ${sizeMap[size]}
        ${className}
      `}
      style={buttonStyle}
    >
      {/* Shine effect */}
      <motion.div
        className="absolute inset-0 pointer-events-none"
        animate={{
          opacity: [0, 0.2, 0],
          x: ["-100%", "100%"],
        }}
        transition={{
          duration: 2.5,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        style={{
          background:
            "linear-gradient(90deg, transparent, rgba(255,255,255,0.25), transparent)",
        }}
      />

      <span className="relative z-10 flex items-center justify-center gap-2">
        {loading && (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
          />
        )}
        {children}
      </span>
    </motion.button>
  );
}

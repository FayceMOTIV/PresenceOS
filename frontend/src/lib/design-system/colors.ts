// Design System - Colors & Gradients (Light Theme)
export const colors = {
  primary: {
    50: "#f5f3ff",
    100: "#ede9fe",
    200: "#ddd6fe",
    500: "#8b5cf6",
    600: "#7c3aed",
    700: "#6d28d9",
  },
  accent: {
    pink: "#ec4899",
    orange: "#f97316",
    cyan: "#06b6d4",
    emerald: "#10b981",
  },
};

export const gradients = {
  // Hero / Header
  aurora: "linear-gradient(135deg, #8b5cf6 0%, #ec4899 50%, #f97316 100%)",
  sunset: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",

  // Card backgrounds (subtle, light-friendly)
  cardPurple:
    "linear-gradient(135deg, rgba(139, 92, 246, 0.08) 0%, rgba(236, 72, 153, 0.08) 100%)",
  cardBlue:
    "linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(6, 182, 212, 0.08) 100%)",
  cardOrange:
    "linear-gradient(135deg, rgba(249, 115, 22, 0.08) 0%, rgba(236, 72, 153, 0.08) 100%)",
  cardEmerald:
    "linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(20, 184, 166, 0.08) 100%)",

  // Buttons
  primaryButton: "linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)",
  secondaryButton: "linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%)",
  successButton: "linear-gradient(135deg, #10b981 0%, #14b8a6 100%)",
};

export const glass = {
  light: "rgba(255, 255, 255, 0.6)",
  backdrop: "blur(16px)",
  border: "rgba(139, 92, 246, 0.12)",
};

export const shadows = {
  sm: "0 1px 2px rgba(0, 0, 0, 0.05)",
  md: "0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.05)",
  lg: "0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.05)",
  glow: "0 0 20px rgba(139, 92, 246, 0.15)",
  glowPink: "0 0 20px rgba(236, 72, 153, 0.15)",
};

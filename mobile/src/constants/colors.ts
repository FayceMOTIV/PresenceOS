// PresenceOS Mobile — Design System Colors
// Premium LIGHT theme with violet/amber accents — Inspired by Notion, Linear, Arc

export const Colors = {
  // ── Backgrounds ──
  bg: {
    primary: "#F8F7FF",      // Fond principal — blanc légèrement violet
    secondary: "#FFFFFF",    // Cards — blanc pur
    elevated: "#F0EEFF",     // Surfaces élevées — lavande très clair
    overlay: "#EDE9FF",      // Modals
  },

  // ── Brand ──
  brand: {
    primary: "#7C5CBF",      // Violet principal
    light: "#9D7FDB",
    dark: "#5B3E9E",
    amber: "#F4A261",
    amberLight: "#F9C784",
    glow: "rgba(124,92,191,0.15)",
  },

  // ── Text ──
  text: {
    primary: "#1A1033",      // Quasi noir
    secondary: "#5A5272",    // Gris violet
    muted: "#9B97AE",
    accent: "#7C5CBF",
    inverted: "#FFFFFF",
  },

  // ── Borders ──
  border: {
    default: "rgba(124,92,191,0.12)",
    strong: "rgba(124,92,191,0.2)",
    active: "rgba(124,92,191,0.5)",
  },

  // ── Status ──
  status: {
    success: "#10B981",
    successLight: "rgba(16,184,129,0.12)",
    warning: "#F59E0B",
    warningLight: "rgba(245,158,11,0.12)",
    danger: "#EF4444",
    dangerLight: "rgba(239,68,68,0.12)",
    info: "#3B82F6",
    infoLight: "rgba(59,130,246,0.12)",
  },

  // ── Gradients (as arrays for LinearGradient) ──
  gradient: {
    hero: ["#7C5CBF", "#F4A261"] as const,         // Violet → amber
    violet: ["#7C5CBF", "#5B3E9E"] as const,       // Pure violet
    amber: ["#F4A261", "#E08A3E"] as const,         // Amber
    light: ["#F8F7FF", "#F0EEFF"] as const,         // Subtle bg
    success: ["#10B981", "#059669"] as const,
    danger: ["#EF4444", "#DC2626"] as const,
  },
};

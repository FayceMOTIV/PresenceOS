import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + "M";
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + "K";
  }
  return num.toString();
}

export function formatRelativeTime(date: Date | string): string {
  const now = new Date();
  const target = new Date(date);
  const diffMs = target.getTime() - now.getTime();
  const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "Aujourd'hui";
  if (diffDays === 1) return "Demain";
  if (diffDays === -1) return "Hier";
  if (diffDays > 0 && diffDays <= 7) return `Dans ${diffDays} jours`;
  if (diffDays < 0 && diffDays >= -7) return `Il y a ${Math.abs(diffDays)} jours`;

  return target.toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "short",
  });
}

export function getPlatformColor(platform: string): string {
  const colors: Record<string, string> = {
    instagram: "bg-gradient-to-r from-purple-500 to-pink-500",
    tiktok: "bg-black",
    linkedin: "bg-blue-600",
    facebook: "bg-blue-500",
  };
  return colors[platform.toLowerCase()] || "bg-gray-500";
}

export function getPlatformIcon(platform: string): string {
  const icons: Record<string, string> = {
    instagram: "📸",
    tiktok: "🎵",
    linkedin: "💼",
    facebook: "👥",
  };
  return icons[platform.toLowerCase()] || "📱";
}

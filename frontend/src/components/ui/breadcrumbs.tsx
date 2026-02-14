"use client";

import Link from "next/link";
import { ChevronRight, Home } from "lucide-react";
import { usePathname } from "next/navigation";

const PAGE_NAMES: Record<string, string> = {
  dashboard: "Accueil",
  studio: "Créer un post",
  ideas: "Idées de posts",
  brain: "Analyser Instagram",
  agents: "Mes assistants",
  planner: "Calendrier",
  posts: "Mes posts",
  settings: "Réglages",
  trends: "Tendances",
  autopilot: "Pilote automatique",
  analytics: "Statistiques",
  create: "Nouveau post",
  "media-library": "Mes photos",
  "brands": "Marques",
};

export function Breadcrumbs() {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  // Don't show on dashboard (home)
  if (segments.length === 0 || (segments.length === 1 && segments[0] === "dashboard")) {
    return null;
  }

  return (
    <nav
      aria-label="Fil d'Ariane"
      className="flex items-center gap-1.5 text-sm mb-6"
    >
      <Link
        href="/dashboard"
        className="text-gray-400 hover:text-gray-600 transition-colors flex items-center gap-1"
      >
        <Home className="w-3.5 h-3.5" />
        <span className="hidden sm:inline">Accueil</span>
      </Link>

      {segments.map((segment, index) => {
        const href = `/${segments.slice(0, index + 1).join("/")}`;
        const isLast = index === segments.length - 1;
        const label = PAGE_NAMES[segment] || segment;

        return (
          <span key={segment} className="flex items-center gap-1.5">
            <ChevronRight className="w-3.5 h-3.5 text-gray-300" />
            {isLast ? (
              <span className="text-gray-700 font-medium">{label}</span>
            ) : (
              <Link
                href={href}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                {label}
              </Link>
            )}
          </span>
        );
      })}
    </nav>
  );
}

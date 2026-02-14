/**
 * Vocabulaire simple — traductions grand public
 * Remplace le jargon technique par du français de tous les jours.
 */

export const SIMPLE_TERMS: Record<string, string> = {
  // Concepts
  workspace: "Mon espace",
  brand: "Ma marque",
  "brand voice": "Comment je parle",
  "ai agents": "Mes assistants",
  "content analysis": "Analyser mes posts",
  autopilot: "Pilote automatique",

  // Actions
  generate: "Créer pour moi",
  analyze: "Analyser",
  schedule: "Programmer pour plus tard",
  publish: "Publier maintenant",
  draft: "Brouillon",

  // États
  connected: "Connecté",
  disconnected: "Non connecté",
  active: "Actif",
  inactive: "Inactif",
  pending: "En attente",
  failed: "Échec",

  // UI
  dashboard: "Accueil",
  settings: "Réglages",
  account: "Mon compte",
  logout: "Se déconnecter",
};

export const SIMPLE_DESCRIPTIONS: Record<string, string> = {
  workspace:
    "C'est votre espace pour gérer votre activité. Vous pouvez en avoir plusieurs !",
  brand:
    "C'est comment votre établissement parle à vos clients (ton, style, personnalité).",
  "ai agents":
    "Des assistants automatiques qui créent vos posts pendant que vous travaillez !",
  autopilot:
    "Le robot fait tout automatiquement : photos → texte → publication. Vous n'avez rien à faire !",
  "content analysis":
    "L'ordinateur regarde vos anciens posts Instagram pour apprendre votre style.",
  schedule:
    "Choisir quand publier (aujourd'hui à 18h, demain matin, etc.)",
  "brand voice":
    "C'est le style et le ton que vous utilisez pour parler à vos clients (amical, chic, fun...).",
  studio:
    "L'endroit où vous créez vos posts avec l'aide de l'intelligence artificielle.",
  ideas:
    "L'IA vous propose des idées de posts. Vous choisissez celles qui vous plaisent !",
  planner:
    "Votre calendrier de publications. Programmez à l'avance pour ne plus y penser.",
  brain:
    "L'IA analyse votre Instagram pour apprendre votre style d'écriture et vos habitudes.",
  trends:
    "Découvrez ce qui marche en ce moment dans votre domaine pour créer du contenu populaire.",
};

export const SIMPLE_EXAMPLES: Record<string, string> = {
  workspace: "Ex: Restaurant La Bonne Table, Pizzeria Mario, Café des Artistes",
  brand: "Ex: Amical et chaleureux, Chic et raffiné, Fun et jeune",
  caption:
    "Ex: Nos pâtes fraîches du jour ! 🍝 Venez goûter cette merveille ❤️",
};

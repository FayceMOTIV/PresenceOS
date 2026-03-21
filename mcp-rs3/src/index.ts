#!/usr/bin/env node
/**
 * MCP Server RS3 — Pour Morpheus
 *
 * 15 tools pour piloter PresenceOS RS3 entièrement depuis Morpheus.
 *
 * Config Morpheus (claude_desktop_config.json) :
 * {
 *   "mcpServers": {
 *     "rs3": {
 *       "command": "node",
 *       "args": ["/chemin/absolu/mcp-rs3/dist/index.js"],
 *       "env": {
 *         "RS3_API_KEY": "TON_FIREBASE_TOKEN",
 *         "RS3_API_URL": "https://rs3-api-production.up.railway.app"
 *       }
 *     }
 *   }
 * }
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { rs3 } from "./client.js";

const server = new McpServer({
  name: "rs3",
  version: "1.0.0",
});

// ─── Helper réponse ──────────────────────────────────────────────────────────

function ok(data: unknown) {
  return {
    content: [{ type: "text" as const, text: JSON.stringify(data, null, 2) }],
  };
}

function fail(error: unknown) {
  const msg = error instanceof Error ? error.message : String(error);
  return {
    content: [{ type: "text" as const, text: `❌ Erreur RS3: ${msg}` }],
    isError: true as const,
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// TOOL 1 — SANTÉ
// ═══════════════════════════════════════════════════════════════════════════

server.tool(
  "rs3_health",
  "Vérifie l'état de santé de tous les services RS3 (API Railway, workers).",
  {},
  async () => {
    try {
      const [api, social] = await Promise.allSettled([
        rs3.get("/health"),
        rs3.get("/api/v2/publish/health"),
      ]);
      return ok({
        api:
          api.status === "fulfilled"
            ? "✅ OK"
            : `❌ ${(api as PromiseRejectedResult).reason}`,
        social:
          social.status === "fulfilled"
            ? "✅ OK"
            : `❌ ${(social as PromiseRejectedResult).reason}`,
        timestamp: new Date().toISOString(),
      });
    } catch (e) {
      return fail(e);
    }
  }
);

// ═══════════════════════════════════════════════════════════════════════════
// TOOLS 2-3 — BRANDS
// ═══════════════════════════════════════════════════════════════════════════

server.tool(
  "rs3_list_brands",
  "Liste tous les brands (restaurants/clients) de l'utilisateur avec leur niche et statut.",
  {},
  async () => {
    try {
      return ok(await rs3.get("/api/v2/me/brands"));
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "rs3_list_niches",
  "Liste les 16 niches disponibles (restaurant, médecin, coiffeur, avocat...).",
  {},
  async () => {
    try {
      return ok(await rs3.get("/api/v2/brands/niches/list"));
    } catch (e) {
      return fail(e);
    }
  }
);

// ═══════════════════════════════════════════════════════════════════════════
// TOOL 4 — NICHE
// ═══════════════════════════════════════════════════════════════════════════

server.tool(
  "rs3_set_niche",
  `Définit la niche d'un brand → Ilyas s'adapte instantanément.
Niches disponibles : restaurant, boulangerie, medecin, dentiste, pharmacie,
coiffeur, estheticienne, coach_sportif, coach_vie, avocat, comptable,
agent_immobilier, ecommerce, formateur, artisan, saas.
Exemple : "Configure Dr Dupont comme médecin"`,
  {
    brand_id: z.string().describe("UUID du brand"),
    business_type: z
      .string()
      .describe("Type de business (ex: medecin, coiffeur, restaurant)"),
  },
  async ({ brand_id, business_type }) => {
    try {
      return ok(
        await rs3.post(
          `/api/v2/brands/${brand_id}/niche?business_type=${encodeURIComponent(business_type)}`
        )
      );
    } catch (e) {
      return fail(e);
    }
  }
);

// ═══════════════════════════════════════════════════════════════════════════
// TOOLS 5-7 — SOCIAL / PUBLICATION
// ═══════════════════════════════════════════════════════════════════════════

server.tool(
  "rs3_list_social_accounts",
  "Liste les comptes sociaux connectés pour un brand (Instagram, Facebook, TikTok, LinkedIn).",
  {
    brand_id: z.string().describe("UUID du brand"),
  },
  async ({ brand_id }) => {
    try {
      return ok(
        await rs3.get(`/api/v2/publish/brands/${brand_id}/integrations`)
      );
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "rs3_publish_post",
  "Publie un post immédiatement sur un ou plusieurs réseaux sociaux d'un brand.",
  {
    brand_id: z.string().describe("UUID du brand"),
    integration_ids: z
      .array(z.string())
      .describe(
        "IDs des comptes cibles (récupérés via rs3_list_social_accounts)"
      ),
    content: z.string().describe("Texte du post (max 2200 chars)"),
    media_urls: z
      .array(z.string())
      .optional()
      .describe("URLs médias optionnelles (images/vidéos S3)"),
  },
  async ({ brand_id, integration_ids, content, media_urls }) => {
    try {
      return ok(
        await rs3.post(`/api/v2/publish/brands/${brand_id}/publish`, {
          integration_ids,
          content,
          media_urls: media_urls ?? [],
        })
      );
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "rs3_schedule_post",
  "Planifie un post pour une date/heure future sur un brand.",
  {
    brand_id: z.string().describe("UUID du brand"),
    integration_ids: z
      .array(z.string())
      .describe("IDs des comptes cibles"),
    content: z.string().describe("Texte du post"),
    publish_at: z
      .string()
      .describe("Date ISO 8601 ex: 2026-04-15T10:00:00Z"),
    media_urls: z
      .array(z.string())
      .optional()
      .describe("URLs médias optionnelles"),
  },
  async ({ brand_id, integration_ids, content, publish_at, media_urls }) => {
    try {
      return ok(
        await rs3.post(`/api/v2/publish/brands/${brand_id}/schedule`, {
          integration_ids,
          content,
          publish_at,
          media_urls: media_urls ?? [],
        })
      );
    } catch (e) {
      return fail(e);
    }
  }
);

// ═══════════════════════════════════════════════════════════════════════════
// TOOLS 8-11 — CALENDRIER ÉDITORIAL
// ═══════════════════════════════════════════════════════════════════════════

server.tool(
  "rs3_generate_calendar",
  `Génère 1 mois complet de contenu éditorial pour un brand.
Ilyas crée le contenu adapté à la niche et aux plateformes.
Exemple : "Génère 3 posts + 2 stories/jour pour Le Family's en avril"`,
  {
    brand_id: z.string().describe("UUID du brand"),
    posts_per_day: z
      .number()
      .min(1)
      .max(10)
      .optional()
      .describe("Posts par jour (1-10). Défaut: 3"),
    stories_per_day: z
      .number()
      .min(0)
      .max(5)
      .optional()
      .describe("Stories par jour (0-5). Défaut: 2"),
    platforms: z
      .array(z.string())
      .optional()
      .describe(
        "Plateformes ex: ['instagram','facebook','tiktok']. Défaut: toutes"
      ),
    month: z
      .string()
      .optional()
      .describe("Mois cible format YYYY-MM ex: 2026-04. Défaut: mois actuel"),
  },
  async ({ brand_id, posts_per_day, stories_per_day, platforms, month }) => {
    try {
      return ok(
        await rs3.post(`/api/v2/calendar/${brand_id}/generate`, {
          posts_per_day: posts_per_day ?? 3,
          stories_per_day: stories_per_day ?? 2,
          platforms: platforms ?? ["instagram", "facebook", "tiktok"],
          month: month ?? null,
        })
      );
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "rs3_get_calendar",
  "Récupère le calendrier éditorial d'un brand (posts planifiés, statuts, heures).",
  {
    brand_id: z.string().describe("UUID du brand"),
    status: z
      .string()
      .optional()
      .describe(
        "Filtre statut: pending_approval | approved | scheduled | published"
      ),
    month: z.string().optional().describe("Filtre mois format YYYY-MM"),
  },
  async ({ brand_id, status, month }) => {
    try {
      const params = new URLSearchParams();
      if (status) params.append("status", status);
      if (month) params.append("month", month);
      const qs = params.toString();
      return ok(
        await rs3.get(
          `/api/v2/calendar/${brand_id}${qs ? `?${qs}` : ""}`
        )
      );
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "rs3_approve_all_calendar",
  "Approuve tous les posts en attente d'un brand d'un coup.",
  {
    brand_id: z.string().describe("UUID du brand"),
  },
  async ({ brand_id }) => {
    try {
      return ok(await rs3.post(`/api/v2/calendar/${brand_id}/approve-all`));
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "rs3_approve_post",
  "Approuve un post spécifique du calendrier éditorial.",
  {
    brand_id: z.string().describe("UUID du brand"),
    post_id: z.string().describe("UUID du post à approuver"),
  },
  async ({ brand_id, post_id }) => {
    try {
      return ok(
        await rs3.post(
          `/api/v2/calendar/${brand_id}/posts/${post_id}/approve`
        )
      );
    } catch (e) {
      return fail(e);
    }
  }
);

// ═══════════════════════════════════════════════════════════════════════════
// TOOLS 12-13 — ILYAS / WAR ROOM
// ═══════════════════════════════════════════════════════════════════════════

server.tool(
  "rs3_chat_ilyas",
  `Envoie un message à Ilyas pour un brand spécifique.
Ilyas connaît la niche, le DNA et l'historique du brand.
Exemples :
- "Génère 3 idées de posts pour la semaine de Pâques"
- "Comment répondre à ce commentaire négatif ?"
- "Quelle stratégie pour le mois de juin ?"`,
  {
    brand_id: z.string().describe("UUID du brand"),
    message: z.string().describe("Message pour Ilyas"),
    session_id: z
      .string()
      .optional()
      .describe(
        "ID de session pour continuer une conversation existante (optionnel)"
      ),
  },
  async ({ brand_id, message, session_id }) => {
    try {
      return ok(
        await rs3.post(`/api/v2/ilyas/${brand_id}/chat`, {
          message,
          session_id: session_id ?? null,
        })
      );
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "rs3_analyze_url",
  `Analyse une URL pour un brand et retourne un plan stratégique.
Utilise la War Room Ilyas : Firecrawl + Claude Sonnet.
Exemples :
- "Analyse ce TikTok concurrent pour Le Family's"
- "Que peut-on apprendre de ce site concurrent ?"`,
  {
    brand_id: z.string().describe("UUID du brand"),
    url: z
      .string()
      .describe("URL à analyser (TikTok, Instagram, article, site...)"),
  },
  async ({ brand_id, url }) => {
    try {
      return ok(
        await rs3.post(`/api/v2/war-room/${brand_id}/analyze-url`, { url })
      );
    } catch (e) {
      return fail(e);
    }
  }
);

// ═══════════════════════════════════════════════════════════════════════════
// TOOLS 14-15 — VIDÉO
// ═══════════════════════════════════════════════════════════════════════════

server.tool(
  "rs3_video_pricing",
  "Récupère le pricing des templates vidéo RS3.",
  {},
  async () => {
    try {
      return ok(await rs3.get("/api/v2/templates/cinematic/pricing"));
    } catch (e) {
      return fail(e);
    }
  }
);

server.tool(
  "rs3_video_templates",
  `Liste les templates vidéo disponibles dans RS3 :
- Breakout V4 : sujet qui sort du cadre Instagram — GRATUIT
- Cinematic Food : photo → vidéo cinématique via Kling 2.6 Pro`,
  {},
  async () => {
    return ok({
      templates: [
        {
          id: "breakout_v4",
          name: "Breakout V4",
          description:
            "Sujet sort du cadre Instagram — style Tim Gray. GRATUIT.",
          cost_usd: 0.0,
          duration_seconds: 3,
          input: "image",
          endpoint: "POST /api/v2/templates/breakout/prepare",
        },
        {
          id: "cinematic_food",
          name: "Cinematic Food",
          description: "Photo → vidéo cinématique via Kling 2.6 Pro.",
          cost_usd: 0.35,
          duration_seconds: 5,
          input: "image",
          food_types: ["default", "burger", "pizza", "dessert", "drink"],
          endpoint: "POST /api/v2/templates/cinematic/generate",
        },
        {
          id: "promo_flash",
          name: "Promo Flash",
          description: "Photo + texte → vidéo promo animée.",
          cost_usd: 0.35,
          duration_seconds: 8,
          input: "image + text",
          endpoint: "POST /api/v2/templates/promo-flash/generate",
        },
      ],
    });
  }
);

// ═══════════════════════════════════════════════════════════════════════════
// DÉMARRAGE
// ═══════════════════════════════════════════════════════════════════════════

const transport = new StdioServerTransport();
await server.connect(transport);
process.stderr.write("✅ MCP Server RS3 démarré — 15 tools disponibles\n");

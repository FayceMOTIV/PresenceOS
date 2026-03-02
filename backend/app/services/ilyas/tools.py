"""
PresenceOS — Ilyas Tool Definitions (Sprint 3: Intelligence Module)

Claude Anthropic tool_use format for native tool calling.
Each tool maps to an intelligence module method or an existing action.
"""

# ── Existing action tools (Sprint 1) ──

GENERATE_POST_TOOL = {
    "name": "generate_post",
    "description": "Generate a social media post with caption and hashtags for the brand.",
    "input_schema": {
        "type": "object",
        "properties": {
            "platform": {
                "type": "string",
                "enum": ["instagram", "facebook", "tiktok", "linkedin"],
                "description": "Target social media platform.",
            },
            "post_type": {
                "type": "string",
                "enum": ["post", "reel", "story", "carousel"],
                "description": "Type of content to generate.",
            },
            "topic": {
                "type": "string",
                "description": "Topic or theme for the post.",
            },
        },
        "required": ["platform", "post_type", "topic"],
    },
}

ANALYZE_PHOTO_TOOL = {
    "name": "analyze_photo",
    "description": "Analyze a food photo and suggest social media content ideas.",
    "input_schema": {
        "type": "object",
        "properties": {
            "image_url": {
                "type": "string",
                "description": "URL of the image to analyze.",
            },
        },
        "required": ["image_url"],
    },
}

SCHEDULE_POST_TOOL = {
    "name": "schedule_post",
    "description": "Schedule a post for optimal publishing time.",
    "input_schema": {
        "type": "object",
        "properties": {
            "proposal_id": {
                "type": "string",
                "description": "ID of the proposal to schedule.",
            },
            "preferred_time": {
                "type": "string",
                "description": "ISO datetime or 'optimal' for AI-picked time.",
            },
        },
        "required": ["proposal_id"],
    },
}

# ── Intelligence tools (Sprint 3) ──

GOOGLE_TRENDS_TOOL = {
    "name": "google_trends",
    "description": (
        "Recherche les tendances Google en France pour un mot-clé food/restaurant. "
        "Retourne les recherches associées en hausse et les plus populaires."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "Mot-clé à rechercher (ex: 'burger', 'brunch', 'restaurant').",
                "default": "restaurant",
            },
        },
        "required": [],
    },
}

COMPARE_TRENDS_TOOL = {
    "name": "compare_trends",
    "description": (
        "Compare l'intérêt de plusieurs mots-clés sur Google Trends France (3 mois). "
        "Utile pour décider quel sujet poster."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Liste de mots-clés à comparer (max 5).",
                "maxItems": 5,
            },
        },
        "required": ["keywords"],
    },
}

INSTAGRAM_COMPETITOR_TOOL = {
    "name": "instagram_competitor",
    "description": (
        "Analyse le profil Instagram d'un concurrent : followers, engagement rate, "
        "derniers posts, hashtags utilisés. Données publiques uniquement."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "username": {
                "type": "string",
                "description": "Nom d'utilisateur Instagram (sans @).",
            },
        },
        "required": ["username"],
    },
}

INSTAGRAM_HASHTAG_TOOL = {
    "name": "instagram_hashtag",
    "description": (
        "Analyse un hashtag Instagram : nombre de posts, top posts récents. "
        "Utile pour choisir les meilleurs hashtags."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "tag": {
                "type": "string",
                "description": "Hashtag à analyser (sans #).",
            },
        },
        "required": ["tag"],
    },
}

TIKTOK_SEARCH_TOOL = {
    "name": "tiktok_search",
    "description": (
        "Recherche des vidéos TikTok par mot-clé. Retourne les vidéos les plus "
        "pertinentes avec vues, likes, commentaires."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "keyword": {
                "type": "string",
                "description": "Mot-clé de recherche TikTok.",
            },
            "count": {
                "type": "integer",
                "description": "Nombre de résultats (max 20).",
                "default": 10,
            },
        },
        "required": ["keyword"],
    },
}

TIKTOK_VIDEO_INFO_TOOL = {
    "name": "tiktok_video_info",
    "description": (
        "Extrait les métadonnées d'une vidéo TikTok (titre, vues, likes, tags). "
        "Accepte une URL TikTok."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL complète de la vidéo TikTok.",
            },
        },
        "required": ["url"],
    },
}

REDDIT_SEARCH_TOOL = {
    "name": "reddit_search",
    "description": (
        "Recherche des discussions Reddit sur la food/restauration en France. "
        "Explore r/france, r/AskFrance, r/FrenchFood, r/Cooking."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Requête de recherche.",
            },
            "subreddits": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Subreddits à explorer (défaut: france, AskFrance, FrenchFood, Cooking).",
            },
        },
        "required": ["query"],
    },
}

YOUTUBE_SEARCH_TOOL = {
    "name": "youtube_search",
    "description": (
        "Recherche des vidéos YouTube food/restaurant en France. "
        "Retourne titre, chaîne, vues, likes pour chaque vidéo."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Requête de recherche YouTube.",
            },
            "max_results": {
                "type": "integer",
                "description": "Nombre de résultats (max 25).",
                "default": 10,
            },
        },
        "required": ["query"],
    },
}

YOUTUBE_CHANNEL_TOOL = {
    "name": "youtube_channel",
    "description": (
        "Analyse une chaîne YouTube : abonnés, vues totales, vidéos récentes. "
        "Utile pour surveiller des food influencers."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "channel_id": {
                "type": "string",
                "description": "ID de la chaîne YouTube (format UCxxxxxxxx).",
            },
        },
        "required": ["channel_id"],
    },
}


# ── Tool collections ──

# Original Sprint 1 tools (actions)
ACTION_TOOLS = [GENERATE_POST_TOOL, ANALYZE_PHOTO_TOOL, SCHEDULE_POST_TOOL]

# Intelligence tools (Sprint 3)
INTELLIGENCE_TOOLS = [
    GOOGLE_TRENDS_TOOL,
    COMPARE_TRENDS_TOOL,
    INSTAGRAM_COMPETITOR_TOOL,
    INSTAGRAM_HASHTAG_TOOL,
    TIKTOK_SEARCH_TOOL,
    TIKTOK_VIDEO_INFO_TOOL,
    REDDIT_SEARCH_TOOL,
    YOUTUBE_SEARCH_TOOL,
    YOUTUBE_CHANNEL_TOOL,
]

# All tools combined
ILYAS_TOOLS = ACTION_TOOLS + INTELLIGENCE_TOOLS

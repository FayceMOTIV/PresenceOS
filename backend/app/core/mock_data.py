"""
PresenceOS - Mock Data Provider (Dev/Degraded Mode)

Provides realistic demo data for the restaurant "Family's" when
the database is unavailable. Each response includes `degraded: true`
so the frontend can display an appropriate banner.
"""

MOCK_BRAND = {
    "id": "demo-brand-001",
    "name": "Family's",
    "slug": "familys",
    "description": "Restaurant familial mediterraneen",
    "industry": "restaurant",
    "logo_url": None,
    "is_active": True,
    "workspace_id": "demo-workspace-001",
    "voice": {
        "tone": "chaleureux",
        "language": "fr",
        "emoji_level": "moderate",
        "hashtag_strategy": "mixed",
    },
    "degraded": True,
}

MOCK_BRANDS_LIST = [MOCK_BRAND]

MOCK_POSTS_LIST = {
    "items": [
        {
            "id": "demo-post-001",
            "caption": "Notre specialite du jour: tagine aux legumes de saison",
            "status": "draft",
            "platform": "instagram",
            "media_type": "image",
            "scheduled_at": "2026-02-14T12:00:00Z",
            "created_at": "2026-02-10T10:00:00Z",
        },
        {
            "id": "demo-post-002",
            "caption": "Happy Valentine's! Menu special pour les amoureux",
            "status": "scheduled",
            "platform": "facebook",
            "media_type": "image",
            "scheduled_at": "2026-02-14T18:00:00Z",
            "created_at": "2026-02-10T11:00:00Z",
        },
    ],
    "total": 2,
    "degraded": True,
}

MOCK_CALENDAR = {
    "brand_id": "demo-brand-001",
    "start_date": "2026-02-01T00:00:00Z",
    "end_date": "2026-02-28T23:59:59Z",
    "days": [
        {
            "date": "2026-02-14",
            "scheduled_posts": [
                {
                    "id": "demo-post-001",
                    "caption": "Notre specialite du jour",
                    "status": "scheduled",
                    "scheduled_at": "2026-02-14T12:00:00Z",
                }
            ],
            "ideas": [],
        },
        {
            "date": "2026-02-17",
            "scheduled_posts": [],
            "ideas": [{"title": "Post hebdomadaire — Plat du lundi"}],
        },
    ],
    "degraded": True,
}

MOCK_DASHBOARD_METRICS = {
    "total_posts_published": 12,
    "total_posts_scheduled": 3,
    "total_impressions": 4820,
    "total_engagement": 387,
    "average_engagement_rate": 4.2,
    "top_platform": "instagram",
    "best_posting_time": "12:00-14:00",
    "ai_insight": "Vos posts avec des photos de plats obtiennent 2.3x plus d'engagement. Continuez !",
    "degraded": True,
}

MOCK_PLATFORM_BREAKDOWN = [
    {
        "platform": "instagram",
        "posts_count": 8,
        "total_impressions": 3200,
        "total_engagement": 280,
        "average_engagement_rate": 5.1,
    },
    {
        "platform": "facebook",
        "posts_count": 4,
        "total_impressions": 1620,
        "total_engagement": 107,
        "average_engagement_rate": 3.2,
    },
]

MOCK_TOP_POSTS = {
    "posts": [
        {
            "post_id": "demo-post-top-1",
            "platform_post_url": None,
            "published_at": "2026-02-05T12:00:00Z",
            "caption_preview": "Notre couscous royal, une recette transmise de generation en generation...",
            "impressions": 1200,
            "reach": 980,
            "likes": 89,
            "comments": 12,
            "shares": 7,
            "engagement_rate": 6.8,
        }
    ],
    "degraded": True,
}

MOCK_LEARNING_INSIGHTS = {
    "summary": "Basee sur vos 30 derniers jours de contenu, voici ce qui fonctionne :",
    "what_works": [
        "Les photos de plats en gros plan obtiennent 2.3x plus d'engagement",
        "Le contenu behind-the-scenes en cuisine performe tres bien",
        "Les posts du mardi et jeudi midi ont le meilleur reach",
    ],
    "recommendations": [
        "Postez plus de contenu video — votre audience repond bien au mouvement",
        "Meilleurs creneaux : Mar-Jeu 12:00-14:00 et 18:00-20:00",
        "Incluez un call-to-action dans vos captions pour plus d'engagement",
    ],
    "content_mix_suggestion": {
        "education": 20,
        "entertainment": 25,
        "engagement": 20,
        "promotion": 15,
        "behind_scenes": 20,
    },
    "degraded": True,
}

MOCK_KNOWLEDGE_LIST = [
    {
        "id": "demo-knowledge-001",
        "brand_id": "demo-brand-001",
        "knowledge_type": "menu_item",
        "title": "Couscous Royal",
        "content": "Notre plat signature, prepare avec du poulet, agneau et merguez. Servi chaque vendredi.",
        "category": "Plats principaux",
        "is_active": True,
        "is_featured": True,
        "created_at": "2026-01-15T10:00:00Z",
    },
    {
        "id": "demo-knowledge-002",
        "brand_id": "demo-brand-001",
        "knowledge_type": "brand_value",
        "title": "Notre histoire",
        "content": "Family's est un restaurant familial fonde en 2015, specialise dans la cuisine mediterraneenne authentique.",
        "category": "A propos",
        "is_active": True,
        "is_featured": False,
        "created_at": "2026-01-10T10:00:00Z",
    },
]

MOCK_KNOWLEDGE_CATEGORIES = {
    "categories": ["A propos", "Plats principaux", "Desserts", "Valeurs"],
    "degraded": True,
}

MOCK_IDEAS_LIST = [
    {
        "id": "demo-idea-001",
        "brand_id": "demo-brand-001",
        "title": "Saint-Valentin — Menu special couples",
        "description": "Mettre en avant le menu special Saint-Valentin avec une photo du dressage",
        "content_pillar": "promotion",
        "status": "approved",
        "platforms": ["instagram", "facebook"],
        "created_at": "2026-02-08T10:00:00Z",
    },
    {
        "id": "demo-idea-002",
        "brand_id": "demo-brand-001",
        "title": "Behind the scenes — Preparation du couscous",
        "description": "Video courte montrant la preparation du couscous en cuisine",
        "content_pillar": "behind_scenes",
        "status": "new",
        "platforms": ["instagram"],
        "created_at": "2026-02-09T10:00:00Z",
    },
]

MOCK_DRAFTS_LIST = [
    {
        "id": "demo-draft-001",
        "brand_id": "demo-brand-001",
        "caption": "Decouvrez notre menu Saint-Valentin ! Reservation au 01 23 45 67 89",
        "status": "draft",
        "platform": "instagram",
        "media_type": "image",
        "hashtags": ["#familys", "#saintvalentin", "#restaurant"],
        "created_at": "2026-02-09T14:00:00Z",
    },
]

MOCK_CONNECTORS_LIST = [
    {
        "id": "demo-connector-001",
        "brand_id": "demo-brand-001",
        "platform": "instagram",
        "account_name": "@familys_restaurant",
        "status": "connected",
        "created_at": "2026-01-20T10:00:00Z",
    },
    {
        "id": "demo-connector-002",
        "brand_id": "demo-brand-001",
        "platform": "facebook",
        "account_name": "Family's Restaurant",
        "status": "connected",
        "created_at": "2026-01-20T10:05:00Z",
    },
]

MOCK_AUTOPILOT_CONFIG = {
    "id": "demo-autopilot-001",
    "brand_id": "demo-brand-001",
    "is_active": False,
    "frequency": "daily",
    "platforms": ["instagram", "facebook"],
    "content_pillars": ["promotion", "engagement", "behind_scenes"],
    "approval_required": True,
    "created_at": "2026-02-01T10:00:00Z",
    "degraded": True,
}

MOCK_MEDIA_ASSETS = {
    "items": [],
    "total": 0,
    "degraded": True,
}

MOCK_MEDIA_STATS = {
    "total_assets": 0,
    "total_size_bytes": 0,
    "by_type": {},
    "by_source": {},
    "degraded": True,
}

MOCK_SETTINGS = {
    "brand": MOCK_BRAND,
    "notifications": {"email": True, "push": False},
    "timezone": "Europe/Paris",
    "language": "fr",
    "degraded": True,
}

MOCK_WORKSPACE = {
    "id": "demo-workspace-001",
    "name": "Family's Workspace",
    "slug": "familys-workspace",
    "owner_id": "demo-user-001",
    "brands": MOCK_BRANDS_LIST,
    "degraded": True,
}

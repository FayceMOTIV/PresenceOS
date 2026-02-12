"""
PresenceOS - Database Seed Script

Run with: python scripts/seed.py
"""
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.core.database import async_session_maker
from app.core.security import get_password_hash, get_token_encryption
from app.models.user import User, Workspace, WorkspaceMember, UserRole
from app.models.brand import Brand, BrandVoice, BrandType
from app.models.content import (
    ContentIdea,
    ContentDraft,
    IdeaSource,
    IdeaStatus,
    Platform,
    DraftStatus,
)
from app.models.publishing import (
    SocialConnector,
    ScheduledPost,
    MetricsSnapshot,
    SocialPlatform,
    ConnectorStatus,
    PostStatus,
)


async def seed():
    """Seed the database with demo data."""
    async with async_session_maker() as db:
        print("Starting database seed...")

        # Check if already seeded (idempotent)
        result = await db.execute(
            select(User).where(User.email == "demo@presenceos.com")
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("Demo user already exists. Skipping seed.")
            return

        print("\n[1/9] Creating demo user...")
        # Create demo user
        user = User(
            email="demo@presenceos.com",
            hashed_password=get_password_hash("Demo123!"),
            full_name="Faïçal Kriourar",
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        await db.flush()
        print(f"   ✓ Created user: {user.email}")

        print("\n[2/9] Creating workspace...")
        # Create workspace
        workspace = Workspace(
            name="Mon Workspace",
            slug="mon-workspace",
            timezone="Europe/Paris",
            default_language="fr",
        )
        db.add(workspace)
        await db.flush()
        print(f"   ✓ Created workspace: {workspace.name}")

        print("\n[3/9] Adding workspace member...")
        # Add user as owner
        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=user.id,
            role=UserRole.OWNER,
        )
        db.add(member)
        await db.flush()
        print(f"   ✓ User added as OWNER to workspace")

        print("\n[4/9] Creating brand...")
        # Create restaurant brand
        brand = Brand(
            workspace_id=workspace.id,
            name="Le Petit Bistrot",
            slug="le-petit-bistrot",
            brand_type=BrandType.RESTAURANT,
            description="Un bistrot authentique au coeur de Paris, proposant une cuisine française traditionnelle avec des produits frais et de saison. Ambiance chaleureuse et conviviale.",
            locations=["Paris 11e"],
            target_persona={
                "name": "Parisiens gourmets",
                "age_range": "25-55",
                "interests": ["gastronomie", "vin", "culture"],
                "pain_points": ["cherche authenticité", "veut qualité/prix"],
            },
            constraints={
                "opening_hours": {"mon-fri": "12:00-14:30, 19:00-22:30", "sat-sun": "12:00-23:00"},
                "closed_days": ["Monday lunch"],
            },
            content_pillars={
                "education": 20,
                "entertainment": 25,
                "engagement": 25,
                "promotion": 15,
                "behind_scenes": 15,
            },
        )
        db.add(brand)
        await db.flush()
        print(f"   ✓ Created brand: {brand.name}")

        print("\n[5/9] Creating brand voice...")
        # Brand voice
        brand_voice = BrandVoice(
            brand_id=brand.id,
            tone_formal=40,
            tone_playful=60,
            tone_bold=55,
            tone_technical=20,
            tone_emotional=65,
            example_phrases=[
                "Chez nous, chaque plat raconte une histoire",
                "La tradition française dans l'assiette, la passion dans le coeur",
                "Des saveurs qui vous font voyager dans le temps",
            ],
            words_to_avoid=["cheap", "fast", "industriel"],
            words_to_prefer=["authentique", "fait maison", "tradition", "passion", "savoir-faire"],
            emojis_allowed=["🍷", "🍽️", "👨‍🍳", "❤️", "✨", "🇫🇷"],
            max_emojis_per_post=3,
            hashtag_style="lowercase",
            primary_language="fr",
            allow_english_terms=False,
            custom_instructions="Ton chaleureux et passionné. Mettre en avant l'authenticité, le savoir-faire et la convivialité à la française.",
        )
        db.add(brand_voice)
        print(f"   ✓ Created brand voice with tone settings")

        print("\n[6/9] Creating social connector...")
        # Social connector for Instagram
        token_encryption = get_token_encryption()
        connector = SocialConnector(
            brand_id=brand.id,
            platform=SocialPlatform.INSTAGRAM,
            account_id="demo_instagram_account_123",
            account_name="Le Petit Bistrot",
            account_username="@lepetitbistrot",
            status=ConnectorStatus.CONNECTED,
            access_token_encrypted=token_encryption.encrypt("demo_token"),
            platform_data={
                "business_account_id": "demo_business_123",
                "page_id": "demo_page_456",
            },
        )
        db.add(connector)
        await db.flush()
        print(f"   ✓ Created Instagram connector for {connector.account_username}")

        print("\n[7/9] Creating content ideas...")
        # Content ideas
        ideas_data = [
            {
                "title": "Recette traditionnelle du boeuf bourguignon",
                "description": "Partager notre recette familiale de boeuf bourguignon, mijotée pendant 4 heures. Montrer les étapes clés et les secrets du chef.",
                "status": IdeaStatus.APPROVED,
                "source": IdeaSource.USER_CREATED,
                "content_pillar": "education",
                "target_platforms": ["instagram_post", "instagram_reel"],
                "hooks": [
                    "Le secret d'un boeuf bourguignon parfait ? 4h de cuisson et beaucoup d'amour ❤️",
                    "Notre chef vous dévoile SA recette de boeuf bourguignon 👨‍🍳",
                ],
            },
            {
                "title": "Coulisses du marché matinal",
                "description": "Vidéo du chef au marché Aligre à 6h du matin pour choisir les produits frais de la journée.",
                "status": IdeaStatus.APPROVED,
                "source": IdeaSource.AI_GENERATED,
                "content_pillar": "behind_scenes",
                "target_platforms": ["instagram_story", "instagram_reel"],
                "hooks": [
                    "Il est 6h du matin au marché Aligre... Suivez-nous ! 🌅",
                    "Comment on choisit les meilleurs produits pour vous",
                ],
            },
            {
                "title": "Menu de printemps - asperges et morilles",
                "description": "Annonce du nouveau menu de saison avec asperges blanches et morilles.",
                "status": IdeaStatus.NEW,
                "source": IdeaSource.CALENDAR_EVENT,
                "content_pillar": "promotion",
                "target_platforms": ["instagram_post", "facebook"],
                "suggested_date": datetime.now(timezone.utc) + timedelta(days=3),
            },
            {
                "title": "Question du jour : votre plat français préféré ?",
                "description": "Post d'engagement pour créer de l'interaction avec la communauté.",
                "status": IdeaStatus.APPROVED,
                "source": IdeaSource.AI_GENERATED,
                "content_pillar": "engagement",
                "target_platforms": ["instagram_post"],
                "hooks": [
                    "Question du jour : quel est VOTRE plat français préféré ? 🇫🇷",
                    "On est curieux... Votre plat réconfort français ?",
                ],
            },
            {
                "title": "Histoire de notre bistrot - 3 générations",
                "description": "Raconter l'histoire familiale du restaurant, de la grand-mère à aujourd'hui.",
                "status": IdeaStatus.NEW,
                "source": IdeaSource.USER_CREATED,
                "content_pillar": "entertainment",
                "target_platforms": ["instagram_post"],
            },
        ]

        created_ideas = []
        for idea_data in ideas_data:
            idea = ContentIdea(
                brand_id=brand.id,
                **idea_data
            )
            db.add(idea)
            created_ideas.append(idea)
        await db.flush()
        print(f"   ✓ Created {len(created_ideas)} content ideas")

        print("\n[8/9] Creating content drafts and scheduled posts...")
        # Content drafts
        now = datetime.now(timezone.utc)

        draft1 = ContentDraft(
            brand_id=brand.id,
            idea_id=created_ideas[0].id,  # boeuf bourguignon
            platform=Platform.INSTAGRAM_POST,
            status=DraftStatus.SCHEDULED,
            caption="Le secret d'un boeuf bourguignon parfait ? 4h de cuisson et beaucoup d'amour ❤️\n\nNotre chef vous partage sa recette familiale, celle qui a traversé trois générations. Des morceaux de boeuf fondants, une sauce onctueuse au vin rouge, et ces légumes qui ont mijoté des heures...\n\nVenez goûter le vrai goût de la tradition française chez nous ! 👨‍🍳",
            hashtags=["#boeufbourguignon", "#cuisinefrancaise", "#faitmaison", "#bistrotparisien", "#recettetraditionnelle"],
            media_urls=["https://example.com/images/boeuf-bourguignon.jpg"],
            media_type="image",
            ai_model_used="gpt-4-turbo-preview",
            prompt_version="v2.1",
        )
        db.add(draft1)
        await db.flush()

        draft2 = ContentDraft(
            brand_id=brand.id,
            idea_id=created_ideas[1].id,  # marché matinal
            platform=Platform.INSTAGRAM_POST,
            status=DraftStatus.SCHEDULED,
            caption="6h du matin au marché Aligre 🌅\n\nChaque jour, notre chef sélectionne personnellement les meilleurs produits pour vos assiettes. Des producteurs locaux, des produits de saison, et cette passion qui fait toute la différence.\n\nC'est ça, l'authenticité du Petit Bistrot ✨",
            hashtags=["#coulisses", "#marchealigre", "#produitsfrais", "#chefpassionne", "#paris"],
            media_urls=["https://example.com/images/marche-aligre.jpg"],
            media_type="image",
            ai_model_used="gpt-4-turbo-preview",
            prompt_version="v2.1",
        )
        db.add(draft2)
        await db.flush()

        draft3 = ContentDraft(
            brand_id=brand.id,
            idea_id=created_ideas[3].id,  # question engagement
            platform=Platform.INSTAGRAM_POST,
            status=DraftStatus.SCHEDULED,
            caption="Question du jour : quel est VOTRE plat français préféré ? 🇫🇷\n\nBoeuf bourguignon, coq au vin, blanquette de veau, pot-au-feu... La cuisine française regorge de merveilles !\n\nDites-nous tout en commentaire 👇 On est curieux de découvrir vos classiques ❤️",
            hashtags=["#cuisinefrancaise", "#platfrancais", "#gastronomie", "#bistrot", "#questiondujour"],
            media_type="image",
            ai_model_used="gpt-4-turbo-preview",
            prompt_version="v2.1",
        )
        db.add(draft3)
        await db.flush()

        print(f"   ✓ Created 3 content drafts")

        # Scheduled posts (spread over next 7 days)
        scheduled_post1 = ScheduledPost(
            brand_id=brand.id,
            draft_id=draft1.id,
            connector_id=connector.id,
            scheduled_at=now + timedelta(days=2, hours=12),
            timezone="Europe/Paris",
            status=PostStatus.SCHEDULED,
            content_snapshot={
                "caption": draft1.caption,
                "hashtags": draft1.hashtags,
                "media_urls": draft1.media_urls,
                "platform": "instagram_post",
            },
        )
        db.add(scheduled_post1)

        scheduled_post2 = ScheduledPost(
            brand_id=brand.id,
            draft_id=draft2.id,
            connector_id=connector.id,
            scheduled_at=now + timedelta(days=5, hours=9),
            timezone="Europe/Paris",
            status=PostStatus.SCHEDULED,
            content_snapshot={
                "caption": draft2.caption,
                "hashtags": draft2.hashtags,
                "media_urls": draft2.media_urls,
                "platform": "instagram_post",
            },
        )
        db.add(scheduled_post2)

        scheduled_post3 = ScheduledPost(
            brand_id=brand.id,
            draft_id=draft3.id,
            connector_id=connector.id,
            scheduled_at=now + timedelta(days=7, hours=18),
            timezone="Europe/Paris",
            status=PostStatus.SCHEDULED,
            content_snapshot={
                "caption": draft3.caption,
                "hashtags": draft3.hashtags,
                "platform": "instagram_post",
            },
        )
        db.add(scheduled_post3)
        await db.flush()

        print(f"   ✓ Created 3 scheduled posts (over next 7 days)")

        print("\n[9/9] Creating metrics snapshots...")
        # Metrics snapshots
        metric1 = MetricsSnapshot(
            connector_id=connector.id,
            snapshot_date=now - timedelta(days=1),
            impressions=1245,
            reach=987,
            likes=156,
            comments=23,
            shares=8,
            saves=34,
            engagement_rate=17.8,
            followers_count=2450,
        )
        db.add(metric1)

        metric2 = MetricsSnapshot(
            connector_id=connector.id,
            snapshot_date=now - timedelta(days=2),
            impressions=2103,
            reach=1543,
            likes=234,
            comments=45,
            shares=12,
            saves=67,
            engagement_rate=23.4,
            followers_count=2443,
            followers_gained=7,
        )
        db.add(metric2)

        await db.flush()
        print(f"   ✓ Created 2 metrics snapshots")

        # Commit all changes
        await db.commit()

        print("\n" + "=" * 60)
        print("✅ Database seeded successfully!")
        print("=" * 60)
        print("\nDemo credentials:")
        print(f"  Email:    demo@presenceos.com")
        print(f"  Password: Demo123!")
        print("\nSeeded data:")
        print(f"  • 1 User (verified)")
        print(f"  • 1 Workspace (Mon Workspace)")
        print(f"  • 1 Brand (Le Petit Bistrot - Restaurant)")
        print(f"  • 1 Brand Voice (configured with French tone)")
        print(f"  • 1 Instagram Connector (connected)")
        print(f"  • 5 Content Ideas (various statuses)")
        print(f"  • 3 Content Drafts (all scheduled)")
        print(f"  • 3 Scheduled Posts (next 7 days)")
        print(f"  • 2 Metrics Snapshots (sample engagement)")
        print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())

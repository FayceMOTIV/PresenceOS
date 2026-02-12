#!/usr/bin/env python3
"""
PresenceOS - Telegram Polling Test Script

Runs the Telegram bot in polling mode for local testing (no ngrok needed).
Creates tables and seeds a test brand "Family's" if the DB is empty.

Usage:
    cd backend
    python3 scripts/test_telegram_polling.py

Press Ctrl+C to stop.
"""
import asyncio
import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Load .env (pydantic-settings will read it, but ensure we're in the right dir)
os.chdir(os.path.dirname(os.path.dirname(__file__)))


async def init_database():
    """Create all tables (skip pgvector if not available)."""
    from app.core.database import engine, Base

    # Import all models so Base.metadata knows about them
    import app.models  # noqa: F401

    print("[DB] Creating tables...")
    async with engine.begin() as conn:
        # Try pgvector extension (may fail on fresh installs)
        try:
            from sqlalchemy import text
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        except Exception:
            print("[DB] pgvector extension not available, skipping")
        await conn.run_sync(Base.metadata.create_all)
    print("[DB] Tables ready.")


async def seed_brand_if_empty():
    """
    If no Brand exists, seed "Family's" with a Workspace, BrandVoice,
    and an AutopilotConfig linked to it.
    """
    from app.core.database import async_session_maker
    from sqlalchemy import select, func

    async with async_session_maker() as db:
        # Check if any brand exists
        count_result = await db.execute(
            select(func.count()).select_from(
                select(1).select_from(
                    __import__("app.models.brand", fromlist=["Brand"]).Brand.__table__
                ).subquery()
            )
        )
        brand_count = count_result.scalar()

        if brand_count and brand_count > 0:
            print(f"[Seed] {brand_count} brand(s) already exist, skipping seed.")
            return

        # Need to seed
        from app.models.user import User, Workspace, WorkspaceMember, UserRole
        from app.models.brand import Brand, BrandVoice, BrandType
        from app.models.autopilot import AutopilotConfig, AutopilotFrequency

        print("[Seed] Creating test workspace + brand 'Family\\'s'...")

        # Create a test user
        user = User(
            email="dev@presenceos.com",
            hashed_password="not-a-real-hash",
            full_name="Dev Tester",
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        await db.flush()

        # Create workspace
        workspace = Workspace(
            name="Dev Workspace",
            slug="dev-workspace",
        )
        db.add(workspace)
        await db.flush()

        # Link user to workspace
        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=user.id,
            role=UserRole.OWNER,
        )
        db.add(member)

        # Create brand "Family's"
        brand = Brand(
            workspace_id=workspace.id,
            name="Family's",
            slug="familys",
            brand_type=BrandType.RESTAURANT,
            description="Restaurant familial halal a Paris - cuisine mediterraneenne et orientale.",
            website_url="https://familys-restaurant.com",
            locations=["Paris 15e"],
            target_persona={
                "name": "Familles CSP+",
                "age_range": "30-50",
                "interests": ["gastronomie", "famille", "qualite"],
            },
            content_pillars={
                "education": 15,
                "entertainment": 25,
                "engagement": 25,
                "promotion": 20,
                "behind_scenes": 15,
            },
            is_active=True,
        )
        db.add(brand)
        await db.flush()

        # Create brand voice
        voice = BrandVoice(
            brand_id=brand.id,
            tone_formal=30,
            tone_playful=70,
            tone_bold=60,
            tone_technical=10,
            tone_emotional=65,
            example_phrases=[
                "Venez decouvrir nos saveurs!",
                "Un moment en famille, ca n'a pas de prix",
                "Frais, fait maison, avec amour",
            ],
            words_to_avoid=["cheap", "discount"],
            words_to_prefer=["fait maison", "frais", "famille"],
            emojis_allowed=["🍽️", "❤️", "👨‍👩‍👧‍👦", "🔥", "✨"],
            max_emojis_per_post=3,
            hashtag_style="lowercase",
            primary_language="fr",
            allow_english_terms=True,
            custom_instructions="Toujours mentionner que c'est halal. Ton chaleureux et familial.",
        )
        db.add(voice)

        # Create autopilot config (enabled, for Telegram fallback)
        config = AutopilotConfig(
            brand_id=brand.id,
            is_enabled=True,
            platforms=["instagram"],
            frequency=AutopilotFrequency.DAILY,
            generation_hour=9,
            auto_publish=False,
            approval_window_hours=4,
            whatsapp_enabled=False,
            preferred_posting_time="10:30",
        )
        db.add(config)

        await db.commit()

        print(f"[Seed] Brand 'Family\\'s' created (id={brand.id})")
        print(f"[Seed] AutopilotConfig created (id={config.id})")
        print(f"[Seed] BrandVoice created")


async def main():
    from telegram import Bot

    # Import after path setup
    from app.core.config import settings

    token = settings.telegram_bot_token
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not set in .env")
        sys.exit(1)

    # Step 1: Init database tables
    await init_database()

    # Step 2: Seed brand if empty
    await seed_brand_if_empty()

    # Step 3: Start polling
    print()
    print(f"Starting Telegram polling bot...")
    print(f"  Token: {token[:10]}...")
    print(f"  DB: {settings.database_url[:50]}...")

    bot = Bot(token=token)
    me = await bot.get_me()
    print(f"  Bot: @{me.username} ({me.first_name})")
    print(f"  ID: {me.id}")
    print()
    print("Listening for messages... (Ctrl+C to stop)")
    print("=" * 60)

    # Remove any existing webhook (required for polling)
    await bot.delete_webhook()

    # Polling loop
    offset = None
    from app.services.telegram_adapter import TelegramAdapter
    adapter = TelegramAdapter()

    while True:
        try:
            updates = await bot.get_updates(offset=offset, timeout=30)
            for update in updates:
                offset = update.update_id + 1

                update_dict = update.to_dict()
                print(f"\n--- Update {update.update_id} ---")
                print(json.dumps(update_dict, indent=2, ensure_ascii=False, default=str))

                try:
                    await adapter.handle_telegram_update(update_dict)
                    print("  -> Processed OK")
                except Exception as e:
                    print(f"  -> Error: {e}")
                    import traceback
                    traceback.print_exc()

        except asyncio.CancelledError:
            break
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Polling error: {e}")
            await asyncio.sleep(5)

    print("\nStopping polling...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBye!")

#!/usr/bin/env python3
"""
PresenceOS - Upload-Post Integration Test (E2E)

Uses stable username "LEFAMILYS" (already has Instagram + Facebook connected).
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# Stable username — matches existing Upload-Post profile
BRAND_USERNAME = "LEFAMILYS"


async def main():
    api_key = os.getenv("UPLOAD_POST_API_KEY", "")
    if not api_key:
        print("UPLOAD_POST_API_KEY non configuree dans .env")
        sys.exit(1)

    print(f"UPLOAD_POST_API_KEY trouvee ({api_key[:12]}...)")
    print("=" * 60)

    # Import after dotenv
    from app.services.social_publisher import SocialPublisher, UploadPostError
    publisher = SocialPublisher(api_key=api_key)

    # ── Step 1: Check if profile exists ──
    print(f"\n[1/4] Verification du profil '{BRAND_USERNAME}'...")
    try:
        profile = await publisher._find_profile(BRAND_USERNAME)
        if profile:
            print(f"  Profil trouve: {profile['username']}")
            social = profile.get("social_accounts", {})
            for platform, data in social.items():
                if isinstance(data, dict) and data:
                    handle = data.get("handle") or data.get("display_name") or "?"
                    print(f"    {platform}: @{handle}")
                else:
                    print(f"    {platform}: (non connecte)")
        else:
            print(f"  Profil introuvable — creation...")
            await publisher.create_brand_profile(BRAND_USERNAME)
            print(f"  Profil cree.")
    except UploadPostError as e:
        print(f"  Erreur: {e}")
        return

    # ── Step 2: Generate JWT URL ──
    print(f"\n[2/4] Generation de l'URL JWT...")
    try:
        url = await publisher.get_social_link_url(
            brand_id=BRAND_USERNAME,
            platforms=["instagram", "facebook", "tiktok"],
            connect_title="Family's Bourg-en-Bresse",
        )
    except UploadPostError as e:
        print(f"  Erreur: {e}")
        return

    # ── Step 3: Test URL accessibility ──
    print(f"\n[3/4] Test d'accessibilite de l'URL...")
    import httpx
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            r = await client.get(url)
            page_ok = r.status_code == 200
            has_error = any(
                s in r.text.lower()
                for s in ["introuvable", "not found", "n'existe pas", "does not exist"]
            )
            if page_ok and not has_error:
                print(f"  URL OK (status {r.status_code}, pas d'erreur)")
            else:
                print(f"  ATTENTION: status={r.status_code}, erreur detectee={has_error}")
    except Exception as e:
        print(f"  Erreur de connexion: {e}")

    print(f"\n  URL JWT (ouvrir sur iPhone):")
    print(f"  {url}")

    # ── Step 4: List connected accounts ──
    print(f"\n[4/4] Comptes connectes...")
    try:
        accounts = await publisher.get_connected_accounts(BRAND_USERNAME)
        connected = [a for a in accounts if a.get("connected")]
        if connected:
            print(f"  {len(connected)} compte(s) connecte(s):")
            for a in connected:
                print(f"    {a['platform']}: @{a.get('username', '?')}")
        else:
            print("  Aucun compte connecte.")
            print("  Ouvrez l'URL ci-dessus pour connecter Instagram.")
            return
    except UploadPostError as e:
        print(f"  Erreur: {e}")
        return

    # ── Bonus: Test publish if Instagram connected ──
    has_ig = any(a["platform"] == "instagram" and a.get("connected") for a in accounts)
    if has_ig:
        print(f"\n[BONUS] Publication test Instagram...")
        try:
            result = await publisher.publish_photo(
                brand_id=BRAND_USERNAME,
                image_url="https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=1080",
                caption="Test PresenceOS — Publication automatique!\n\n#PresenceOS #Test",
                platforms=["instagram"],
            )
            print(f"  Publication reussie!")
            print(f"  Post URL: {result.get('post_url', 'N/A')}")
        except UploadPostError as e:
            print(f"  Erreur de publication: {e}")

    print("\n" + "=" * 60)
    print("Test termine.")


if __name__ == "__main__":
    asyncio.run(main())

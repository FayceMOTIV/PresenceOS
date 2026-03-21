"""
PresenceOS -- Mem0 Onboarding Init Service (Sprint 7)

Initializes Mem0 conversational memory for a brand after onboarding completion.
Stores BusinessDNA fields as individual memories so Ilyas can recall them later.
"""
import logging
from typing import Any

from app.services.ilyas.memory import Mem0Memory

logger = logging.getLogger(__name__)


async def init_mem0_for_brand(
    brand_id: str,
    brand_name: str,
    dna: dict[str, Any],
    scrape_data: dict[str, Any] | None = None,
) -> bool:
    """
    Init Mem0 with the DNA du restaurant after onboarding completion.

    user_id : EXACTLY f"restaurant_{brand_id}"
    Returns True on success, False on failure (NEVER raises).
    """
    user_id = f"restaurant_{brand_id}"
    metadata = {"source": "onboarding", "brand_id": brand_id}

    try:
        mem0 = Mem0Memory()

        # -- 1. Store identity fields as a single memory block --
        identity_parts: list[str] = []
        if brand_name:
            identity_parts.append(f"Le commerce s'appelle {brand_name}.")
        if dna.get("business_type"):
            identity_parts.append(f"C'est un(e) {dna['business_type']}.")
        if dna.get("cuisine_style"):
            identity_parts.append(f"Style de cuisine : {dna['cuisine_style']}.")
        if dna.get("city"):
            loc = dna["city"]
            if dna.get("neighborhood"):
                loc += f" ({dna['neighborhood']})"
            identity_parts.append(f"Localisation : {loc}.")

        if identity_parts:
            await mem0.add(
                messages=[{"role": "user", "content": " ".join(identity_parts)}],
                user_id=user_id,
                metadata=metadata,
            )

        # -- 2. Store personality fields --
        personality_parts: list[str] = []
        if dna.get("ambiance"):
            personality_parts.append(f"Ambiance : {dna['ambiance']}.")
        if dna.get("unique_selling_point"):
            personality_parts.append(f"Point fort : {dna['unique_selling_point']}.")
        if dna.get("target_audience"):
            personality_parts.append(f"Clientele cible : {dna['target_audience']}.")
        if dna.get("tone_of_voice"):
            personality_parts.append(f"Ton de communication : {dna['tone_of_voice']}.")

        if personality_parts:
            await mem0.add(
                messages=[{"role": "user", "content": " ".join(personality_parts)}],
                user_id=user_id,
                metadata=metadata,
            )

        # -- 3. Store content preferences --
        content_parts: list[str] = []
        if dna.get("favorite_platforms"):
            platforms = dna["favorite_platforms"]
            if isinstance(platforms, list):
                platforms = ", ".join(platforms)
            content_parts.append(f"Reseaux sociaux : {platforms}.")
        if dna.get("posting_frequency"):
            content_parts.append(f"Frequence de publication : {dna['posting_frequency']}.")
        if dna.get("signature_dishes"):
            dishes = dna["signature_dishes"]
            if isinstance(dishes, list):
                dishes = ", ".join(dishes)
            content_parts.append(f"Plats/produits signatures : {dishes}.")
        if dna.get("no_go_topics"):
            topics = dna["no_go_topics"]
            if isinstance(topics, list):
                topics = ", ".join(topics)
            content_parts.append(f"Sujets a eviter : {topics}.")

        if content_parts:
            await mem0.add(
                messages=[{"role": "user", "content": " ".join(content_parts)}],
                user_id=user_id,
                metadata=metadata,
            )

        # -- 4. Store scrape data if available --
        if scrape_data:
            scrape_parts: list[str] = []
            if scrape_data.get("website_url"):
                scrape_parts.append(f"Site web : {scrape_data['website_url']}.")
            if scrape_data.get("opening_hours"):
                scrape_parts.append(f"Horaires : {scrape_data['opening_hours']}.")
            if scrape_data.get("price_range"):
                scrape_parts.append(f"Gamme de prix : {scrape_data['price_range']}.")

            # Include any extra scraped fields not already in DNA
            for key, value in scrape_data.items():
                if key not in ("website_url", "opening_hours", "price_range") and value:
                    if isinstance(value, str) and len(value) > 5:
                        scrape_parts.append(f"{key} : {value}.")

            if scrape_parts:
                await mem0.add(
                    messages=[{"role": "user", "content": " ".join(scrape_parts)}],
                    user_id=user_id,
                    metadata={**metadata, "source": "onboarding_scrape"},
                )

        logger.info(
            "Mem0 initialized for brand %s (user_id=%s)",
            brand_id, user_id,
        )
        return True

    except Exception as exc:
        logger.error(
            "Mem0 init failed for brand %s: %s",
            brand_id, exc,
            exc_info=True,
        )
        return False

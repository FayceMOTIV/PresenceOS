"""
PresenceOS - BrandDNA Extraction
Extracts visual identity from reference photos using GPT-4o Vision.
"""
import structlog
from openai import AsyncOpenAI

from app.core.config import settings

logger = structlog.get_logger()


async def extract_brand_dna(image_urls: list[str], brand_name: str, niche: str = "restaurant") -> dict:
    """
    Analyze reference photos to extract BrandDNA (colors, style, atmosphere).
    Returns a dict suitable for storing in brands.brand_dna JSONB column.
    """
    if not settings.openai_api_key:
        logger.warning("OpenAI API key not configured, returning empty BrandDNA")
        return {}

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    # Build vision content with up to 5 images
    content = [
        {
            "type": "text",
            "text": f"""Analyse ces photos du restaurant "{brand_name}" (niche: {niche}).
Extrais l'identité visuelle (BrandDNA) en JSON:
{{
  "dominant_colors": ["#hex1", "#hex2", "#hex3"],
  "secondary_colors": ["#hex1", "#hex2"],
  "atmosphere": "description courte de l'ambiance",
  "lighting_style": "natural|warm|dramatic|bright",
  "food_style": "description du style de présentation des plats",
  "decor_elements": ["élément1", "élément2"],
  "overall_aesthetic": "rustic|modern|traditional|fusion|street_food|fine_dining",
  "brand_personality": ["adjectif1", "adjectif2", "adjectif3"],
  "photo_recommendations": "conseils pour futures photos cohérentes"
}}
Réponds UNIQUEMENT en JSON valide."""
        }
    ]

    for url in image_urls[:5]:
        content.append({
            "type": "image_url",
            "image_url": {"url": url, "detail": "low"}
        })

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": content}],
            max_tokens=1000,
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        import json
        dna = json.loads(response.choices[0].message.content)
        logger.info("BrandDNA extracted", brand=brand_name, colors=dna.get("dominant_colors"))
        return dna

    except Exception as e:
        logger.error("BrandDNA extraction failed", error=str(e))
        return {}

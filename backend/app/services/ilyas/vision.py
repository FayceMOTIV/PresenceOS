"""
PresenceOS - Ilyas Food Vision Analyzer

Uses GPT-4o Vision to analyze food photos with brand context.
"""
import structlog
from openai import AsyncOpenAI

from app.core.config import settings

logger = structlog.get_logger()


class FoodVisionAnalyzer:
    """Analyzes food photos using GPT-4o Vision."""

    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            if not settings.openai_api_key:
                raise RuntimeError("OpenAI API key not configured.")
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    async def analyze_food_photo(
        self,
        image_url: str,
        brand_context: str = "",
    ) -> str:
        """Analyze a food photo and return structured text description.

        Args:
            image_url: Public URL of the image to analyze.
            brand_context: Optional brand info for personalized analysis.

        Returns:
            Structured text analysis of the food photo.
        """
        client = self._get_client()

        system_prompt = (
            "Tu es un expert en photographie culinaire et marketing restaurant. "
            "Analyse cette photo de plat et décris :\n"
            "1. Le plat identifié (nom probable, ingrédients visibles)\n"
            "2. La qualité de la photo (lumière, composition, attrait)\n"
            "3. Les émotions et sensations que la photo évoque\n"
            "4. 2-3 suggestions de légende Instagram basées sur ce plat\n"
            "Réponds en français, de manière concise et enthousiaste."
        )

        if brand_context:
            system_prompt += f"\n\nContexte de la marque :\n{brand_context}"

        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyse cette photo de plat :"},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    },
                ],
                max_tokens=500,
                temperature=0.7,
            )
            analysis = response.choices[0].message.content or ""
            logger.info("Food photo analyzed", image_url=image_url[:80], length=len(analysis))
            return analysis
        except Exception as exc:
            logger.error("Vision analysis failed", error=str(exc))
            return "Impossible d'analyser cette photo pour le moment."

"""Outil CrewAI pour lire le Business Brain d'une marque."""
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional
import asyncio
from sqlalchemy import select
from app.core.database import async_session_maker
from app.models.brand import Brand, BrandVoice, KnowledgeItem


class BrandKnowledgeInput(BaseModel):
    brand_id: str = Field(description="UUID de la marque")
    category: Optional[str] = Field(
        default=None,
        description="Categorie de connaissance a filtrer",
    )
    query: Optional[str] = Field(
        default=None,
        description="Recherche textuelle dans les connaissances",
    )


class BrandKnowledgeTool(BaseTool):
    name: str = "brand_knowledge"
    description: str = (
        "Lit les connaissances du Business Brain d'une marque. "
        "Retourne l'identite, les produits, l'audience cible, le ton de voix et les performances. "
        "Utilise category pour filtrer ou query pour chercher."
    )
    args_schema: type[BaseModel] = BrandKnowledgeInput

    def _run(
        self,
        brand_id: str,
        category: str | None = None,
        query: str | None = None,
    ) -> str:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(
                        asyncio.run,
                        self._async_run(brand_id, category, query),
                    ).result()
            return loop.run_until_complete(
                self._async_run(brand_id, category, query)
            )
        except RuntimeError:
            return asyncio.run(self._async_run(brand_id, category, query))

    async def _async_run(
        self,
        brand_id: str,
        category: str | None,
        query: str | None,
    ) -> str:
        async with async_session_maker() as session:
            # 1. Recuperer la marque
            brand_result = await session.execute(
                select(Brand).where(Brand.id == brand_id)
            )
            brand = brand_result.scalar_one_or_none()
            if not brand:
                return f"Erreur: Marque {brand_id} non trouvee"

            # 2. Recuperer le brand voice
            voice_result = await session.execute(
                select(BrandVoice).where(BrandVoice.brand_id == brand_id)
            )
            voice = voice_result.scalar_one_or_none()

            # 3. Recuperer les knowledge items
            stmt = select(KnowledgeItem).where(
                KnowledgeItem.brand_id == brand_id,
                KnowledgeItem.is_active.is_(True),
            )
            if category:
                stmt = stmt.where(KnowledgeItem.category == category)
            items_result = await session.execute(stmt)
            items = items_result.scalars().all()

            # 4. Formatter le resultat
            output = f"# Marque: {brand.name}\n"
            output += f"Type: {brand.brand_type.value if brand.brand_type else 'N/A'}\n"
            output += f"Description: {brand.description or 'N/A'}\n"
            if brand.website_url:
                output += f"Site web: {brand.website_url}\n"
            if brand.locations:
                output += f"Localisations: {', '.join(brand.locations)}\n"
            if brand.content_pillars:
                output += f"Piliers de contenu: {brand.content_pillars}\n"
            if brand.target_persona:
                output += f"Persona cible: {brand.target_persona}\n"

            if voice:
                output += "\n## Ton de voix\n"
                output += f"- Formel: {voice.tone_formal}/100\n"
                output += f"- Playful: {voice.tone_playful}/100\n"
                output += f"- Bold: {voice.tone_bold}/100\n"
                output += f"- Technique: {voice.tone_technical}/100\n"
                output += f"- Emotionnel: {voice.tone_emotional}/100\n"
                output += f"- Langue: {voice.primary_language}\n"
                output += f"- Style hashtags: {voice.hashtag_style}\n"
                output += f"- Max emojis: {voice.max_emojis_per_post}\n"
                if voice.example_phrases:
                    output += f"- Phrases exemples: {', '.join(voice.example_phrases)}\n"
                if voice.words_to_avoid:
                    output += f"- Mots a eviter: {', '.join(voice.words_to_avoid)}\n"
                if voice.words_to_prefer:
                    output += f"- Mots preferes: {', '.join(voice.words_to_prefer)}\n"
                if voice.custom_instructions:
                    output += f"- Instructions custom: {voice.custom_instructions}\n"

            if items:
                output += f"\n## Connaissances ({len(items)} elements)\n"
                for item in items[:20]:
                    output += f"- [{item.knowledge_type.value}] {item.title}: {item.content[:200]}\n"

            return output

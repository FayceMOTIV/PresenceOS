# PresenceOS — Firecrawl Scraper (Sprint 6)
# Scrape un site web → extrait le Business DNA via Claude Haiku
# Fallback httpx si pas de clé Firecrawl

from __future__ import annotations

import json
import logging
import re

import anthropic
import httpx

from app.core.config import settings
from app.models.business_dna import BusinessDNA

logger = logging.getLogger(__name__)

FIRECRAWL_URL = "https://api.firecrawl.dev/v1/scrape"


class FirecrawlScraper:
    """Scrape a website and extract Business DNA using Claude."""

    def __init__(self) -> None:
        self._claude: anthropic.Anthropic | None = None

    def _get_claude(self) -> anthropic.Anthropic:
        if self._claude is None:
            api_key = settings.anthropic_api_key
            if not api_key:
                raise RuntimeError("ANTHROPIC_API_KEY not configured")
            self._claude = anthropic.Anthropic(api_key=api_key)
        return self._claude

    async def scrape_url(self, url: str) -> str | None:
        """Scrape URL content. Tries Firecrawl first, falls back to httpx."""
        # Try Firecrawl if API key available
        if settings.firecrawl_api_key:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.post(
                        FIRECRAWL_URL,
                        headers={
                            "Authorization": f"Bearer {settings.firecrawl_api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "url": url,
                            "formats": ["markdown"],
                            "onlyMainContent": True,
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                    return data.get("data", {}).get("markdown", "")
            except Exception as exc:
                logger.warning("Firecrawl failed, using fallback", extra={"error": str(exc)})

        # Fallback: basic httpx scraping
        try:
            async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; PresenceOS/1.0)"},
                )
                response.raise_for_status()
                text = response.text
                text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
                text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
                text = re.sub(r"<[^>]+>", " ", text)
                text = re.sub(r"\s+", " ", text).strip()
                return text[:5000]
        except Exception as exc:
            logger.error("Fallback scraping failed", extra={"url": url, "error": str(exc)})
            return None

    async def extract_dna_from_content(self, content: str, url: str) -> BusinessDNA:
        """Use Claude Haiku to extract Business DNA from scraped content."""
        prompt = f"""Analyse ce contenu de site web et extrais les informations sur ce commerce.
URL : {url}

Contenu (extrait) :
{content[:3000]}

Extrais en JSON strict (sans markdown) :
{{
  "business_name": "<nom du commerce ou null>",
  "business_type": "<un parmi: restaurant|fast_food|boucherie|boulangerie|pizzeria|cafe|bar|traiteur|other>",
  "city": "<ville uniquement ou null>",
  "cuisine_style": "<type de cuisine en quelques mots ou null>",
  "target_audience": "<cible en 1 phrase ou null>",
  "tone_of_voice": "<un parmi: chaleureux|fun|premium|authentique|professionnel ou null>",
  "ambiance": "<ambiance du lieu en 1 phrase ou null>",
  "unique_selling_point": "<ce qui les distingue en 1 phrase ou null>"
}}

Si une info n'est pas claire, mets null. JSON uniquement."""

        try:
            claude = self._get_claude()
            response = claude.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            extracted = json.loads(raw)
            clean = {k: v for k, v in extracted.items() if v is not None and v != [] and v != ""}
            return BusinessDNA.from_dict(clean)
        except Exception as exc:
            logger.error("DNA extraction from content failed", extra={"error": str(exc)})
            return BusinessDNA()

    async def scrape_and_extract(self, url: str) -> dict:
        """Full pipeline: scrape URL → extract DNA → return result."""
        if not url.startswith("http"):
            url = f"https://{url}"

        content = await self.scrape_url(url)
        if not content:
            return {"dna": BusinessDNA().to_dict(), "success": False, "fields_found": 0}

        dna = await self.extract_dna_from_content(content, url)

        fields_found = sum(
            1
            for v in [dna.business_name, dna.city, dna.cuisine_style, dna.target_audience, dna.tone_of_voice]
            if v
        )

        return {
            "dna": dna.to_dict(),
            "success": fields_found >= 2,
            "fields_found": fields_found,
        }

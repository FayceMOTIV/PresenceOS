"""Outil CrewAI pour scraper des sites web avec Firecrawl."""
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from app.core.config import get_settings


class WebScraperInput(BaseModel):
    url: str = Field(description="URL a scraper")
    extract_schema: dict | None = Field(
        default=None,
        description="Schema JSON d'extraction structuree",
    )


class WebScraperTool(BaseTool):
    name: str = "web_scraper"
    description: str = (
        "Scrape une page web et retourne son contenu en Markdown structure. "
        "Peut extraire des donnees structurees avec un schema JSON. "
        "Ideal pour analyser les sites concurrents, blogs du secteur, pages d'actualite."
    )
    args_schema: type[BaseModel] = WebScraperInput

    def _run(self, url: str, extract_schema: dict | None = None) -> str:
        settings = get_settings()

        if settings.firecrawl_api_key:
            return self._firecrawl_scrape(url, extract_schema, settings.firecrawl_api_key)

        return self._fallback_scrape(url)

    def _firecrawl_scrape(
        self, url: str, extract_schema: dict | None, api_key: str
    ) -> str:
        try:
            from firecrawl import FirecrawlApp

            app = FirecrawlApp(api_key=api_key)
            formats = ["markdown"]
            params: dict = {"formats": formats}
            if extract_schema:
                formats.append("json")
                params["jsonOptions"] = {"schema": extract_schema}

            result = app.scrape_url(url, params=params)

            output = f"# Contenu de {url}\n\n"
            if hasattr(result, "markdown") and result.markdown:
                output += result.markdown[:5000]
            if hasattr(result, "json") and result.json:
                output += f"\n\n## Donnees extraites\n{result.json}"
            return output
        except Exception as e:
            return f"Erreur Firecrawl {url}: {e}"

    def _fallback_scrape(self, url: str) -> str:
        try:
            import httpx

            resp = httpx.get(url, timeout=15, follow_redirects=True)
            resp.raise_for_status()
            # Simple HTML to text extraction
            text = resp.text
            # Strip HTML tags (basic)
            import re

            text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.S)
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.S)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            return f"# Contenu de {url}\n\n{text[:5000]}"
        except Exception as e:
            return (
                f"Erreur fallback scraping {url}: {e}. "
                "Configure FIRECRAWL_API_KEY pour un scraping fiable."
            )

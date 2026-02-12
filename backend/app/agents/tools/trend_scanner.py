"""Outil CrewAI pour scanner les tendances d'un secteur."""
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from app.core.config import get_settings


class TrendScannerInput(BaseModel):
    industry: str = Field(
        description="Secteur d'activite (ex: restaurant, immobilier, fitness)"
    )
    platforms: list[str] = Field(
        default=["linkedin", "instagram"],
        description="Plateformes cibles",
    )
    location: str = Field(default="France", description="Zone geographique")


class TrendScannerTool(BaseTool):
    name: str = "trend_scanner"
    description: str = (
        "Scanne les tendances actuelles d'un secteur d'activite sur les reseaux sociaux. "
        "Retourne les sujets populaires, hashtags tendance, et formats de contenu qui performent. "
        "Utilise la recherche web pour trouver des donnees fraiches."
    )
    args_schema: type[BaseModel] = TrendScannerInput

    def _run(
        self,
        industry: str,
        platforms: list[str] | None = None,
        location: str = "France",
    ) -> str:
        platforms = platforms or ["linkedin", "instagram"]
        settings = get_settings()

        if settings.serper_api_key:
            return self._search_trends(
                industry, platforms, location, settings.serper_api_key
            )

        return self._generic_trends(industry, platforms)

    def _search_trends(
        self,
        industry: str,
        platforms: list[str],
        location: str,
        api_key: str,
    ) -> str:
        try:
            import httpx

            results = []
            for platform in platforms:
                query = f"{industry} {platform} content trends {location} 2025 2026"
                response = httpx.post(
                    "https://google.serper.dev/search",
                    headers={"X-API-KEY": api_key},
                    json={"q": query, "num": 5, "gl": "fr"},
                    timeout=10,
                )
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("organic", [])[:3]:
                        results.append(
                            f"- [{platform}] {item.get('title', '')}: "
                            f"{item.get('snippet', '')}"
                        )

            if results:
                return (
                    f"# Tendances {industry} ({location})\n\n"
                    + "\n".join(results)
                )
            return self._generic_trends(industry, platforms)
        except Exception as e:
            return f"Erreur recherche: {e}"

    def _generic_trends(self, industry: str, platforms: list[str]) -> str:
        return (
            f"# Tendances generiques pour {industry}\n\n"
            f"Plateformes ciblees: {', '.join(platforms)}\n\n"
            "## Formats qui performent en 2025-2026:\n"
            "- Videos courtes (Reels, TikTok) : taux d'engagement 3x superieur\n"
            "- Carrousels educatifs : fort taux de sauvegarde\n"
            "- Temoignages clients authentiques\n"
            "- Behind-the-scenes / coulisses\n"
            "- Stories interactives (sondages, quiz)\n"
            "- Posts texte longs sur LinkedIn (storytelling)\n\n"
            "## Hashtags tendance:\n"
            f"- #{industry.replace(' ', '')} #contentmarketing #socialmedia\n"
            "- #reels #trending #viral\n\n"
            "Configure SERPER_API_KEY pour des tendances en temps reel."
        )

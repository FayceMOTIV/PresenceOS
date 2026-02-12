"""Agent veilleur — scanne les tendances et le secteur."""
from crewai import Agent
from app.agents.config import get_crew_llm, get_crew_verbose
from app.agents.tools.web_scraper import WebScraperTool
from app.agents.tools.trend_scanner import TrendScannerTool
from app.agents.tools.brand_knowledge import BrandKnowledgeTool


def create_researcher_agent() -> Agent:
    return Agent(
        role="Veilleur Marketing Digital",
        goal=(
            "Identifier les tendances, sujets populaires et opportunites de contenu "
            "dans le secteur du client. Fournir des donnees concretes et actuelles."
        ),
        backstory=(
            "Tu es un expert en veille marketing avec 15 ans d'experience. "
            "Tu maitrises l'analyse de tendances sur les reseaux sociaux et tu sais "
            "identifier les sujets qui generent de l'engagement. Tu utilises des donnees "
            "reelles pour tes recommandations, jamais des suppositions."
        ),
        tools=[WebScraperTool(), TrendScannerTool(), BrandKnowledgeTool()],
        llm=get_crew_llm(),
        verbose=get_crew_verbose(),
        allow_delegation=False,
        max_iter=5,
    )

"""Taches d'analyse de tendances."""
from crewai import Task, Agent


def create_trend_analysis_task(
    agent: Agent,
    brand_id: str,
    industry: str,
    platforms: list[str],
) -> Task:
    return Task(
        description=(
            f"Analyse les tendances actuelles du secteur '{industry}' "
            f"pour les plateformes: {', '.join(platforms)}. "
            f"Utilise les outils de scan et de scraping pour des donnees fraiches. "
            f"Consulte la marque (brand_id: {brand_id}) pour contextualiser."
        ),
        expected_output=(
            "Rapport de tendances en JSON:\n"
            "```json\n"
            '{"trends": [\n'
            '  {"topic": "Sujet tendance",\n'
            '   "relevance_score": 8,\n'
            '   "platforms": ["instagram", "linkedin"],\n'
            '   "suggested_angle": "Angle pour la marque",\n'
            '   "hashtags": ["#trending"]}\n'
            "],\n"
            '"summary": "Resume des tendances"}\n'
            "```"
        ),
        agent=agent,
    )

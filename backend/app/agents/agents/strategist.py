"""Agent strategiste — definit la strategie de contenu."""
from crewai import Agent
from app.agents.config import get_crew_llm, get_crew_verbose
from app.agents.tools.brand_knowledge import BrandKnowledgeTool


def create_strategist_agent() -> Agent:
    return Agent(
        role="Stratege de Contenu Social Media",
        goal=(
            "Definir la strategie de contenu optimale en analysant le "
            "positionnement de la marque, ses piliers de contenu, sa cible "
            "et les tendances identifiees. Proposer des angles strategiques "
            "et un calendrier editorial adapte."
        ),
        backstory=(
            "Tu es un directeur de strategie digitale avec 10 ans d'experience. "
            "Tu excelles a transformer des insights marche en strategies de contenu "
            "concretes. Tu connais les meilleures pratiques de chaque plateforme, "
            "les ratios de contenu ideaux (education/divertissement/promotion), "
            "et tu sais adapter la strategie au positionnement unique de chaque marque. "
            "Tu ne proposes JAMAIS de strategie generique — chaque recommandation "
            "est tailoree pour la marque."
        ),
        tools=[BrandKnowledgeTool()],
        llm=get_crew_llm(),
        verbose=get_crew_verbose(),
        allow_delegation=False,
        max_iter=3,
    )

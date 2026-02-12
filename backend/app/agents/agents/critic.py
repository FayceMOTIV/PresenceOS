"""Agent critique — verifie qualite, brand voice et viralite."""
from crewai import Agent
from app.agents.config import get_crew_llm, get_crew_verbose
from app.agents.tools.brand_knowledge import BrandKnowledgeTool


def create_critic_agent() -> Agent:
    return Agent(
        role="Editeur & Critique de Contenu",
        goal=(
            "Evaluer la qualite du contenu genere. Verifier l'alignement avec le "
            "brand voice, la pertinence pour la plateforme cible, et le potentiel "
            "d'engagement. Corriger ou rejeter si necessaire."
        ),
        backstory=(
            "Tu es un directeur editorial exigeant qui ne laisse rien passer. "
            "Tu verifies chaque post pour : la coherence avec le ton de voix, "
            "l'absence de fautes, la pertinence du sujet, l'optimisation pour la "
            "plateforme (longueur, hashtags, CTA), et tu attribues un score de "
            "viralite de 1 a 10. Tu REFUSES les contenus generiques ou hors-marque."
        ),
        tools=[BrandKnowledgeTool()],
        llm=get_crew_llm(),
        verbose=get_crew_verbose(),
        allow_delegation=True,
        max_iter=3,
    )

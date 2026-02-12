"""Taches d'extraction pour l'onboarding."""
from crewai import Task, Agent


def create_brand_extraction_task(agent: Agent, website_url: str) -> Task:
    return Task(
        description=(
            f"Analyse le site web {website_url} en le scrapant. "
            "Extrais toutes les informations de branding possibles. "
            "Si le site n'est pas accessible, deduis ce que tu peux de l'URL."
        ),
        expected_output=(
            "Resultat en JSON strict:\n"
            "```json\n"
            '{"business_name": "Nom de l\'entreprise",\n'
            ' "description": "Description courte (2-3 phrases)",\n'
            ' "industry": "Secteur d\'activite",\n'
            ' "products": ["Produit/service 1", "Produit/service 2"],\n'
            ' "target_audience": "Description de l\'audience cible",\n'
            ' "tone_of_voice": "Description du ton (ex: professionnel, chaleureux)",\n'
            ' "colors": {"primary": "#hex", "secondary": "#hex"},\n'
            ' "tagline": "Slogan si trouve"}\n'
            "```"
        ),
        agent=agent,
    )

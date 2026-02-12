"""Taches de generation de contenu pour le Content Crew."""
from crewai import Task, Agent


def create_research_task(
    agent: Agent,
    brand_id: str,
    platforms: list[str],
    topic: str | None,
    industry: str | None,
) -> Task:
    return Task(
        description=(
            f"Analyse la marque (brand_id: {brand_id}) via l'outil brand_knowledge. "
            f"Identifie les tendances du secteur '{industry or 'non specifie'}' "
            f"pour les plateformes: {', '.join(platforms)}. "
            f"{'Concentre-toi sur le sujet: ' + topic if topic else 'Trouve les 3 meilleurs sujets du moment.'} "
            f"Fournis des idees concretes avec des angles originaux."
        ),
        expected_output=(
            "Un rapport structure avec:\n"
            "1. Resume de la marque et son positionnement\n"
            "2. 3-5 sujets tendance pertinents pour cette marque\n"
            "3. Pour chaque sujet: angle recommande, hashtags suggeres, format ideal"
        ),
        agent=agent,
    )


def create_strategy_task(
    agent: Agent,
    brand_id: str,
    platforms: list[str],
    num_posts: int,
    tone: str | None,
    research_task: Task,
) -> Task:
    tone_instruction = f"Le ton souhaite est: {tone}. " if tone else ""
    return Task(
        description=(
            f"En te basant sur la recherche, definis la strategie de contenu pour "
            f"la marque (brand_id: {brand_id}). Consulte le brand_knowledge pour les "
            f"piliers de contenu et la cible. {tone_instruction}"
            f"Plateformes cibles: {', '.join(platforms)}. "
            f"Nombre de posts a produire: {num_posts}. "
            "Pour chaque post, definis: le sujet precis, l'angle, le format, "
            "le CTA, et les hashtags strategiques. Assure la diversite des piliers."
        ),
        expected_output=(
            f"Un plan editorial detaille avec {num_posts} briefs:\n"
            "```json\n"
            "[\n"
            '  {"platform": "linkedin|instagram|tiktok",\n'
            '   "topic": "Sujet precis",\n'
            '   "angle": "Angle editorial unique",\n'
            '   "content_pillar": "education|entertainment|engagement|promotion|behind_scenes",\n'
            '   "tone_direction": "Instructions de ton specifiques",\n'
            '   "cta": "Call to action suggere",\n'
            '   "hashtag_strategy": ["#hash1", "#hash2"]}\n'
            "]\n"
            "```"
        ),
        agent=agent,
        context=[research_task],
    )


def create_writing_task(
    agent: Agent,
    brand_id: str,
    platforms: list[str],
    num_posts: int,
    context_tasks: list[Task],
) -> Task:
    return Task(
        description=(
            f"En te basant sur la recherche et la strategie, redige {num_posts} posts pour la marque "
            f"(brand_id: {brand_id}). Consulte le brand_knowledge pour le ton de voix. "
            f"Plateformes cibles: {', '.join(platforms)}. "
            "Chaque post doit etre adapte a sa plateforme specifique. "
            "Inclus les hashtags, emojis (si approprie), et un CTA."
        ),
        expected_output=(
            f"Exactement {num_posts} posts formates en JSON:\n"
            "```json\n"
            "[\n"
            '  {"platform": "linkedin|instagram|facebook|tiktok",\n'
            '   "content": "Le texte complet du post",\n'
            '   "hashtags": ["#hash1", "#hash2"],\n'
            '   "suggested_media": "Description du visuel suggere",\n'
            '   "cta": "Call to action",\n'
            '   "topic": "Sujet principal"}\n'
            "]\n"
            "```"
        ),
        agent=agent,
        context=context_tasks,
    )


def create_review_task(
    agent: Agent,
    brand_id: str,
    research_task: Task,
    writing_task: Task,
) -> Task:
    return Task(
        description=(
            f"Evalue chaque post genere pour la marque (brand_id: {brand_id}). "
            "Verifie via brand_knowledge que le ton correspond au brand voice. "
            "Pour chaque post, attribue un score de 1-10 et corrige si < 7. "
            "Rejette et reecris les posts generiques ou hors-marque."
        ),
        expected_output=(
            "Posts finaux valides en JSON:\n"
            "```json\n"
            '{"posts": [\n'
            '  {"platform": "...",\n'
            '   "content": "Texte final (corrige si necessaire)",\n'
            '   "hashtags": ["..."],\n'
            '   "suggested_media": "...",\n'
            '   "cta": "...",\n'
            '   "topic": "...",\n'
            '   "virality_score": 8,\n'
            '   "brand_voice_score": 9,\n'
            '   "review_notes": "Bon alignement avec le ton de la marque"}\n'
            '],\n'
            '"metadata": {\n'
            '  "total_generated": 3,\n'
            '  "approved": 3,\n'
            '  "rejected": 0,\n'
            '  "avg_virality": 7.5}}\n'
            "```"
        ),
        agent=agent,
        context=[research_task, writing_task],
    )

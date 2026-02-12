"""Crew principal de generation de contenu — 4 agents."""
import json
import re

from crewai import Crew, Process
from app.agents.agents.researcher import create_researcher_agent
from app.agents.agents.strategist import create_strategist_agent
from app.agents.agents.writer import create_writer_agent
from app.agents.agents.critic import create_critic_agent
from app.agents.config import get_crew_verbose, get_crew_max_rpm
from app.agents.tasks.content_tasks import (
    create_research_task,
    create_strategy_task,
    create_writing_task,
    create_review_task,
)


def run_content_crew(
    brand_id: str,
    platforms: list[str],
    num_posts: int = 3,
    topic: str | None = None,
    industry: str | None = None,
    tone: str | None = None,
) -> dict:
    """
    Lance le Crew de generation de contenu (4 agents).

    Pipeline: researcher -> strategist -> writer -> critic

    Returns:
        dict avec cles: posts (list), metadata (dict)
    """
    researcher = create_researcher_agent()
    strategist = create_strategist_agent()
    writer = create_writer_agent()
    critic = create_critic_agent()

    research_task = create_research_task(
        researcher, brand_id, platforms, topic, industry
    )
    strategy_task = create_strategy_task(
        strategist, brand_id, platforms, num_posts, tone, research_task
    )
    writing_task = create_writing_task(
        writer, brand_id, platforms, num_posts, [research_task, strategy_task]
    )
    review_task = create_review_task(
        critic, brand_id, research_task, writing_task
    )

    crew = Crew(
        agents=[researcher, strategist, writer, critic],
        tasks=[research_task, strategy_task, writing_task, review_task],
        process=Process.sequential,
        verbose=get_crew_verbose(),
        max_rpm=get_crew_max_rpm(),
    )

    result = crew.kickoff()

    # Parser le resultat JSON
    raw = str(result)
    json_match = re.search(r'\{[\s\S]*"posts"[\s\S]*\}', raw)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    return {
        "posts": [],
        "metadata": {
            "raw_output": raw[:2000],
            "error": "Impossible de parser le JSON",
        },
    }

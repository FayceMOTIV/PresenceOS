"""Crew veille — scan des tendances sectorielles."""
import json
import re

from crewai import Crew, Process
from app.agents.agents.researcher import create_researcher_agent
from app.agents.config import get_crew_verbose, get_crew_max_rpm
from app.agents.tasks.trend_tasks import create_trend_analysis_task


def run_trends_crew(
    brand_id: str,
    industry: str,
    platforms: list[str] | None = None,
) -> dict:
    """
    Lance le Crew de veille tendances.

    Returns:
        dict avec cles: trends (list), summary (str)
    """
    platforms = platforms or ["instagram", "linkedin"]
    researcher = create_researcher_agent()

    trend_task = create_trend_analysis_task(
        researcher, brand_id, industry, platforms
    )

    crew = Crew(
        agents=[researcher],
        tasks=[trend_task],
        process=Process.sequential,
        verbose=get_crew_verbose(),
        max_rpm=get_crew_max_rpm(),
    )

    result = crew.kickoff()

    raw = str(result)
    json_match = re.search(r'\{[\s\S]*"trends"[\s\S]*\}', raw)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    return {
        "trends": [],
        "summary": raw[:1000],
    }

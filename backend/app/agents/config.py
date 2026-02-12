"""Configuration centralisee pour les agents CrewAI."""
from crewai import LLM
from app.core.config import get_settings


def get_crew_llm(model: str | None = None) -> LLM:
    """Retourne le LLM configure pour les agents."""
    s = get_settings()
    model_name = model or s.crew_default_llm

    if model_name.startswith("claude"):
        return LLM(
            model=f"anthropic/{model_name}",
            api_key=s.anthropic_api_key,
            max_tokens=4096,
        )
    return LLM(
        model=f"openai/{model_name}",
        api_key=s.openai_api_key,
        max_tokens=4096,
    )


def get_crew_verbose() -> bool:
    return get_settings().crew_verbose


def get_crew_max_rpm() -> int:
    return get_settings().crew_max_rpm

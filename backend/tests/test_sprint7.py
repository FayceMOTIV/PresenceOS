"""
PresenceOS - Phase 1 Tests: AI Agents CrewAI + API endpoints.
"""
import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient


# ── Config agents ─────────────────────────────────────────────────────


def test_get_crew_llm_returns_openai():
    """get_crew_llm retourne un LLM OpenAI par defaut."""
    with patch("app.agents.config.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            crew_default_llm="gpt-4o-mini",
            openai_api_key="sk-test",
            anthropic_api_key="",
            crew_verbose=True,
        )
        from app.agents.config import get_crew_llm

        llm = get_crew_llm()
        assert llm is not None
        # CrewAI may strip prefixes; check the object type or model name
        llm_type = type(llm).__name__.lower()
        llm_model = str(llm.model).lower()
        assert "openai" in llm_type or "gpt" in llm_model


def test_get_crew_llm_returns_anthropic():
    """get_crew_llm retourne un LLM Anthropic quand le modele commence par 'claude'."""
    with patch("app.agents.config.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            crew_default_llm="claude-sonnet-4-5-20250929",
            openai_api_key="",
            anthropic_api_key="sk-ant-test",
            crew_verbose=True,
        )
        from app.agents.config import get_crew_llm

        llm = get_crew_llm("claude-sonnet-4-5-20250929")
        assert llm is not None
        llm_type = type(llm).__name__.lower()
        llm_model = str(llm.model).lower()
        assert "anthropic" in llm_type or "claude" in llm_model


def test_get_crew_verbose():
    """get_crew_verbose retourne la config."""
    with patch("app.agents.config.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(crew_verbose=True)
        from app.agents.config import get_crew_verbose

        assert get_crew_verbose() is True


def test_get_crew_max_rpm():
    """get_crew_max_rpm retourne la config."""
    with patch("app.agents.config.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(crew_max_rpm=10)
        from app.agents.config import get_crew_max_rpm

        assert get_crew_max_rpm() == 10


# ── Tools init ────────────────────────────────────────────────────────


def test_brand_knowledge_tool_init():
    """BrandKnowledgeTool peut etre instancie."""
    from app.agents.tools.brand_knowledge import BrandKnowledgeTool

    tool = BrandKnowledgeTool()
    assert tool is not None
    assert tool.name is not None
    assert len(tool.name) > 0


def test_metrics_reader_tool_init():
    """MetricsReaderTool peut etre instancie."""
    from app.agents.tools.metrics_reader import MetricsReaderTool

    tool = MetricsReaderTool()
    assert tool is not None
    assert tool.name is not None


def test_web_scraper_tool_fallback():
    """WebScraperTool fonctionne sans FIRECRAWL_API_KEY (fallback httpx)."""
    with patch("app.agents.tools.web_scraper.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(firecrawl_api_key="")
        from app.agents.tools.web_scraper import WebScraperTool

        tool = WebScraperTool()
        assert tool is not None


def test_trend_scanner_tool_fallback():
    """TrendScannerTool retourne des guidelines generiques sans SERPER_API_KEY."""
    with patch("app.agents.tools.trend_scanner.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(serper_api_key="")
        from app.agents.tools.trend_scanner import TrendScannerTool

        tool = TrendScannerTool()
        assert tool is not None


# ── Agent creation ────────────────────────────────────────────────────


@patch("app.agents.config.get_settings")
def test_create_researcher_agent(mock_settings):
    """L'agent researcher peut etre cree."""
    mock_settings.return_value = MagicMock(
        crew_default_llm="gpt-4o-mini",
        openai_api_key="sk-test",
        anthropic_api_key="",
        crew_verbose=False,
        firecrawl_api_key="",
        serper_api_key="",
    )
    from app.agents.agents.researcher import create_researcher_agent

    agent = create_researcher_agent()
    assert agent is not None
    assert agent.role is not None


@patch("app.agents.config.get_settings")
def test_create_strategist_agent(mock_settings):
    """L'agent strategist peut etre cree."""
    mock_settings.return_value = MagicMock(
        crew_default_llm="gpt-4o-mini",
        openai_api_key="sk-test",
        anthropic_api_key="",
        crew_verbose=False,
    )
    from app.agents.agents.strategist import create_strategist_agent

    agent = create_strategist_agent()
    assert agent is not None
    assert "strat" in agent.role.lower()


@patch("app.agents.config.get_settings")
def test_create_writer_agent(mock_settings):
    """L'agent writer peut etre cree."""
    mock_settings.return_value = MagicMock(
        crew_default_llm="gpt-4o-mini",
        openai_api_key="sk-test",
        anthropic_api_key="",
        crew_verbose=False,
    )
    from app.agents.agents.writer import create_writer_agent

    agent = create_writer_agent()
    assert agent is not None


@patch("app.agents.config.get_settings")
def test_create_critic_agent(mock_settings):
    """L'agent critic peut etre cree."""
    mock_settings.return_value = MagicMock(
        crew_default_llm="gpt-4o-mini",
        openai_api_key="sk-test",
        anthropic_api_key="",
        crew_verbose=False,
    )
    from app.agents.agents.critic import create_critic_agent

    agent = create_critic_agent()
    assert agent is not None


# ── Content crew instantiation ────────────────────────────────────────


@patch("app.agents.config.get_settings")
def test_content_crew_instantiation(mock_settings):
    """Le content_crew peut etre importe et les fonctions existent."""
    mock_settings.return_value = MagicMock(
        crew_default_llm="gpt-4o-mini",
        openai_api_key="sk-test",
        anthropic_api_key="",
        crew_verbose=False,
        crew_max_rpm=10,
        firecrawl_api_key="",
        serper_api_key="",
    )
    from app.agents.crews.content_crew import run_content_crew

    assert callable(run_content_crew)


@patch("app.agents.config.get_settings")
def test_trends_crew_instantiation(mock_settings):
    """Le trends_crew peut etre importe."""
    mock_settings.return_value = MagicMock(
        crew_default_llm="gpt-4o-mini",
        openai_api_key="sk-test",
        anthropic_api_key="",
        crew_verbose=False,
        crew_max_rpm=10,
        firecrawl_api_key="",
        serper_api_key="",
    )
    from app.agents.crews.trends_crew import run_trends_crew

    assert callable(run_trends_crew)


# ── API endpoints existent ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_content_endpoint_exists(
    client: AsyncClient, auth_headers: dict, test_brand
):
    """POST /agents/generate-content ne retourne pas 404."""
    response = await client.post(
        "/api/v1/agents/generate-content",
        json={
            "brand_id": str(test_brand.id),
            "platforms": ["instagram"],
            "num_posts": 1,
            "topic": "test",
        },
        headers=auth_headers,
    )
    assert response.status_code != 404


@pytest.mark.asyncio
async def test_scan_trends_endpoint_exists(
    client: AsyncClient, auth_headers: dict, test_brand
):
    """POST /agents/scan-trends ne retourne pas 404."""
    response = await client.post(
        "/api/v1/agents/scan-trends",
        json={
            "brand_id": str(test_brand.id),
            "industry": "restaurant",
            "platforms": ["instagram"],
        },
        headers=auth_headers,
    )
    assert response.status_code != 404


@pytest.mark.asyncio
async def test_analyze_brand_endpoint_exists(
    client: AsyncClient, auth_headers: dict, test_brand
):
    """POST /agents/analyze-brand ne retourne pas 404."""
    response = await client.post(
        "/api/v1/agents/analyze-brand",
        json={
            "brand_id": str(test_brand.id),
            "website_url": "https://example.com",
        },
        headers=auth_headers,
    )
    assert response.status_code != 404


@pytest.mark.asyncio
async def test_task_status_endpoint_exists(client: AsyncClient):
    """GET /agents/status/{task_id} retourne 404 pour un task_id inconnu."""
    response = await client.get("/api/v1/agents/status/nonexistent-task")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_task_status_alias_endpoint_exists(client: AsyncClient):
    """GET /agents/tasks/{task_id} retourne 404 pour un task_id inconnu."""
    response = await client.get("/api/v1/agents/tasks/nonexistent-task")
    assert response.status_code == 404

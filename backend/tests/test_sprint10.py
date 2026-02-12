"""
PresenceOS - Phase 6 Tests: Remotion Templates + Polish + Production.
"""
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient


# ── RemotionRenderer tests ──────────────────────────────────────────────


def test_remotion_renderer_init():
    """RemotionRenderer peut etre instancie."""
    from app.services.remotion_renderer import RemotionRenderer

    renderer = RemotionRenderer()
    assert renderer is not None
    assert renderer.engine_path is not None


def test_remotion_renderer_templates_list():
    """RemotionRenderer a les 3 templates."""
    from app.services.remotion_renderer import RemotionRenderer

    renderer = RemotionRenderer()
    templates = renderer.available_templates

    assert "restaurant_showcase" in templates
    assert "promo_flash" in templates
    assert "daily_story" in templates
    assert len(templates) == 3


def test_remotion_renderer_template_info():
    """Chaque template a composition_id, fps, dimensions."""
    from app.services.remotion_renderer import RemotionRenderer

    renderer = RemotionRenderer()

    for name in renderer.available_templates:
        info = renderer.get_template_info(name)
        assert info is not None
        assert "composition_id" in info
        assert "fps" in info
        assert "width" in info
        assert "height" in info
        assert info["width"] == 1080
        assert info["height"] == 1920
        assert info["fps"] == 30


def test_remotion_renderer_unknown_template():
    """get_template_info retourne None pour template inconnu."""
    from app.services.remotion_renderer import RemotionRenderer

    renderer = RemotionRenderer()
    assert renderer.get_template_info("nonexistent") is None


def test_remotion_renderer_template_composition_ids():
    """Les composition IDs correspondent aux composants Remotion."""
    from app.services.remotion_renderer import RemotionRenderer

    renderer = RemotionRenderer()
    expected = {
        "restaurant_showcase": "RestaurantShowcase",
        "promo_flash": "PromoFlash",
        "daily_story": "DailyStory",
    }
    for name, comp_id in expected.items():
        info = renderer.get_template_info(name)
        assert info["composition_id"] == comp_id


@pytest.mark.asyncio
async def test_remotion_render_unknown_template():
    """render() retourne None pour un template inconnu."""
    from app.services.remotion_renderer import RemotionRenderer

    renderer = RemotionRenderer()
    result = await renderer.render("nonexistent", {}, "brand-123")
    assert result is None


# ── PublisherService tests ──────────────────────────────────────────────


def test_publisher_service_init():
    """PublisherService peut etre instancie."""
    from app.services.publisher import PublisherService

    mock_db = MagicMock()
    publisher = PublisherService(db=mock_db)
    assert publisher is not None
    assert publisher.db is mock_db
    assert publisher.whatsapp is not None


@pytest.mark.asyncio
async def test_publisher_publish_post_not_found():
    """publish_post retourne erreur quand le post n'existe pas."""
    from app.services.publisher import PublisherService
    import uuid

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    publisher = PublisherService(db=mock_db)
    result = await publisher.publish_post(uuid.uuid4())

    assert result["success"] is False
    assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_publisher_notify_no_phone():
    """notify_result ne fait rien sans numero de telephone."""
    from app.services.publisher import PublisherService
    import uuid

    mock_db = MagicMock()
    publisher = PublisherService(db=mock_db)

    # Should not raise
    await publisher.notify_result(uuid.uuid4(), phone=None, success=True)


@pytest.mark.asyncio
async def test_publisher_retry_not_found():
    """retry_failed retourne erreur pour post inexistant."""
    from app.services.publisher import PublisherService
    import uuid

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    publisher = PublisherService(db=mock_db)
    result = await publisher.retry_failed(uuid.uuid4())

    assert result["success"] is False
    assert "not found" in result["error"]


# ── Dashboard Metrics API tests ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_dashboard_metrics_endpoint(
    client: AsyncClient, auth_headers: dict, test_brand
):
    """GET /metrics/brands/{id}/dashboard retourne 200."""
    response = await client.get(
        f"/api/v1/metrics/brands/{test_brand.id}/dashboard",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_posts_published" in data
    assert "total_posts_scheduled" in data
    assert "total_impressions" in data
    assert "total_engagement" in data
    assert "average_engagement_rate" in data
    assert "ai_insight" in data


@pytest.mark.asyncio
async def test_platform_breakdown_endpoint(
    client: AsyncClient, auth_headers: dict, test_brand
):
    """GET /metrics/brands/{id}/platforms retourne 200."""
    response = await client.get(
        f"/api/v1/metrics/brands/{test_brand.id}/platforms",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_top_posts_endpoint(
    client: AsyncClient, auth_headers: dict, test_brand
):
    """GET /metrics/brands/{id}/top-posts retourne 200."""
    response = await client.get(
        f"/api/v1/metrics/brands/{test_brand.id}/top-posts",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "posts" in data


@pytest.mark.asyncio
async def test_learning_insights_endpoint(
    client: AsyncClient, auth_headers: dict, test_brand
):
    """GET /metrics/brands/{id}/learning retourne 200."""
    response = await client.get(
        f"/api/v1/metrics/brands/{test_brand.id}/learning",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "what_works" in data
    assert "recommendations" in data
    assert "content_mix_suggestion" in data


@pytest.mark.asyncio
async def test_post_metrics_404(client: AsyncClient, auth_headers: dict):
    """GET /metrics/posts/{id} retourne 404 pour post inconnu."""
    import uuid

    response = await client.get(
        f"/api/v1/metrics/posts/{uuid.uuid4()}",
        headers=auth_headers,
    )
    assert response.status_code == 404


# ── Video Engine project files ──────────────────────────────────────────


def test_video_engine_package_json_exists():
    """video-engine/package.json existe."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    path = os.path.join(root, "video-engine", "package.json")
    assert os.path.exists(path), f"package.json not found at {path}"


def test_video_engine_root_tsx_exists():
    """video-engine/src/Root.tsx existe."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    path = os.path.join(root, "video-engine", "src", "Root.tsx")
    assert os.path.exists(path), f"Root.tsx not found at {path}"


def test_video_engine_templates_exist():
    """Les 3 templates Remotion existent."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    templates_dir = os.path.join(root, "video-engine", "src", "templates")

    for template in ["RestaurantShowcase.tsx", "PromoFlash.tsx", "DailyStory.tsx"]:
        path = os.path.join(templates_dir, template)
        assert os.path.exists(path), f"Template {template} not found"


def test_video_engine_components_exist():
    """Les composants Remotion existent."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    components_dir = os.path.join(root, "video-engine", "src", "components")

    for component in ["AnimatedText.tsx", "BackgroundMedia.tsx", "ProgressBar.tsx"]:
        path = os.path.join(components_dir, component)
        assert os.path.exists(path), f"Component {component} not found"


# ── Deploy scripts ──────────────────────────────────────────────────────


def test_deploy_script_exists():
    """deploy/deploy.sh existe et est executable."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    path = os.path.join(root, "deploy", "deploy.sh")
    assert os.path.exists(path), "deploy.sh not found"
    assert os.access(path, os.X_OK), "deploy.sh is not executable"


def test_systemd_services_exist():
    """Les fichiers systemd existent."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    systemd_dir = os.path.join(root, "deploy", "systemd")

    for service in [
        "presenceos-api.service",
        "presenceos-worker.service",
        "presenceos-beat.service",
        "presenceos-frontend.service",
    ]:
        path = os.path.join(systemd_dir, service)
        assert os.path.exists(path), f"Service file {service} not found"


def test_nginx_config_exists():
    """deploy/nginx.conf existe."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    path = os.path.join(root, "deploy", "nginx.conf")
    assert os.path.exists(path), "nginx.conf not found"


def test_env_production_example_exists():
    """deploy/.env.production.example existe."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    path = os.path.join(root, "deploy", ".env.production.example")
    assert os.path.exists(path), ".env.production.example not found"


# ── Integration: all services importable ────────────────────────────────


def test_all_services_importable():
    """Tous les services backend sont importables."""
    from app.services.remotion_renderer import RemotionRenderer
    from app.services.publisher import PublisherService
    from app.services.video_producer import VideoProducer
    from app.services.vision import VisionService
    from app.services.transcription import TranscriptionService
    from app.services.instruction_parser import InstructionParser
    from app.services.conversation_engine import ConversationEngine
    from app.services.ffmpeg_processor import FFmpegProcessor
    from app.services.tts import TTSService
    from app.services.music_library import MusicLibrary
    from app.services.pexels import PexelsService
    from app.services.whatsapp import WhatsAppService
    from app.services.storage import get_storage_service

    assert RemotionRenderer is not None
    assert PublisherService is not None
    assert VideoProducer is not None
    assert VisionService is not None
    assert TranscriptionService is not None
    assert InstructionParser is not None


def test_all_models_importable():
    """Tous les models sont importables."""
    from app.models.publishing import (
        ScheduledPost,
        SocialConnector,
        MetricsSnapshot,
        PostStatus,
        SocialPlatform,
    )
    from app.models.autopilot import (
        AutopilotConfig,
        PendingPost,
        PendingPostStatus,
    )
    from app.models.media import (
        MediaAsset,
        VoiceNote,
        MediaSource,
        MediaType,
    )

    assert ScheduledPost is not None
    assert AutopilotConfig is not None
    assert MediaAsset is not None


def test_all_connectors_importable():
    """Tous les connecteurs sont importables."""
    from app.connectors.factory import get_connector_handler
    from app.connectors.upload_post import UploadPostConnector
    from app.connectors.linkedin import LinkedInConnector

    assert get_connector_handler is not None
    assert UploadPostConnector is not None
    assert LinkedInConnector is not None


# ── Docker Compose validation ────────────────────────────────────────────


def test_docker_compose_exists():
    """docker-compose.yml existe."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    path = os.path.join(root, "docker-compose.yml")
    assert os.path.exists(path), "docker-compose.yml not found"


def test_docker_compose_has_all_services():
    """docker-compose.yml definit les 6 services."""
    import yaml

    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    path = os.path.join(root, "docker-compose.yml")

    with open(path) as f:
        compose = yaml.safe_load(f)

    services = compose.get("services", {})
    expected = ["postgres", "redis", "minio", "backend", "celery-worker", "celery-beat", "frontend"]

    for svc in expected:
        assert svc in services, f"Service {svc} missing from docker-compose.yml"

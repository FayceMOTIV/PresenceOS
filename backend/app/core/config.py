"""
PresenceOS - Core Configuration
"""
from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "PresenceOS"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    secret_key: str
    api_v1_prefix: str = "/api/v1"
    frontend_url: str = "http://localhost:3001"

    # Database
    database_url: str
    database_url_sync: str | None = None

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Storage (S3/MinIO)
    s3_endpoint_url: str | None = None
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket_name: str = "presenceos-media"
    s3_region: str = "us-east-1"
    s3_public_url: str | None = None

    # AI Providers
    openai_api_key: str | None = None
    openai_model: str = "gpt-4-turbo-preview"
    openai_embedding_model: str = "text-embedding-3-small"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-5-20250929"
    ai_provider: Literal["openai", "anthropic"] = "openai"
    openrouter_api_key: str = ""

    # OAuth - Meta
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_redirect_uri: str = ""
    meta_graph_version: str = "v19.0"

    # OAuth - TikTok
    tiktok_client_key: str = ""
    tiktok_client_secret: str = ""
    tiktok_redirect_uri: str = ""

    # Upload-Post API (Instagram, Facebook, TikTok)
    upload_post_api_key: str = ""

    # OAuth - LinkedIn
    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_redirect_uri: str = ""

    # Encryption
    token_encryption_key: str = ""

    # AI Agents
    firecrawl_api_key: str = ""
    composio_api_key: str = ""
    serper_api_key: str = ""
    crew_default_llm: str = "gpt-4o-mini"
    crew_max_rpm: int = 10
    crew_verbose: bool = True

    # WhatsApp Cloud API
    whatsapp_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_business_account_id: str = ""
    whatsapp_verify_token: str = "presenceos-webhook-verify"
    whatsapp_api_version: str = "v21.0"
    whatsapp_webhook_secret: str = ""

    # Telegram Bot API
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""

    # Video Pipeline (Sprint 9C)
    pexels_api_key: str = ""
    openai_tts_voice: str = "nova"  # alloy, echo, fable, onyx, nova, shimmer
    openai_tts_model: str = "tts-1"
    music_library_path: str = "/data/music"
    ffmpeg_path: str = "ffmpeg"
    video_output_path: str = "/tmp/presenceos_videos"
    video_max_duration: int = 60  # seconds

    # Conversation Engine (Sprint 9C)
    conversation_ttl_seconds: int = 1800  # 30 min conversation timeout

    # Observability
    sentry_dsn: str | None = None
    log_level: str = "INFO"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

"""
PresenceOS - Connector Factory

Routing:
  - linkedin → LinkedInConnector (native OAuth)
  - instagram, facebook, tiktok → UploadPostConnector (Upload-Post API)
"""
from app.connectors.base import BaseConnector
from app.connectors.upload_post import UploadPostConnector
from app.connectors.linkedin import LinkedInConnector
from app.models.publishing import SocialPlatform


def get_connector_handler(platform: SocialPlatform) -> BaseConnector:
    """Get the appropriate connector handler for a platform."""

    # LinkedIn → native OAuth connector
    if platform == SocialPlatform.LINKEDIN:
        return LinkedInConnector()

    # Instagram, Facebook, TikTok → Upload-Post API
    if platform in (
        SocialPlatform.INSTAGRAM,
        SocialPlatform.FACEBOOK,
        SocialPlatform.TIKTOK,
    ):
        return UploadPostConnector(platform=platform.value)

    raise ValueError(f"Unsupported platform: {platform}")

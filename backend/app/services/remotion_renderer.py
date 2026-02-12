"""
PresenceOS - Remotion Renderer Service (Sprint 10)

Renders videos using the Remotion video-engine project.
Supports three templates: RestaurantShowcase, PromoFlash, DailyStory.

In production, this calls the Remotion CLI via subprocess.
Videos are rendered server-side and uploaded to S3.
"""
import json
import os
import uuid
import subprocess
import tempfile
import structlog

from app.core.config import settings
from app.services.storage import get_storage_service

logger = structlog.get_logger()

# Path to video-engine project (relative to monorepo root)
VIDEO_ENGINE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "video-engine",
)

TEMPLATES = {
    "restaurant_showcase": {
        "composition_id": "RestaurantShowcase",
        "default_duration": 300,
        "fps": 30,
        "width": 1080,
        "height": 1920,
    },
    "promo_flash": {
        "composition_id": "PromoFlash",
        "default_duration": 240,
        "fps": 30,
        "width": 1080,
        "height": 1920,
    },
    "daily_story": {
        "composition_id": "DailyStory",
        "default_duration": 270,
        "fps": 30,
        "width": 1080,
        "height": 1920,
    },
}


class RemotionRenderer:
    """
    Render Remotion compositions to MP4 videos.

    Uses the Remotion CLI to render compositions with custom props,
    then uploads the result to S3/MinIO.
    """

    def __init__(self):
        self.engine_path = VIDEO_ENGINE_PATH
        self.templates = TEMPLATES

    @property
    def available_templates(self) -> list[str]:
        """List available template names."""
        return list(self.templates.keys())

    def get_template_info(self, template_name: str) -> dict | None:
        """Get metadata for a template."""
        return self.templates.get(template_name)

    async def render(
        self,
        template_name: str,
        props: dict,
        brand_id: str,
        duration_frames: int | None = None,
        output_format: str = "mp4",
    ) -> dict | None:
        """
        Render a video using a Remotion template.

        Args:
            template_name: Template key (restaurant_showcase, promo_flash, daily_story)
            props: Template-specific props dict
            brand_id: Brand UUID for S3 storage key
            duration_frames: Override default duration in frames
            output_format: Output format (mp4, webm)

        Returns:
            {"url": str, "key": str, "size": int, "duration_seconds": float} or None
        """
        template = self.templates.get(template_name)
        if not template:
            logger.error("Unknown template", template_name=template_name)
            return None

        composition_id = template["composition_id"]
        duration = duration_frames or template["default_duration"]
        fps = template["fps"]

        output_path = os.path.join(
            tempfile.gettempdir(),
            f"remotion_{uuid.uuid4().hex[:8]}.{output_format}",
        )

        props_path = os.path.join(
            tempfile.gettempdir(),
            f"remotion_props_{uuid.uuid4().hex[:8]}.json",
        )

        try:
            # Write props to temp file
            with open(props_path, "w") as f:
                json.dump(props, f)

            # Build Remotion CLI command
            cmd = [
                "npx",
                "remotion",
                "render",
                os.path.join(self.engine_path, "src", "Root.tsx"),
                composition_id,
                output_path,
                "--props",
                props_path,
                "--codec",
                "h264" if output_format == "mp4" else "vp8",
            ]

            logger.info(
                "Rendering video",
                template=template_name,
                composition=composition_id,
                duration_frames=duration,
            )

            # Execute render
            result = subprocess.run(
                cmd,
                cwd=self.engine_path,
                capture_output=True,
                text=True,
                timeout=300,  # 5 min timeout
            )

            if result.returncode != 0:
                logger.error(
                    "Remotion render failed",
                    stderr=result.stderr[:500],
                    returncode=result.returncode,
                )
                return None

            if not os.path.exists(output_path):
                logger.error("Render output file not found", path=output_path)
                return None

            # Upload to S3
            file_size = os.path.getsize(output_path)
            with open(output_path, "rb") as f:
                video_bytes = f.read()

            storage = get_storage_service()
            key = storage.generate_key(
                brand_id, "video", f"remotion_{uuid.uuid4().hex[:8]}.{output_format}"
            )
            upload_result = await storage.upload_bytes(
                video_bytes,
                key,
                content_type=f"video/{output_format}",
            )

            duration_seconds = duration / fps

            logger.info(
                "Video rendered and uploaded",
                template=template_name,
                size=file_size,
                duration_seconds=duration_seconds,
                key=upload_result["key"],
            )

            return {
                "url": upload_result["url"],
                "key": upload_result["key"],
                "size": file_size,
                "duration_seconds": duration_seconds,
                "template": template_name,
                "composition_id": composition_id,
            }

        except subprocess.TimeoutExpired:
            logger.error("Remotion render timed out", template=template_name)
            return None
        except Exception as e:
            logger.error(
                "Remotion render error", template=template_name, error=str(e)
            )
            return None
        finally:
            # Cleanup temp files
            for path in [output_path, props_path]:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except OSError:
                    pass

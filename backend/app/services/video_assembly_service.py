"""
Video Assembly Service RS3 — Download clips -> FFmpeg concat -> S3 upload.

Leverages existing FFmpegProcessor for concat and StorageService for S3.
Rule: always 3 clips x 5s, never 1 clip of 15s (65% cost savings).
"""

import os
import tempfile
import uuid
from datetime import datetime, timezone

import httpx
import structlog

from app.core.config import settings
from app.core.observability import capture_exception
from app.core.timeouts import get_http_timeout
from app.services.ffmpeg_processor import FFmpegProcessor
from app.services.storage import get_storage_service

logger = structlog.get_logger()


async def _download_clip(
    client: httpx.AsyncClient,
    url: str,
    dest_path: str,
) -> bool:
    """Download a single clip from fal.ai to a local temp file.

    Returns True on success, False on failure.
    """
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            f.write(resp.content)
        logger.debug("clip_downloaded", dest=dest_path, size=len(resp.content))
        return True
    except Exception as exc:
        logger.error("clip_download_failed", url=url[:120], error=str(exc))
        capture_exception(exc, {"context": "video_assembly.download_clip", "url": url[:120]})
        return False


async def assemble_clips(
    clip_urls: list[str],
    brand_id: str = "",
    label: str = "cinematic",
) -> str | None:
    """Download clip URLs, concatenate via FFmpeg, upload to S3.

    Args:
        clip_urls: List of video URLs (typically from fal.ai).
        brand_id: Brand UUID for S3 path organization.
        label: Descriptive label used in the S3 filename.

    Returns:
        S3 public URL of the assembled video, or None on failure.
    """
    if not clip_urls:
        logger.warning("assemble_clips.no_urls")
        return None

    with tempfile.TemporaryDirectory(prefix="presenceos_assembly_") as tmp_dir:
        # -- 1. Download all clips to temp files --
        async with httpx.AsyncClient(timeout=get_http_timeout("video_download")) as client:
            local_paths: list[str] = []
            for idx, url in enumerate(clip_urls):
                dest = os.path.join(tmp_dir, f"clip_{idx:02d}.mp4")
                ok = await _download_clip(client, url, dest)
                if ok:
                    local_paths.append(dest)

        if not local_paths:
            logger.error("assemble_clips.no_clips_downloaded", count=len(clip_urls))
            return None

        logger.info(
            "assemble_clips.downloaded",
            total=len(clip_urls),
            downloaded=len(local_paths),
        )

        # -- 2. Concatenate via FFmpegProcessor --
        try:
            processor = FFmpegProcessor()
            output_path = os.path.join(tmp_dir, f"assembled_{uuid.uuid4().hex[:8]}.mp4")
            concat_result = await processor.concatenate_clips(
                clip_paths=local_paths,
                output_path=output_path,
            )
            if not concat_result:
                logger.error("assemble_clips.concat_failed")
                return None
        except Exception as exc:
            logger.error("assemble_clips.concat_error", error=str(exc))
            capture_exception(exc, {"context": "video_assembly.concatenate"})
            return None

        # -- 3. Upload assembled video to S3 --
        try:
            with open(concat_result, "rb") as f:
                video_bytes = f.read()

            storage = get_storage_service()
            key = storage.generate_key(
                brand_id=brand_id or "ai-studio",
                media_type="video",
                original_filename=f"{label}_{len(local_paths)}clips_{uuid.uuid4().hex[:8]}.mp4",
            )
            result = await storage.upload_bytes(
                data=video_bytes,
                key=key,
                content_type="video/mp4",
            )

            s3_url = result["url"]
            logger.info(
                "assemble_clips.uploaded",
                key=key,
                size=len(video_bytes),
                clips=len(local_paths),
            )
            return s3_url

        except Exception as exc:
            logger.error("assemble_clips.upload_failed", error=str(exc))
            capture_exception(exc, {"context": "video_assembly.upload"})
            return None

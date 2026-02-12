"""
PresenceOS - Video Producer (Sprint 9C)

Orchestrates the full video production pipeline:
  1. Analyze user media + instructions
  2. Fetch B-roll from Pexels if needed
  3. Generate voiceover with TTS
  4. Select background music
  5. Compose final video with FFmpeg

The result is a professional Instagram Reel / TikTok-ready video.
"""
import os
import uuid
import tempfile
import structlog
import httpx

from app.core.config import settings
from app.services.pexels import PexelsService
from app.services.tts import TTSService
from app.services.music_library import MusicLibrary
from app.services.ffmpeg_processor import FFmpegProcessor
from app.services.storage import get_storage_service

logger = structlog.get_logger()


class VideoProducer:
    """
    Produce a complete video from user inputs.

    Takes images/videos + caption + AI tags and produces
    a polished social media video with voiceover and music.
    """

    def __init__(self):
        self.pexels = PexelsService()
        self.tts = TTSService()
        self.music = MusicLibrary()
        self.ffmpeg = FFmpegProcessor()

    async def produce(
        self,
        media_urls: list[str],
        media_types: list[str],
        caption: str,
        brand_id: str,
        ai_tags: list[str] | None = None,
        ai_description: str | None = None,
        max_duration: int | None = None,
        include_voiceover: bool = True,
        include_music: bool = True,
        include_broll: bool = True,
    ) -> dict | None:
        """
        Produce a complete video.

        Args:
            media_urls: User-uploaded media URLs
            media_types: Types for each URL ('image' or 'video')
            caption: The post caption (used for voiceover)
            brand_id: Brand UUID for storage
            ai_tags: AI-generated tags for B-roll search
            ai_description: AI description of the content
            max_duration: Max video duration in seconds
            include_voiceover: Whether to add TTS voiceover
            include_music: Whether to add background music
            include_broll: Whether to fetch B-roll from Pexels

        Returns:
            {"url": str, "key": str, "duration": int} or None on failure
        """
        max_dur = max_duration or settings.video_max_duration
        temp_files = []

        try:
            # Step 1: Download user media to local temp files
            local_media = await self._download_media(media_urls, media_types)
            if not local_media:
                logger.error("No media downloaded for video production")
                return None

            temp_files.extend([m["path"] for m in local_media])

            # Step 2: Convert images to video clips (Ken Burns)
            clips = []
            clip_duration = max_dur / max(len(local_media), 1)

            for i, media in enumerate(local_media):
                if media["type"] == "image":
                    direction = "in" if i % 2 == 0 else "out"
                    clip = await self.ffmpeg.image_to_video(
                        media["path"],
                        duration=min(clip_duration, 8.0),
                        zoom_direction=direction,
                    )
                    if clip:
                        clips.append(clip)
                        temp_files.append(clip)
                else:
                    clips.append(media["path"])

            # Step 3: Fetch B-roll if needed and enabled
            if include_broll and ai_tags and len(clips) < 3:
                broll_clips = await self._fetch_broll(
                    ai_tags, ai_description or "",
                    count=min(2, 3 - len(clips)),
                    clip_duration=clip_duration,
                )
                clips.extend(broll_clips)
                temp_files.extend(broll_clips)

            if not clips:
                logger.error("No clips generated for video")
                return None

            # Step 4: Concatenate all clips
            main_video = await self.ffmpeg.concatenate_clips(clips)
            if not main_video:
                logger.error("Failed to concatenate clips")
                return None
            if main_video not in temp_files:
                temp_files.append(main_video)

            # Step 5: Generate voiceover
            voiceover_path = None
            if include_voiceover and caption:
                voiceover_bytes = await self.tts.generate_speech_for_caption(caption)
                if voiceover_bytes:
                    voiceover_path = os.path.join(
                        settings.video_output_path,
                        f"vo_{uuid.uuid4().hex[:8]}.mp3",
                    )
                    with open(voiceover_path, "wb") as f:
                        f.write(voiceover_bytes)
                    temp_files.append(voiceover_path)

            # Step 6: Select background music
            music_path = None
            if include_music:
                mood = self.music.suggest_mood(
                    ai_tags or [], ai_description or ""
                )
                music_path = self.music.get_track(mood)

            # Step 7: Mix audio
            if voiceover_path or music_path:
                mixed = await self.ffmpeg.mix_audio_tracks(
                    main_video,
                    voiceover_path=voiceover_path,
                    music_path=music_path,
                    voiceover_volume=1.0,
                    music_volume=0.25,
                )
                if mixed and mixed != main_video:
                    if mixed not in temp_files:
                        temp_files.append(mixed)
                    main_video = mixed

            # Step 8: Format for social media (9:16, max duration)
            final_video = await self.ffmpeg.format_for_reel(
                main_video, max_duration=max_dur
            )
            if not final_video:
                logger.error("Failed to format video for reel")
                return None
            if final_video not in temp_files:
                temp_files.append(final_video)

            # Step 9: Upload to S3
            with open(final_video, "rb") as f:
                video_bytes = f.read()

            storage = get_storage_service()
            key = storage.generate_key(brand_id, "video", f"reel_{uuid.uuid4().hex[:8]}.mp4")
            upload_result = await storage.upload_bytes(
                video_bytes, key, content_type="video/mp4"
            )

            logger.info(
                "Video produced",
                brand_id=brand_id,
                clips=len(clips),
                has_voiceover=voiceover_path is not None,
                has_music=music_path is not None,
                size=upload_result["size"],
            )

            return {
                "url": upload_result["url"],
                "key": upload_result["key"],
                "size": upload_result["size"],
            }

        except Exception as e:
            logger.error("Video production failed", error=str(e))
            return None

        finally:
            # Cleanup temp files
            await self.ffmpeg.cleanup(*temp_files)

    async def _download_media(
        self, urls: list[str], types: list[str]
    ) -> list[dict]:
        """Download media files to local temp directory."""
        results = []

        async with httpx.AsyncClient(timeout=60.0) as client:
            for url, mtype in zip(urls, types):
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()

                    ext = "jpg" if mtype == "image" else "mp4"
                    path = os.path.join(
                        settings.video_output_path,
                        f"dl_{uuid.uuid4().hex[:8]}.{ext}",
                    )
                    with open(path, "wb") as f:
                        f.write(resp.content)

                    results.append({"path": path, "type": mtype})
                except Exception as e:
                    logger.warning("Failed to download media", url=url, error=str(e))

        return results

    async def _fetch_broll(
        self,
        tags: list[str],
        description: str,
        count: int = 2,
        clip_duration: float = 5.0,
    ) -> list[str]:
        """Fetch and prepare B-roll clips from Pexels."""
        clips = []

        if not self.pexels.is_configured:
            return clips

        # Build search query from tags
        query = " ".join(tags[:3]) if tags else "food restaurant"

        try:
            videos = await self.pexels.search_videos(
                query, per_page=count, orientation="portrait"
            )

            for video in videos[:count]:
                video_bytes = await self.pexels.download_video(video["url"])
                if not video_bytes:
                    continue

                # Save to temp
                path = os.path.join(
                    settings.video_output_path,
                    f"broll_{uuid.uuid4().hex[:8]}.mp4",
                )
                with open(path, "wb") as f:
                    f.write(video_bytes)

                clips.append(path)

        except Exception as e:
            logger.warning("B-roll fetch failed", error=str(e))

        return clips

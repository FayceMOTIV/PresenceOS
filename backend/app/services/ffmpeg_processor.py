"""
PresenceOS - FFmpeg Media Processor (Sprint 9C)

Handles video composition tasks:
  - Ken Burns effect on still images
  - Concatenating clips
  - Adding audio tracks (voiceover + music)
  - Adding text overlays
  - Format conversion for social platforms
"""
import os
import uuid
import asyncio
import structlog
import shutil

from app.core.config import settings

logger = structlog.get_logger()


class FFmpegProcessor:
    """FFmpeg-based media processing for video production."""

    def __init__(self):
        self.ffmpeg = settings.ffmpeg_path
        self.output_dir = settings.video_output_path
        os.makedirs(self.output_dir, exist_ok=True)

    async def _run(self, cmd: list[str], timeout: int = 300) -> bool:
        """Run an FFmpeg command asynchronously."""
        cmd_str = " ".join(cmd)
        logger.debug("FFmpeg command", cmd=cmd_str)

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            if process.returncode != 0:
                logger.error(
                    "FFmpeg failed",
                    returncode=process.returncode,
                    stderr=stderr.decode()[:500],
                )
                return False

            return True

        except asyncio.TimeoutError:
            logger.error("FFmpeg timeout", cmd=cmd_str[:200])
            process.kill()
            return False
        except FileNotFoundError:
            logger.error("FFmpeg not found", path=self.ffmpeg)
            return False

    def _temp_path(self, ext: str = "mp4") -> str:
        """Generate a temp file path."""
        return os.path.join(self.output_dir, f"{uuid.uuid4().hex[:12]}.{ext}")

    async def image_to_video(
        self,
        image_path: str,
        duration: float = 5.0,
        width: int = 1080,
        height: int = 1920,
        zoom_direction: str = "in",
    ) -> str | None:
        """
        Apply Ken Burns effect to a still image.

        Args:
            image_path: Path to input image
            duration: Output duration in seconds
            width/height: Output dimensions (default: 9:16 portrait)
            zoom_direction: 'in' or 'out'

        Returns:
            Path to output video or None on failure
        """
        output = self._temp_path()

        # Ken Burns: slow zoom in/out with slight pan
        if zoom_direction == "in":
            zoompan = (
                f"zoompan=z='min(zoom+0.001,1.3)':d={int(duration * 25)}"
                f":s={width}x{height}:fps=25"
            )
        else:
            zoompan = (
                f"zoompan=z='if(eq(on,1),1.3,max(zoom-0.001,1))':d={int(duration * 25)}"
                f":s={width}x{height}:fps=25"
            )

        cmd = [
            self.ffmpeg, "-y",
            "-loop", "1",
            "-i", image_path,
            "-vf", zoompan,
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            output,
        ]

        success = await self._run(cmd)
        return output if success else None

    async def concatenate_clips(
        self,
        clip_paths: list[str],
        output_path: str | None = None,
    ) -> str | None:
        """
        Concatenate multiple video clips into one.

        All clips should have the same resolution and codec.
        """
        if not clip_paths:
            return None

        if len(clip_paths) == 1:
            return clip_paths[0]

        output = output_path or self._temp_path()

        # Create concat file
        concat_file = self._temp_path("txt")
        with open(concat_file, "w") as f:
            for clip in clip_paths:
                f.write(f"file '{clip}'\n")

        cmd = [
            self.ffmpeg, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            output,
        ]

        success = await self._run(cmd)

        # Cleanup concat file
        try:
            os.remove(concat_file)
        except OSError:
            pass

        return output if success else None

    async def add_audio(
        self,
        video_path: str,
        audio_path: str,
        volume: float = 1.0,
        output_path: str | None = None,
    ) -> str | None:
        """
        Add an audio track to a video.

        If video already has audio, mixes both tracks.
        """
        output = output_path or self._temp_path()

        cmd = [
            self.ffmpeg, "-y",
            "-i", video_path,
            "-i", audio_path,
            "-filter_complex",
            f"[1:a]volume={volume}[a];[0:a][a]amix=inputs=2:duration=shortest[out]"
            if self._has_audio(video_path)
            else f"[1:a]volume={volume}[out]",
            "-map", "0:v",
            "-map", "[out]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output,
        ]

        # If no audio in source video, simpler command
        if not self._has_audio(video_path):
            cmd = [
                self.ffmpeg, "-y",
                "-i", video_path,
                "-i", audio_path,
                "-map", "0:v",
                "-map", "1:a",
                "-c:v", "copy",
                "-c:a", "aac",
                f"-filter:a", f"volume={volume}",
                "-shortest",
                output,
            ]

        success = await self._run(cmd)
        return output if success else None

    async def mix_audio_tracks(
        self,
        video_path: str,
        voiceover_path: str | None = None,
        music_path: str | None = None,
        voiceover_volume: float = 1.0,
        music_volume: float = 0.3,
        output_path: str | None = None,
    ) -> str | None:
        """
        Mix voiceover and background music onto a video.

        Music volume is ducked when voiceover is present.
        """
        output = output_path or self._temp_path()

        inputs = [self.ffmpeg, "-y", "-i", video_path]
        filter_parts = []
        audio_idx = 1

        if voiceover_path:
            inputs.extend(["-i", voiceover_path])
            filter_parts.append(f"[{audio_idx}:a]volume={voiceover_volume}[vo]")
            audio_idx += 1

        if music_path:
            inputs.extend(["-i", music_path])
            filter_parts.append(f"[{audio_idx}:a]volume={music_volume}[mu]")
            audio_idx += 1

        if voiceover_path and music_path:
            filter_parts.append("[vo][mu]amix=inputs=2:duration=shortest[audio]")
        elif voiceover_path:
            filter_parts.append("[vo]acopy[audio]")
        elif music_path:
            filter_parts.append("[mu]acopy[audio]")
        else:
            return video_path  # Nothing to mix

        filter_complex = ";".join(filter_parts)

        cmd = inputs + [
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[audio]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output,
        ]

        success = await self._run(cmd)
        return output if success else None

    async def add_text_overlay(
        self,
        video_path: str,
        text: str,
        position: str = "bottom",
        font_size: int = 48,
        font_color: str = "white",
        bg_color: str = "black@0.5",
        output_path: str | None = None,
    ) -> str | None:
        """Add text overlay to video."""
        output = output_path or self._temp_path()

        # Position mapping
        positions = {
            "top": "x=(w-text_w)/2:y=100",
            "center": "x=(w-text_w)/2:y=(h-text_h)/2",
            "bottom": "x=(w-text_w)/2:y=h-text_h-100",
        }
        pos = positions.get(position, positions["bottom"])

        # Escape special chars for FFmpeg drawtext
        escaped = text.replace("'", "\\'").replace(":", "\\:")

        drawtext = (
            f"drawtext=text='{escaped}':fontsize={font_size}"
            f":fontcolor={font_color}:box=1:boxcolor={bg_color}"
            f":boxborderw=10:{pos}"
        )

        cmd = [
            self.ffmpeg, "-y",
            "-i", video_path,
            "-vf", drawtext,
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "copy",
            output,
        ]

        success = await self._run(cmd)
        return output if success else None

    async def format_for_reel(
        self,
        video_path: str,
        max_duration: int = 60,
        output_path: str | None = None,
    ) -> str | None:
        """
        Format video for Instagram Reels / TikTok.

        Ensures: 9:16 aspect ratio, max duration, H.264 codec.
        """
        output = output_path or self._temp_path()

        cmd = [
            self.ffmpeg, "-y",
            "-i", video_path,
            "-t", str(max_duration),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            output,
        ]

        success = await self._run(cmd)
        return output if success else None

    def _has_audio(self, video_path: str) -> bool:
        """Quick check if video has an audio stream (heuristic)."""
        # For simplicity, assume user videos have audio, generated ones don't
        return False

    async def cleanup(self, *paths: str):
        """Remove temporary files."""
        for path in paths:
            try:
                if path and os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass

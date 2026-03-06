"""
BreakoutEngine — Pipeline de génération vidéo "3D Breakout"

Effet popularisé par Tim Gray (@iamtimgray) : le sujet sort du cadre vidéo
et déborde sur l'interface sociale. Crée une illusion de profondeur 3D.

Stack :
  - fal_client (subscribe_async) — SAM2, Depth Anything, Kling
  - Pillow — compositing frame-by-frame
  - FFmpeg — assemblage vidéo
  - numpy — analyse depth map

Pipeline :
  1. Kling génère la vidéo source (ou upload)
  2. Frame 0 → Depth Anything → centroïde du sujet en PIXELS ABSOLUS
  3. SAM2 video → masque binaire de la vidéo entière
  4. Pillow compose frame by frame (Breakout effect)
  5. FFmpeg assemble + remux audio
  6. fal_client.upload_file() → URL stockage
"""

import asyncio
import os
import tempfile
from pathlib import Path

import httpx
from PIL import Image, ImageFilter, ImageDraw

from app.core.config import settings

# ── Configuration compositing ────────────────────────────────────────────
CANVAS_W = 1080
CANVAS_H = 1920
VIDEO_ZONE_H = int(CANVAS_H * 0.60)    # 1152px — zone vidéo haute
UI_ZONE_H = CANVAS_H - VIDEO_ZONE_H    # 768px  — interface sociale blanche
SUBJECT_SCALE = 1.1                     # 110% — effet "coming toward you"
BOKEH_RADIUS = 3                        # léger flou depth-of-field sur fond
SHADOW_BLUR = 15                        # flou ombre portée
SHADOW_OPACITY = 140                    # 0-255
SHADOW_OFFSET_X = 8
SHADOW_OFFSET_Y = 12
VIDEO_FPS = 30


class BreakoutEngine:

    async def generate(
        self,
        source_type: str,
        source_url: str | None = None,
        ai_prompt: str | None = None,
        brand_id: str | None = None,
        on_progress: object = None,
    ) -> dict:
        """
        Pipeline complet Breakout :
          1. Obtenir vidéo source (Kling ou upload)
          2. Extraire frame 0 → détecter centre du sujet principal
          3. SAM2 video segmentation avec point d'ancrage pixel
          4. Compositing Breakout frame-by-frame
          5. Assembler + audio via FFmpeg
          6. Upload résultat vers fal.ai storage
        """
        self._setup_fal()

        # Étape 1 : Source vidéo
        if source_type == "ai_prompt":
            video_url = await self._kling_text_to_video(ai_prompt or "")
        elif source_type == "image":
            video_url = await self._kling_image_to_video(source_url or "", ai_prompt)
        else:
            video_url = source_url or ""

        # Étape 2 : Détecter point d'ancrage du sujet
        anchor = await self._detect_anchor_point(video_url)

        # Étape 3 : SAM2 segmentation vidéo
        mask_video_url = await self._sam2_segment(video_url, anchor)

        # Étape 4 & 5 : Compositing + rendu FFmpeg
        result_url = await self._composite_and_render(video_url, mask_video_url)

        return {
            "video_url": result_url,
            "source_type": source_type,
            "anchor_point": anchor,
        }

    # ── Setup fal.ai ───────────────────────────────────────────────────────

    def _setup_fal(self) -> None:
        """Set FAL_KEY env var (required by fal_client)."""
        fal_key = settings.fal_key
        if not fal_key:
            raise RuntimeError("FAL_KEY not configured")
        os.environ["FAL_KEY"] = fal_key

    # ── Génération vidéo ───────────────────────────────────────────────────

    async def _kling_text_to_video(self, prompt: str) -> str:
        """Kling text-to-video via fal.ai (subscribe_async = waits for result)."""
        import fal_client
        result = await fal_client.subscribe_async(
            "fal-ai/kling-video/v2.1/pro/text-to-video",
            arguments={
                "prompt": prompt,
                "duration": "5",
                "aspect_ratio": "9:16",
            },
        )
        url = result.get("video", {}).get("url") if isinstance(result, dict) else None
        if not url:
            raise RuntimeError("Kling text-to-video returned no video URL")
        return url

    async def _kling_image_to_video(self, image_url: str, prompt: str | None) -> str:
        """Kling image-to-video via fal.ai."""
        import fal_client
        result = await fal_client.subscribe_async(
            "fal-ai/kling-video/v2.1/pro/image-to-video",
            arguments={
                "image_url": image_url,
                "prompt": prompt or "smooth cinematic motion, camera slightly approaches subject",
                "duration": "5",
                "aspect_ratio": "9:16",
            },
        )
        url = result.get("video", {}).get("url") if isinstance(result, dict) else None
        if not url:
            raise RuntimeError("Kling image-to-video returned no video URL")
        return url

    # ── Détection du sujet ─────────────────────────────────────────────────

    async def _detect_anchor_point(self, video_url: str) -> dict:
        """
        1. Extraire frame 0 de la vidéo
        2. Depth Anything → trouver pixel le plus proche (centroïde zone claire)

        SAM2 attend des coordonnées PIXEL ABSOLUS (pas normalisées 0-1).
        Fallback : centre-haut (idéal pour plats restaurant).
        """
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                video_path = await self._download(video_url, f"{tmpdir}/src.mp4")

                frame_path = f"{tmpdir}/frame0.jpg"
                await self._run_cmd(
                    f"ffmpeg -i {video_path} -vframes 1 -q:v 2 {frame_path}"
                )

                if not os.path.exists(frame_path):
                    return self._default_anchor()

                img = Image.open(frame_path)
                w, h = img.size

                import fal_client
                frame_url = fal_client.upload_file(frame_path)

                depth_result = await fal_client.subscribe_async(
                    "fal-ai/imageutils/depth",
                    arguments={"image_url": frame_url},
                )
                depth_url = depth_result.get("image", {}).get("url") if isinstance(depth_result, dict) else None

                if not depth_url:
                    return {"x": w // 2, "y": int(h * 0.35), "w": w, "h": h}

                depth_path = f"{tmpdir}/depth.jpg"
                await self._download(depth_url, depth_path)

                anchor_x, anchor_y = self._find_closest_centroid(depth_path, w, h)
                return {"x": anchor_x, "y": anchor_y, "w": w, "h": h}

        except Exception:
            return self._default_anchor(640, 1136)

    def _find_closest_centroid(self, depth_path: str, orig_w: int, orig_h: int) -> tuple:
        """
        Analyse depth map (grayscale) :
        - Pixels CLAIRS = sujets PROCHES
        - Pixels SOMBRES = fond lointain
        Retourne centroïde de la zone la plus claire.
        """
        import numpy as np

        depth_img = Image.open(depth_path).convert("L").resize((orig_w, orig_h))
        arr = np.array(depth_img)

        threshold = np.percentile(arr, 80)
        mask = arr >= threshold

        if not mask.any():
            return orig_w // 2, int(orig_h * 0.35)

        ys, xs = np.where(mask)
        cx = int(xs.mean())
        cy = int(ys.mean())

        cx = max(20, min(cx, orig_w - 20))
        cy = max(20, min(cy, orig_h - 20))

        return cx, cy

    def _default_anchor(self, w: int = 640, h: int = 1136) -> dict:
        return {"x": w // 2, "y": int(h * 0.35), "w": w, "h": h}

    # ── SAM2 segmentation ──────────────────────────────────────────────────

    async def _sam2_segment(self, video_url: str, anchor: dict) -> str:
        """
        SAM2 video segmentation via fal.ai.

        Schema vérifié (fal.ai/models/fal-ai/sam2/video/api) :
          prompts: [{x, y, label, frame_index}]
            - x, y = pixels ABSOLUS
            - label = 1 (foreground)
            - frame_index = 0
          apply_mask: False → retourne vidéo masque alpha B&W
        """
        import fal_client

        ax = anchor.get("x", 320)
        ay = anchor.get("y", 400)

        result = await fal_client.subscribe_async(
            "fal-ai/sam2/video",
            arguments={
                "video_url": video_url,
                "prompts": [
                    {"x": ax, "y": ay, "label": 1, "frame_index": 0},
                ],
                "apply_mask": False,
            },
        )
        url = result.get("video", {}).get("url") if isinstance(result, dict) else None
        if not url:
            raise RuntimeError("SAM2 returned no mask video URL")
        return url

    # ── Compositing Breakout ───────────────────────────────────────────────

    async def _composite_and_render(
        self,
        original_video_url: str,
        mask_video_url: str,
    ) -> str:
        """
        Compositing "Tim Gray Breakout" frame-by-frame :

        Couches (bas → haut) :
          1. Canvas blanc 1080×1920
          2. Zone vidéo (top 60%) — vidéo originale avec bokeh léger
          3. Zone UI blanche (bottom 40%) — interface Instagram fake
          4. Ombre portée du sujet (sur zone blanche uniquement)
          5. Sujet découpé SAM2 (scale 1.1x, déborde vers le bas)
        """
        import fal_client

        with tempfile.TemporaryDirectory() as tmpdir:
            orig_path = await self._download(original_video_url, f"{tmpdir}/original.mp4")
            mask_path_dl = await self._download(mask_video_url, f"{tmpdir}/mask.mp4")

            orig_dir = f"{tmpdir}/orig_frames"
            mask_dir = f"{tmpdir}/mask_frames"
            out_dir = f"{tmpdir}/out_frames"
            os.makedirs(orig_dir, exist_ok=True)
            os.makedirs(mask_dir, exist_ok=True)
            os.makedirs(out_dir, exist_ok=True)

            await self._run_cmd(
                f"ffmpeg -i {orig_path} -q:v 2 {orig_dir}/%04d.jpg -y"
            )
            await self._run_cmd(
                f"ffmpeg -i {mask_path_dl} -q:v 2 {mask_dir}/%04d.png -y"
            )

            orig_frames = sorted(Path(orig_dir).glob("*.jpg"))
            if not orig_frames:
                raise ValueError("Aucune frame extraite de la vidéo originale")

            sample = Image.open(orig_frames[0])
            src_w, src_h = sample.size

            mask_frames = sorted(Path(mask_dir).glob("*.png"))
            frame_count = min(len(orig_frames), len(mask_frames))

            for i in range(frame_count):
                frame_num = f"{i + 1:04d}"
                orig_frame = Image.open(orig_frames[i]).convert("RGBA")
                mask_frame = Image.open(mask_frames[i]).convert("L")

                composed = self._compose_breakout_frame(
                    orig_frame, mask_frame, src_w, src_h
                )
                composed.convert("RGB").save(f"{out_dir}/{frame_num}.jpg", quality=95)

            output_path = f"{tmpdir}/breakout_final.mp4"
            await self._run_cmd(
                f"ffmpeg -r {VIDEO_FPS} -i {out_dir}/%04d.jpg "
                f"-i {orig_path} "
                f"-map 0:v -map 1:a? "
                f"-c:v libx264 -crf 18 -pix_fmt yuv420p "
                f"-c:a aac -shortest "
                f"{output_path} -y"
            )

            result_url = fal_client.upload_file(output_path)
            return result_url

    def _compose_breakout_frame(
        self,
        orig_frame: Image.Image,
        mask_frame: Image.Image,
        src_w: int,
        src_h: int,
    ) -> Image.Image:
        """Compose une frame Breakout complète 1080×1920."""
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (255, 255, 255, 255))

        # Layer 2 : Zone vidéo (top 60%) avec bokeh
        video_crop = orig_frame.resize((CANVAS_W, VIDEO_ZONE_H), Image.LANCZOS)
        video_bokeh = video_crop.filter(ImageFilter.GaussianBlur(BOKEH_RADIUS))
        canvas.paste(video_bokeh.convert("RGB"), (0, 0))

        # Layer 3 : Zone UI blanche (bottom 40%)
        ui = self._render_instagram_ui(CANVAS_W, UI_ZONE_H)
        canvas.paste(ui, (0, VIDEO_ZONE_H))

        # Extraire le sujet découpé par SAM2
        mask_resized = mask_frame.resize((src_w, src_h), Image.LANCZOS)
        subject_rgba = Image.new("RGBA", (src_w, src_h), (0, 0, 0, 0))
        orig_rgba_src = orig_frame.resize((src_w, src_h), Image.LANCZOS)
        subject_rgba.paste(orig_rgba_src, mask=mask_resized)

        # Scale sujet à 1.1x
        scale_w = int(CANVAS_W * SUBJECT_SCALE)
        scale_h = int(scale_w * src_h / src_w)
        subject_scaled = subject_rgba.resize((scale_w, scale_h), Image.LANCZOS)
        mask_scaled = mask_resized.resize((scale_w, scale_h), Image.LANCZOS)

        # Position du sujet : centré, déborde 15% dans la zone blanche
        sx = (CANVAS_W - scale_w) // 2
        sy = VIDEO_ZONE_H - scale_h + int(scale_h * 0.15)

        # Layer 4 : Ombre portée (zone blanche uniquement)
        shadow = self._create_shadow(mask_scaled)
        shadow_x = sx + SHADOW_OFFSET_X
        shadow_y = sy + SHADOW_OFFSET_Y
        if shadow_y < CANVAS_H and shadow_y + scale_h > VIDEO_ZONE_H:
            canvas.paste(shadow, (shadow_x, shadow_y), shadow)

        # Layer 5 : Sujet découpé
        canvas.paste(subject_scaled, (sx, sy), subject_scaled)

        return canvas

    def _render_instagram_ui(self, width: int, height: int) -> Image.Image:
        """Fausse interface Instagram (zone blanche, gris doux)."""
        ui = Image.new("RGBA", (width, height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(ui)

        pad = 24
        draw.line([(0, 0), (width, 0)], fill=(220, 220, 220), width=1)

        # Avatar circle
        av_r = 22
        draw.ellipse([pad, 18, pad + av_r * 2, 18 + av_r * 2], fill=(210, 210, 215))

        # Username + subtitle bars
        name_x = pad + av_r * 2 + 12
        draw.rounded_rectangle([name_x, 22, name_x + 120, 36], radius=4, fill=(195, 195, 200))
        draw.rounded_rectangle([name_x, 42, name_x + 80, 52], radius=3, fill=(218, 218, 222))

        # Description lignes
        desc_y = 18 + av_r * 2 + 18
        draw.rounded_rectangle([pad, desc_y, width - pad, desc_y + 12], radius=3, fill=(228, 228, 232))
        draw.rounded_rectangle([pad, desc_y + 18, int(width * 0.6), desc_y + 30], radius=3, fill=(238, 238, 242))

        # Boutons like / comment / share
        btn_y = height - 58
        for idx in range(3):
            bx = pad + idx * 56
            draw.ellipse([bx, btn_y, bx + 40, btn_y + 40], outline=(210, 210, 215), width=2)

        # Compteur likes
        draw.rounded_rectangle([pad, height - 28, pad + 60, height - 16], radius=3, fill=(228, 228, 232))

        return ui

    def _create_shadow(self, mask: Image.Image) -> Image.Image:
        """Ombre portée semi-transparente basée sur la silhouette SAM2."""
        shadow = Image.new("RGBA", mask.size, (0, 0, 0, 0))
        color_layer = Image.new("RGBA", mask.size, (0, 0, 0, SHADOW_OPACITY))
        shadow.paste(color_layer, mask=mask)
        return shadow.filter(ImageFilter.GaussianBlur(SHADOW_BLUR))

    # ── Utilitaires ────────────────────────────────────────────────────────

    async def _download(self, url: str, path: str) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.get(url)
            r.raise_for_status()
            with open(path, "wb") as f:
                f.write(r.content)
        return path

    async def _run_cmd(self, cmd: str) -> None:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {stderr.decode()[:500]}")

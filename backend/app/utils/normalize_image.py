"""
PresenceOS — Image normalization utility

Handles HEIC/HEIF (iPhone) and WebP conversion to JPEG.
Uses pillow-heif to register HEIC opener with Pillow.
"""

import io

from PIL import Image

# Register HEIC/HEIF opener globally (safe to call multiple times)
try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:
    pass  # pillow-heif not installed — HEIC won't be supported


def normalize_image(raw_bytes: bytes, max_size: int = 2048, quality: int = 85) -> bytes:
    """
    Convert any supported image (HEIC, WebP, PNG, TIFF, BMP) to JPEG.

    Args:
        raw_bytes: Raw image bytes (any format Pillow can read).
        max_size: Max dimension (width or height). Resized proportionally if larger.
        quality: JPEG quality (1-100).

    Returns:
        JPEG bytes, RGB mode, EXIF orientation applied.
    """
    img = Image.open(io.BytesIO(raw_bytes))

    # Apply EXIF orientation (iPhone photos are often rotated in EXIF)
    try:
        from PIL import ImageOps

        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    # Resize if too large
    if max(img.size) > max_size:
        img.thumbnail((max_size, max_size), Image.LANCZOS)

    # Convert to RGB (drop alpha, handle CMYK, etc.)
    if img.mode not in ("RGB",):
        img = img.convert("RGB")

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()

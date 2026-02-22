"""File upload validation utilities."""
from fastapi import UploadFile, HTTPException
import hashlib
import io

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif", "heic", "heif"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/heic",
    "image/heif",
    "video/mp4",
    "video/quicktime",
}
MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20 MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100 MB
MIN_IMAGE_DIMENSION = 100  # px
MAX_IMAGE_DIMENSION = 8000  # px


async def validate_image_upload(file: UploadFile) -> tuple[bytes, str]:
    """
    Validate an uploaded image file.

    Returns: (file_bytes, file_hash)
    Raises: HTTPException if invalid
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extension .{ext} non autorisée. Utilisez : {', '.join(ALLOWED_IMAGE_EXTENSIONS)}",
        )

    contents = await file.read()

    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Fichier trop volumineux. Maximum {MAX_IMAGE_SIZE // (1024 * 1024)} Mo",
        )

    if len(contents) < 100:
        raise HTTPException(status_code=400, detail="Fichier trop petit ou corrompu")

    # Check magic bytes for image format
    if contents[:2] == b"\xff\xd8":
        detected = "jpeg"
    elif contents[:8] == b"\x89PNG\r\n\x1a\n":
        detected = "png"
    elif contents[:4] == b"RIFF" and contents[8:12] == b"WEBP":
        detected = "webp"
    elif contents[:6] == b"GIF87a" or contents[:6] == b"GIF89a":
        detected = "gif"
    elif contents[4:12] == b"ftypheic" or contents[4:12] == b"ftypmif1" or contents[4:12] == b"ftyphevc":
        detected = "heic"
    else:
        raise HTTPException(status_code=400, detail="Format d'image non reconnu")

    # Validate dimensions using PIL if available
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(contents))
        width, height = img.size
        if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
            raise HTTPException(
                status_code=400,
                detail=f"Image trop petite. Minimum {MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION}px",
            )
        if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
            raise HTTPException(
                status_code=400,
                detail=f"Image trop grande. Maximum {MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION}px",
            )
    except ImportError:
        pass  # PIL not available, skip dimension check
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Fichier image invalide ou corrompu")

    file_hash = hashlib.sha256(contents).hexdigest()
    return contents, file_hash

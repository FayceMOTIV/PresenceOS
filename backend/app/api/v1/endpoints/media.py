"""
PresenceOS - Media Upload Endpoints
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from pydantic import BaseModel

from app.api.v1.deps import CurrentUser
from app.models.user import User
from app.services.storage import get_storage_service, StorageService, LocalStorageService
from app.utils.file_validation import validate_image_upload, ALLOWED_IMAGE_EXTENSIONS

router = APIRouter()


class UploadResponse(BaseModel):
    """Response for successful upload."""
    key: str
    url: str
    size: int
    content_type: str | None


class PresignedUrlRequest(BaseModel):
    """Request for generating a presigned upload URL."""
    filename: str
    content_type: str


class PresignedUrlResponse(BaseModel):
    """Response with presigned URL for direct upload."""
    upload_url: str
    key: str
    public_url: str
    expires_in: int


# Allowed content types for media uploads
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/heic",
    "image/heif",
}

ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/webm",
    "video/x-msvideo",
}

ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES

# Max file sizes (in bytes)
MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20 MB
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500 MB


def get_max_size(content_type: str) -> int:
    """Get max file size based on content type."""
    if content_type in ALLOWED_VIDEO_TYPES:
        return MAX_VIDEO_SIZE
    return MAX_IMAGE_SIZE


@router.post("/brands/{brand_id}/upload", response_model=UploadResponse)
async def upload_media(
    brand_id: UUID,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    storage: StorageService | LocalStorageService = Depends(get_storage_service),
):
    """
    Upload a media file (image or video) for a brand.

    Supports:
    - Images: JPEG, PNG, GIF, WebP, HEIC
    - Videos: MP4, MOV, WebM, AVI

    Returns the storage key and public URL.
    """
    # Validate content type
    content_type = file.content_type
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Type de fichier non supporte: {content_type}. "
                   f"Types acceptes: {', '.join(ALLOWED_TYPES)}",
        )

    # Check file size (approximate, from content-length header)
    max_size = get_max_size(content_type)

    # Read and validate file content
    if content_type in ALLOWED_IMAGE_TYPES:
        # validate_image_upload reads the file, checks extension, size, magic bytes, and dimensions
        content, _file_hash = await validate_image_upload(file)
    else:
        content = await file.read()

    file_size = len(content)

    if file_size > max_size:
        max_mb = max_size // (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"Fichier trop volumineux. Taille maximale: {max_mb} MB",
        )

    # Generate storage key
    key = storage.generate_key(
        brand_id=str(brand_id),
        media_type="image" if content_type in ALLOWED_IMAGE_TYPES else "video",
        original_filename=file.filename or "media",
    )

    # Upload file
    from io import BytesIO
    try:
        result = await storage.upload_file(
            file=BytesIO(content),
            key=key,
            content_type=content_type,
            metadata={
                "brand_id": str(brand_id),
                "uploader_id": str(current_user.id),
                "original_filename": file.filename or "",
            },
        )
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Service de stockage indisponible",
        )

    return UploadResponse(
        key=result["key"],
        url=result["url"],
        size=result["size"],
        content_type=content_type,
    )


@router.post("/brands/{brand_id}/presigned-url", response_model=PresignedUrlResponse)
async def get_presigned_upload_url(
    brand_id: UUID,
    request: PresignedUrlRequest,
    current_user: CurrentUser,
    storage: StorageService | LocalStorageService = Depends(get_storage_service),
):
    """
    Get a presigned URL for direct upload to S3/MinIO.

    Use this for large files to upload directly from the browser
    without going through the API server.
    """
    # Validate content type
    if request.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Type de fichier non supporte: {request.content_type}",
        )

    # Generate storage key
    key = storage.generate_key(
        brand_id=str(brand_id),
        media_type="image" if request.content_type in ALLOWED_IMAGE_TYPES else "video",
        original_filename=request.filename,
    )

    # Generate presigned URL (valid for 1 hour)
    expires_in = 3600
    upload_url = storage.generate_presigned_url(
        key=key,
        expires_in=expires_in,
        for_upload=True,
        content_type=request.content_type,
    )

    return PresignedUrlResponse(
        upload_url=upload_url,
        key=key,
        public_url=storage.get_public_url(key),
        expires_in=expires_in,
    )


@router.delete("/brands/{brand_id}/media/{key:path}")
async def delete_media(
    brand_id: UUID,
    key: str,
    current_user: CurrentUser,
    storage: StorageService | LocalStorageService = Depends(get_storage_service),
):
    """Delete a media file."""
    # Verify the key belongs to this brand
    if not key.startswith(f"brands/{brand_id}/"):
        raise HTTPException(
            status_code=403,
            detail="Acces non autorise a ce fichier",
        )

    success = await storage.delete_file(key)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Fichier non trouve",
        )

    return {"status": "deleted", "key": key}


@router.get("/brands/{brand_id}/media/{key:path}")
async def get_media_info(
    brand_id: UUID,
    key: str,
    current_user: CurrentUser,
    storage: StorageService | LocalStorageService = Depends(get_storage_service),
):
    """Get information about a media file."""
    # Verify the key belongs to this brand
    if not key.startswith(f"brands/{brand_id}/"):
        raise HTTPException(
            status_code=403,
            detail="Acces non autorise a ce fichier",
        )

    info = await storage.get_file_info(key)
    if not info:
        raise HTTPException(
            status_code=404,
            detail="Fichier non trouve",
        )

    return info

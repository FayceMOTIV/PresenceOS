"""
PresenceOS - Menu Scan API

Endpoints for OCR scanning paper menu photos and importing extracted dishes.
"""
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, UploadFile, File, status
from pydantic import BaseModel, Field

from app.api.v1.deps import CurrentUser, DBSession, get_brand
from app.services.ocr_service import OCRService
from app.services.content_library import ContentLibraryService

logger = structlog.get_logger()
router = APIRouter()

MAX_SCAN_SIZE = 20 * 1024 * 1024  # 20 MB
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}


# ── Request/Response Models ──────────────────────────────────────────────


class DishScanItem(BaseModel):
    name: str
    category: str
    price: float | None
    description: str | None


class ScanResultResponse(BaseModel):
    dishes: list[DishScanItem]
    total: int


class ImportRequest(BaseModel):
    dishes: list[DishScanItem] = Field(..., min_length=1)


class ImportResponse(BaseModel):
    imported_count: int
    dish_ids: list[str]


# ── Endpoints ────────────────────────────────────────────────────────────


@router.post("/{brand_id}/scan")
async def scan_menu(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
    file: UploadFile = File(...),
) -> ScanResultResponse:
    """Upload a menu photo and extract dishes via OCR.

    Returns a list of extracted dishes for user validation before import.
    """
    await get_brand(brand_id, current_user, db)

    # Validate file
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. Allowed: JPEG, PNG, WebP, HEIC.",
        )

    contents = await file.read()
    if len(contents) > MAX_SCAN_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {MAX_SCAN_SIZE // (1024*1024)} MB.",
        )

    ocr = OCRService()
    try:
        raw_dishes = await ocr.scan_menu_image(contents, file.content_type or "image/jpeg")
    except Exception as exc:
        logger.error("Menu scan failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract menu items from this image. Please try a clearer photo.",
        )

    dishes = [DishScanItem(**d) for d in raw_dishes]
    return ScanResultResponse(dishes=dishes, total=len(dishes))


@router.post("/{brand_id}/scan/import", status_code=status.HTTP_201_CREATED)
async def import_scanned_dishes(
    brand_id: UUID,
    body: ImportRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> ImportResponse:
    """Import validated dish list from OCR scan into the content library.

    Also triggers a KB rebuild.
    """
    await get_brand(brand_id, current_user, db)

    service = ContentLibraryService(db)
    dishes_data = [d.model_dump() for d in body.dishes]
    created = await service.import_dishes(str(brand_id), dishes_data)

    return ImportResponse(
        imported_count=len(created),
        dish_ids=[str(d.id) for d in created],
    )

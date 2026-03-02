"""
PresenceOS — A/B Testing API v2 (Sprint 8)

Create A/B tests and view results.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.api.v2.deps import FirebaseUser, DBSession
from app.middleware.rate_limit import limiter
from app.services.ab_testing import ABTestingService
from app.services.firebase_firestore import FirestoreService

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateABTestRequest(BaseModel):
    platform: str = Field(..., description="Target platform (instagram, facebook, tiktok)")
    original_caption: str = Field(..., min_length=1, max_length=5000)
    post_topic: Optional[str] = Field(default="", max_length=200)


@router.post(
    "/{brand_id}/create",
    summary="Create an A/B test",
)
@limiter.limit("10/minute")
async def create_ab_test(
    request: Request,
    brand_id: str,
    body: CreateABTestRequest,
    user: FirebaseUser,
    db: DBSession,
):
    """Generate 2 caption variants for A/B testing."""
    try:
        # Load DNA for brand context
        firestore = FirestoreService()
        dna_data = await firestore.get_subcollection_doc(
            "businesses", brand_id, "dna", "profile"
        )

        service = ABTestingService()
        test = await service.create_ab_test(
            business_id=brand_id,
            platform=body.platform,
            original_caption=body.original_caption,
            business_dna=dna_data,
            post_topic=body.post_topic or "",
        )
        return {"success": True, "test": test.to_dict()}
    except Exception as exc:
        logger.error("create_ab_test failed", extra={"brand_id": brand_id, "error": str(exc)})
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/{brand_id}/tests",
    summary="Get A/B test history",
)
@limiter.limit("30/minute")
async def get_ab_tests(
    request: Request,
    brand_id: str,
    user: FirebaseUser,
    db: DBSession,
):
    """Get A/B test history and accumulated insights."""
    service = ABTestingService()
    tests = await service.get_tests_for_business(brand_id)
    return {"tests": tests, "total": len(tests)}

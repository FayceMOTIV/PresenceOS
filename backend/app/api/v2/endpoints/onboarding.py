"""
PresenceOS — Onboarding API v2 (Sprint 4 + Sprint 6 + Sprint B2)

Conversational onboarding endpoints for Ilyas Business DNA.
Persists state in PostgreSQL (OnboardingState) alongside Firestore.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.api.v2.deps import FirebaseUser, DBSession, verify_brand_access
from app.middleware.rate_limit import limiter
from app.services.ilyas.onboarding_agent import OnboardingAgent, TOTAL_STEPS
from app.services.onboarding_service import OnboardingService

logger = logging.getLogger(__name__)

router = APIRouter()


class ScrapeRequest(BaseModel):
    url: str = Field(..., min_length=3, max_length=500, description="Website URL to scrape")


class AnswerRequest(BaseModel):
    step: int = Field(..., ge=0, lt=TOTAL_STEPS, description="Current step (0-indexed)")
    answer: str = Field(..., min_length=1, max_length=2000, description="User's free-text answer")


class StartResponse(BaseModel):
    step: int
    question: str | None
    complete: bool
    dna: dict[str, Any]


class AnswerResponse(BaseModel):
    step: int
    extracted: dict[str, Any]
    next_step: int | None
    next_question: str | None
    dna: dict[str, Any]
    complete: bool


class DNAResponse(BaseModel):
    dna: dict[str, Any] | None
    complete: bool


# ── Endpoints ──


@router.get(
    "/brands/{brand_id}/onboarding/start",
    response_model=StartResponse,
    summary="Start or resume onboarding",
)
@limiter.limit("20/minute")
async def start_onboarding(
    request: Request,
    brand_id: str,
    user: FirebaseUser,
    db: DBSession,
):
    """Start onboarding or resume from where the user left off."""
    brand = await verify_brand_access(brand_id, user, db)
    agent = OnboardingAgent()
    result = await agent.start_onboarding(brand_id)

    svc = OnboardingService(db)
    await svc.get_or_create_state(brand.id)

    return result


@router.post(
    "/brands/{brand_id}/onboarding/answer",
    response_model=AnswerResponse,
    summary="Submit an onboarding answer",
)
@limiter.limit("20/minute")
async def submit_answer(
    request: Request,
    brand_id: str,
    body: AnswerRequest,
    user: FirebaseUser,
    db: DBSession,
):
    """Process a user's answer for the current onboarding step."""
    brand = await verify_brand_access(brand_id, user, db)
    agent = OnboardingAgent()
    result = await agent.process_answer(
        business_id=brand_id,
        step=body.step,
        user_answer=body.answer,
    )

    svc = OnboardingService(db)
    await svc.advance_step(
        brand_id=brand.id,
        step=body.step,
        answer=body.answer,
        extracted=result.get("extracted", {}),
        dna_snapshot=result.get("dna", {}),
    )

    return result


@router.get(
    "/brands/{brand_id}/onboarding/dna",
    response_model=DNAResponse,
    summary="Get current Business DNA",
)
@limiter.limit("30/minute")
async def get_dna(
    request: Request,
    brand_id: str,
    user: FirebaseUser,
    db: DBSession,
):
    """Retrieve the current Business DNA profile."""
    await verify_brand_access(brand_id, user, db)
    agent = OnboardingAgent()
    dna = await agent.get_dna(brand_id)
    return {
        "dna": dna.to_dict() if dna else None,
        "complete": dna.onboarding_complete if dna else False,
    }


@router.post(
    "/brands/{brand_id}/scrape",
    summary="Scrape website and pre-fill Business DNA",
)
@limiter.limit("5/minute")
async def scrape_website(
    request: Request,
    brand_id: str,
    body: ScrapeRequest,
    user: FirebaseUser,
    db: DBSession,
):
    """Scrape a business website and pre-fill the Business DNA before onboarding."""
    brand = await verify_brand_access(brand_id, user, db)
    svc = OnboardingService(db)
    try:
        from app.services.firecrawl_scraper import FirecrawlScraper
        from app.services.firebase_firestore import FirestoreService

        scraper = FirecrawlScraper()
        result = await scraper.scrape_and_extract(body.url)

        # Save partial DNA to Firestore
        if result["success"]:
            firestore = FirestoreService()
            await firestore.set_subcollection_doc(
                "businesses", brand_id, "dna", "profile",
                result["dna"], merge=True,
            )
            await svc.set_scrape_result(
                brand_id=brand.id,
                website_url=body.url,
                scrape_status="success",
                dna_partial=result["dna"],
            )
        else:
            await svc.set_scrape_result(
                brand_id=brand.id,
                website_url=body.url,
                scrape_status="failed",
            )

        return {
            "success": result["success"],
            "fields_found": result["fields_found"],
            "dna": result["dna"],
            "message": (
                f"J'ai trouve {result['fields_found']} informations sur votre commerce !"
                if result["success"]
                else "Je n'ai pas pu analyser ce site. On va remplir les infos ensemble."
            ),
        }
    except Exception as exc:
        logger.error("scrape_website failed", extra={"brand_id": brand_id, "error": str(exc)})
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/brands/{brand_id}/onboarding/state",
    summary="Get onboarding state from PostgreSQL",
)
@limiter.limit("30/minute")
async def get_onboarding_state(
    request: Request,
    brand_id: str,
    user: FirebaseUser,
    db: DBSession,
):
    """Get onboarding progress from PostgreSQL (step, completion, DNA)."""
    brand = await verify_brand_access(brand_id, user, db)
    svc = OnboardingService(db)
    state = await svc.get_state(brand.id)

    if not state:
        return {
            "current_step": 0,
            "total_steps": TOTAL_STEPS,
            "is_complete": False,
            "dna_snapshot": {},
            "website_url": None,
            "scrape_status": None,
        }

    return {
        "current_step": state.current_step,
        "total_steps": state.total_steps,
        "is_complete": state.is_complete,
        "dna_snapshot": state.dna_snapshot,
        "website_url": state.website_url,
        "scrape_status": state.scrape_status,
    }


@router.post(
    "/brands/{brand_id}/onboarding/reset",
    summary="Reset onboarding state",
)
@limiter.limit("5/minute")
async def reset_onboarding(
    request: Request,
    brand_id: str,
    user: FirebaseUser,
    db: DBSession,
):
    """Reset onboarding to start over."""
    brand = await verify_brand_access(brand_id, user, db)
    svc = OnboardingService(db)
    state = await svc.reset(brand.id)
    return {
        "success": True,
        "current_step": state.current_step,
        "is_complete": state.is_complete,
    }

"""
PresenceOS - Brands v2 Endpoints (Niche Engine)
"""
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Request, status

from app.api.v2.deps import FirebaseUser, DBSession, verify_brand_access
from app.data.niches import detect_niche, NICHES

logger = structlog.get_logger()
router = APIRouter()


@router.post("/{brand_id}/niche")
async def set_brand_niche(
    brand_id: UUID,
    business_type: str,
    current_user: FirebaseUser,
    db: DBSession,
) -> dict:
    """
    Définit la niche du brand -> Ilyas s'adapte immédiatement.
    Appelé par l'onboarding app ET par Morpheus via MCP.
    """
    brand = await verify_brand_access(str(brand_id), current_user, db)

    niche = detect_niche(business_type)

    # Sauvegarder le type de business dans le champ niche
    brand.niche = business_type
    await db.commit()

    return {
        "brand_id": str(brand_id),
        "niche_detected": niche["label"],
        "platforms_priority": niche["platforms_priority"],
        "content_pillars": niche["content_pillars"],
        "legal_constraints": niche["legal_constraints"],
        "message": f"Ilyas est maintenant expert {niche['label']} pour ce brand.",
    }


@router.get("/niches/list")
async def list_available_niches() -> dict:
    """
    Liste toutes les niches disponibles.
    Utilisé par le NicheSelector dans l'onboarding mobile.
    """
    return {
        key: {
            "label": v["label"],
            "platforms": v["platforms_priority"],
            "audience": v["audience"],
        }
        for key, v in NICHES.items()
    }

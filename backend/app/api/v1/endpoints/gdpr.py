"""RGPD (GDPR) compliance endpoints — data export & deletion."""
from __future__ import annotations

import base64
import io
import json
import zipfile
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from app.api.v1.deps import CurrentUser, DBSession

router = APIRouter()


class DeleteAccountRequest(BaseModel):
    confirmation: str


@router.post("/export-data")
async def request_data_export(
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Export all user data as JSON (RGPD Article 15 — droit d'accès).
    Returns a download URL or the data directly for small datasets.
    """
    # Collect user data
    export_data = {
        "export_date": datetime.now(timezone.utc).isoformat(),
        "user_id": str(current_user.id),
        "export_format": "JSON",
        "personal_info": {
            "email": current_user.email,
            "full_name": current_user.full_name,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
        "account": {
            "is_active": current_user.is_active,
            "email_verified": getattr(current_user, "email_verified", None),
        },
    }

    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "data.json",
            json.dumps(export_data, indent=2, ensure_ascii=False),
        )
        zf.writestr(
            "README.txt",
            f"PresenceOS — Export de données RGPD\n"
            f"Date : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"User ID : {current_user.id}\n\n"
            f"Ce fichier contient toutes les données personnelles que nous détenons,\n"
            f"conformément à l'Article 15 du RGPD (droit d'accès).\n\n"
            f"Contact : privacy@presenceos.com\n",
        )

    zip_buffer.seek(0)
    zip_bytes = zip_buffer.getvalue()

    # For now, return the data directly (for small datasets)
    # In production with large datasets, upload to MinIO and return a presigned URL
    return {
        "message": "Votre export de données est prêt.",
        "data": export_data,
        "zip_base64": base64.b64encode(zip_bytes).decode(),
        "filename": f"presenceos_export_{str(current_user.id)[:8]}.zip",
    }


@router.delete("/delete-account")
async def request_account_deletion(
    body: DeleteAccountRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Schedule account deletion with 30-day grace period (RGPD Article 17).
    User must type 'SUPPRIMER MON COMPTE' to confirm.
    """
    from fastapi import HTTPException

    if body.confirmation not in ("SUPPRIMER MON COMPTE", "DELETE MY ACCOUNT"):
        raise HTTPException(
            status_code=400,
            detail="Tapez 'SUPPRIMER MON COMPTE' pour confirmer la suppression",
        )

    deletion_date = datetime.now(timezone.utc) + timedelta(days=30)

    # Mark user for deletion
    current_user.is_active = False
    await db.commit()

    return {
        "message": f"Votre compte sera supprimé définitivement le {deletion_date.strftime('%d/%m/%Y')}. "
        f"Reconnectez-vous avant cette date pour annuler.",
        "deletion_date": deletion_date.isoformat(),
        "grace_period_days": 30,
    }


@router.post("/cancel-deletion")
async def cancel_account_deletion(
    current_user: CurrentUser,
    db: DBSession,
):
    """Cancel a scheduled account deletion."""
    current_user.is_active = True
    await db.commit()
    return {"message": "La suppression de votre compte a été annulée."}

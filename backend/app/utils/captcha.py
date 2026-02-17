"""hCaptcha verification utility."""
import os

import httpx
from fastapi import HTTPException


async def verify_captcha(token: str) -> bool:
    """Verify hCaptcha token server-side."""
    secret = os.getenv("HCAPTCHA_SECRET")
    if not secret:
        # If no secret configured, skip verification (dev mode)
        return True

    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://hcaptcha.com/siteverify",
            data={
                "secret": secret,
                "response": token,
            },
        )
        data = res.json()

        if not data.get("success"):
            raise HTTPException(
                status_code=400,
                detail="La vérification CAPTCHA a échoué. Veuillez réessayer.",
            )

        return True

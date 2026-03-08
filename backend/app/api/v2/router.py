"""
PresenceOS - API v2 Router
"""
from fastapi import APIRouter

from app.api.v2.endpoints import social, ilyas, onboarding, engage, voice, ab_testing, breakout, dish_recognition, video

api_v2_router = APIRouter()

# Social Publishing (Blotato + Upload-Post fallback)
api_v2_router.include_router(social.router, prefix="/social", tags=["Social v2"])

# Ilyas — CM AI Agent
api_v2_router.include_router(ilyas.router, prefix="/ilyas", tags=["Ilyas"])

# Onboarding — Ilyas Business DNA (Sprint 4)
api_v2_router.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding"])

# Engage — Comments, DMs, Unified Inbox (Sprint 5)
api_v2_router.include_router(engage.router, prefix="/engage", tags=["Engage"])

# Voice — Whisper audio transcription (Sprint 7)
api_v2_router.include_router(voice.router, prefix="/voice", tags=["Voice"])

# A/B Testing — Caption variant testing (Sprint 8)
api_v2_router.include_router(ab_testing.router, prefix="/ab", tags=["A/B Testing"])

# Breakout — 3D frame-break video effect
api_v2_router.include_router(breakout.router, prefix="/breakout", tags=["Breakout"])

# Dish Recognition — Gemini Vision auto-identification
api_v2_router.include_router(dish_recognition.router, prefix="/dish", tags=["Dish Recognition"])

# Video Assets — Save + Publish generated videos (Sprint B3)
api_v2_router.include_router(video.router, prefix="/video", tags=["Video Assets"])

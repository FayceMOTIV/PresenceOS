"""
PresenceOS - API v2 Router
"""
from fastapi import APIRouter

from app.api.v2.endpoints import social, ilyas, onboarding, engage, voice, ab_testing, breakout, dish_recognition, video, images, ai_video, social_publish, video_templates, me, brands

api_v2_router = APIRouter()

# Me — Current user info + brands (bridge Firebase → PostgreSQL)
api_v2_router.include_router(me.router, prefix="/me", tags=["Me"])

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

# Image Generation — Gemini Image (replaces DALL-E 3)
api_v2_router.include_router(images.router, prefix="/images", tags=["Images"])

# AI Video Generation — Kling 2.6 Pro / Wan 2.6 via fal.ai
api_v2_router.include_router(ai_video.router, prefix="/ai-video", tags=["AI Video"])

# Social Publishing — Postiz self-hosted scheduler
api_v2_router.include_router(social_publish.router, prefix="/publish", tags=["Social Publish"])

# Video Templates — Breakout V4 + Cinematic Food
api_v2_router.include_router(video_templates.router, prefix="/templates", tags=["Video Templates"])

# Brands — Niche Engine (Sprint Niche)
api_v2_router.include_router(brands.router, prefix="/brands", tags=["Brands v2"])

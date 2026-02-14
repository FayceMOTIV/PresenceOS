"""
PresenceOS - API v1 Router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    workspaces,
    brands,
    knowledge,
    ideas,
    drafts,
    connectors,
    posts,
    metrics,
    ai,
    media,
    agents,
    autopilot,
    media_library,
    onboarding,
    chat,
    photos,
    scheduling,
    repurpose,
    gbp,
    analytics,
    reputation,
    trends,
    competitor,
    hyperlocal,
    interview,
    content_analysis,
)

api_router = APIRouter()

# Authentication
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Users
api_router.include_router(users.router, prefix="/users", tags=["Users"])

# Workspaces
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["Workspaces"])

# Brands
api_router.include_router(brands.router, prefix="/brands", tags=["Brands"])

# Knowledge Base
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge"])

# Content Ideas
api_router.include_router(ideas.router, prefix="/ideas", tags=["Ideas"])

# Content Drafts
api_router.include_router(drafts.router, prefix="/drafts", tags=["Drafts"])

# Social Connectors
api_router.include_router(connectors.router, prefix="/connectors", tags=["Connectors"])

# Scheduled Posts
api_router.include_router(posts.router, prefix="/posts", tags=["Posts"])

# Metrics & Analytics
api_router.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])

# AI Generation
api_router.include_router(ai.router, prefix="/ai", tags=["AI"])

# Media Storage
api_router.include_router(media.router, prefix="/media", tags=["Media"])

# AI Agents
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])

# Autopilot
api_router.include_router(autopilot.router, prefix="/autopilot", tags=["Autopilot"])

# Media Library (Sprint 9B)
api_router.include_router(media_library.router, prefix="/media-library", tags=["Media Library"])

# Onboarding Intelligent (Phase 2)
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding"])

# Content Studio Chat
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])

# Photo Enhancement (Feature 2)
api_router.include_router(photos.router, prefix="/photos", tags=["Photos"])

# Smart Scheduling (Feature 1)
api_router.include_router(scheduling.router, prefix="/scheduling", tags=["Scheduling"])

# Content Repurposing (Feature 4)
api_router.include_router(repurpose.router, prefix="/repurpose", tags=["Repurpose"])

# Google Business Profile Autopublish (Feature 7)
api_router.include_router(gbp.router, prefix="/gbp", tags=["GBP"])

# Analytics Dashboard (Feature 9)
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

# Reputation Manager (Feature 3)
api_router.include_router(reputation.router, prefix="/reputation", tags=["Reputation"])

# Trend Radar (Feature 8)
api_router.include_router(trends.router, prefix="/trends", tags=["Trends"])

# Competitor Intelligence (Feature 5)
api_router.include_router(competitor.router, prefix="/competitor", tags=["Competitor"])

# Hyperlocal Intelligence (Feature 10)
api_router.include_router(hyperlocal.router, prefix="/hyperlocal", tags=["Hyperlocal"])

# Brand Interview AI
api_router.include_router(interview.router, prefix="/interview", tags=["Brand Interview"])

# Content Analysis (Instagram tone extraction)
api_router.include_router(content_analysis.router, prefix="/content-analysis", tags=["Content Analysis"])

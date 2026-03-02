# CLAUDE.md — PresenceOS (RS3)

> Onboarding document for any AI agent working on this project.
> Last updated: 2026-02-27

---

## 1. What is PresenceOS?

PresenceOS (internal codename **RS3**) is a **full-stack AI-powered social media management platform for restaurants**. It automates content creation, publishing, community management, and analytics across Instagram, Facebook, TikTok, LinkedIn, and Google Business Profile.

The platform has **three codebases** in this monorepo:

| Codebase | Path | Stack | Purpose |
|----------|------|-------|---------|
| **Mobile** | `/mobile` | React Native / Expo SDK 54 / TypeScript | iOS & Android app (primary client) |
| **Backend** | `/backend` | FastAPI / Python 3.11 / PostgreSQL + pgvector | API server, AI pipelines, workers |
| **Frontend** | `/frontend` | Next.js 14 / React 18 / Tailwind / Radix UI | Web dashboard (secondary client) |

**Owner:** Faical Kriouar (FayceMOTIV)
**GitHub:** `https://github.com/FayceMOTIV/PresenceOS.git` — branch: `main`

---

## 2. Key Identifiers & Credentials

```
# Production API
API_URL        = https://rs3-api-production.up.railway.app/api/v1

# Test User (auto-login in mobile app)
EMAIL          = test@presenceos.dev
PASSWORD       = Test123pass
USER_ID        = 08842961-7e93-431b-a34d-f5dc82353bdf
BRAND_ID       = 4c4f6d5b-cef8-4f90-b4d7-ce611d1ffcfc

# Dev Mode
DEV_API_URL    = http://192.168.10.114:8000/api/v1
DEV_TOKEN      = Bearer dev-token-presenceos

# Apple / iOS
BUNDLE_ID      = fr.appysolution.rs3
APPLE_TEAM_ID  = 5ZR87TPM89  (2k (ARA))
EAS_PROJECT_ID = 986daedd-7a05-4d22-82bd-ab76a2a8234c
EAS_OWNER      = fayce
SCHEME         = rs3

# Android
PACKAGE        = fr.appysolution.rs3
```

---

## 3. Mobile App (`/mobile`)

### 3.1 Tech Stack

- **Expo SDK 54** with Continuous Native Generation (CNG) — no committed `ios/` or `android/` dirs
- **React Native 0.81.5**, React 19.1, TypeScript 5.9
- **React Navigation 7** — bottom tabs + native stacks
- **Expo modules:** camera, image-picker, av, file-system, secure-store, web-browser, notifications, linear-gradient, linking
- **No axios** — custom fetch wrapper in `src/lib/api.ts` (Hermes-compatible)

### 3.2 Project Structure

```
mobile/
├── App.tsx                          # Entry point (auth, BrandContext, push notification handler, navigationRef)
├── app.json                         # Expo config
├── eas.json                         # EAS Build profiles
├── package.json
├── tsconfig.json
├── babel.config.js
├── assets/                          # icon.png, splash.png, adaptive-icon.png
├── build/                           # Build artifacts (gitignored)
│   ├── RS3.tar.gz                   # Simulator build (19.2 MB)
│   └── ipa/RS3.ipa                  # Device IPA (9.6 MB, Development signed)
└── src/
    ├── components/
    │   ├── ui/Card.tsx              # Glassmorphism card
    │   ├── ui/Badge.tsx             # Status badge (pending/approved/published/rejected)
    │   ├── AssetCard.tsx            # 3-column grid thumbnail
    │   ├── AssetDetailSheet.tsx     # Full-screen asset modal
    │   ├── BrandSwitcher.tsx        # Multi-brand switcher component
    │   ├── DishCard.tsx             # Horizontal dish item
    │   ├── ProposalCard.tsx         # Proposal preview with confidence score
    │   ├── EmptyStateCard.tsx       # Empty state with CTA
    │   ├── FAB.tsx                  # Floating action button
    │   └── KBCompletenessBar.tsx    # Knowledge base score bar (0-100%)
    ├── constants/
    │   ├── colors.ts                # Design system: violet (#7C5CBF) + amber (#F4A261)
    │   └── i18n.ts                  # 150+ French UI strings
    ├── contexts/
    │   └── BrandContext.ts          # AuthContext + BrandContext (multi-brand)
    ├── hooks/
    │   ├── useAuth.ts               # JWT auth with SecureStore
    │   ├── useBrand.ts              # Multi-brand switching
    │   └── useCMChat.ts             # CM Chat conversation hook
    ├── lib/
    │   ├── api.ts                   # Fetch-based API client (11 modules)
    │   ├── deepLinking.ts           # rs3:// deep linking config (React Navigation)
    │   └── pushNotifications.ts     # Expo push notifications setup
    ├── navigation/
    │   └── TabNavigator.tsx         # 5-tab bottom navigator
    ├── screens/
    │   ├── auth/LoginScreen.tsx
    │   ├── home/HomeScreen.tsx      # Dashboard: KB score, brief, recent proposals
    │   ├── brief/BriefDuJourScreen.tsx  # Daily morning brief → AI post generation
    │   ├── social/SocialAccountsScreen.tsx  # Per-platform OAuth via Upload-Post
    │   ├── files/
    │   │   ├── FileHubScreen.tsx    # Tabbed media hub
    │   │   ├── AssetUploadScreen.tsx
    │   │   ├── DishFormScreen.tsx
    │   │   ├── ScanMenuScreen.tsx   # OCR menu scanning
    │   │   └── tabs/ (MediaLibraryTab, MenuTab, RequestsTab)
    │   ├── proposals/
    │   │   ├── ProposalsListScreen.tsx  # AI proposals with status filters
    │   │   └── ProposalDetailScreen.tsx
    │   ├── video/
    │   │   ├── VideoStudioScreen.tsx    # AI video generation (fal.ai Kling 3.0)
    │   │   └── VideoPlansScreen.tsx     # Credit plans
    │   ├── brain/
    │   │   └── BrainDashboardScreen.tsx # Brand Brain dashboard (KB + visual brain)
    │   ├── analytics/
    │   │   └── AnalyticsScreen.tsx      # Analytics dashboard
    │   ├── validation/
    │   │   └── ValidationInboxScreen.tsx # Content validation inbox
    │   ├── cm/
    │   │   └── CMChatScreen.tsx         # iMessage-style CM AI chat
    │   └── inbox/
    │       └── InboxScreen.tsx      # Google reviews + AI responses
    ├── stores/
    │   └── brandStore.ts            # Zustand brand state (multi-brand switching)
    └── types/
        ├── index.ts                 # 11+ TypeScript interfaces
        └── brain.ts                 # Brain-related types
```

### 3.3 Navigation (5 tabs)

```
TabNavigator (bottom tabs)
├── Home → HomeScreen, BriefDuJourScreen, SocialAccountsScreen, BrainDashboardScreen, AnalyticsScreen, ValidationInboxScreen
├── Files → FileHubScreen, AssetUploadScreen, DishFormScreen, ScanMenuScreen
├── Proposals → ProposalsListScreen, ProposalDetailScreen
├── Video → VideoStudioScreen, VideoPlansScreen (modal)
└── Inbox → InboxScreen, CMChatScreen
```

### 3.3.1 Deep Linking (`rs3://`)

```
rs3://                    → HomeMain
rs3://brief               → Brief
rs3://social-callback     → SocialAccounts (OAuth redirect)
rs3://brain               → BrainDashboard
rs3://analytics           → Analytics
rs3://validation          → ValidationInbox
rs3://files               → FileHub
rs3://upload              → AssetUpload
rs3://scan                → ScanMenu
rs3://proposals           → ProposalsList
rs3://proposals/:id       → ProposalDetail
rs3://video               → VideoStudio
rs3://inbox               → InboxMain
rs3://cm-chat             → CMChat
```

### 3.3.2 Push Notifications

- **Expo Push** via `expo-notifications` (free tier, no key required for low volume)
- `App.tsx` uses `createNavigationContainerRef` for programmatic navigation from push taps
- Push tap on CM notification navigates to `Inbox > CMChat` with `sessionId` param
- Backend sends push via `https://exp.host/--/api/v2/push/send` (httpx)

### 3.4 API Client (`src/lib/api.ts`)

Custom fetch wrapper with 30s timeout, dev token bypass, FormData support. Modules:

| Module | Prefix | Purpose |
|--------|--------|---------|
| `authApi` | `/auth` | OAuth2 login |
| `contentApi` | `/content/{brandId}` | Dishes, content requests |
| `menuApi` | `/menu/{brandId}` | OCR scan & import |
| `proposalsApi` | `/proposals/{brandId}` | List, approve, reject, edit, regenerate |
| `briefApi` | `/brief/{brandId}` | Daily brief |
| `kbApi` | `/kb/{brandId}` | Knowledge base |
| `assetsApi` | `/media-library/brands/{brandId}` | Media upload, improve, generate |
| `socialApi` | `/social` | Upload-Post social account linking |
| `videoApi` | `/video` | AI video generation + credits |
| `cmApi` | `/cm` | Community manager inbox + CM Chat |

### 3.5 Design System

- **Background:** `#F8F7FF` (lavender white), cards on `#FFFFFF`
- **Primary:** `#7C5CBF` (violet), **Secondary:** `#F4A261` (amber)
- **Text:** `#1A1033` primary, `#5A5272` secondary, `#9B97AE` muted
- **Gradients:** hero `[#7C5CBF → #F4A261]`, violet `[#7C5CBF → #5B3E9E]`
- **Status:** success `#10B981`, warning `#F59E0B`, danger `#EF4444`, info `#3B82F6`
- **UI style:** Light theme, Notion/Linear/Arc-inspired, glassmorphism cards

### 3.6 Build & Deploy

```bash
# Development
cd mobile && npx expo start          # Metro bundler (Ctrl+D for dev menu)

# iOS Simulator build (via EAS)
npx eas build --platform ios --profile preview-simulator --local

# iOS Device build (via xcodebuild — bypasses EAS credential issues)
npx expo prebuild --platform ios --clean
xcodebuild archive -workspace ios/RS3.xcworkspace -scheme RS3 \
  -configuration Release -archivePath build/RS3.xcarchive \
  -destination "generic/platform=iOS" CODE_SIGN_IDENTITY="Apple Development" \
  DEVELOPMENT_TEAM=5ZR87TPM89 CODE_SIGN_STYLE=Automatic
xcodebuild -exportArchive -archivePath build/RS3.xcarchive \
  -exportPath build/ipa -exportOptionsPlist /tmp/ExportOptions.plist
rm -rf ios/  # Clean up CNG output

# EAS Build (cloud)
npx eas build --platform ios --profile preview
npx eas build --platform ios --profile production
```

**Known issue:** EAS `--non-interactive` fails for iOS device builds because Distribution Certificate is not pre-configured. Use xcodebuild directly or run `npx eas credentials` interactively first.

### 3.7 .gitignore

```
.expo/
ios/          # CNG — generated on demand
android/      # CNG — generated on demand
node_modules/
*.tsbuildinfo
```

---

## 4. Backend (`/backend`)

### 4.1 Tech Stack

- **FastAPI** (async Python 3.11), **Uvicorn**
- **SQLAlchemy 2.0** (async) + **asyncpg** + **PostgreSQL 16** with **pgvector**
- **Redis** — cache + Celery broker
- **Celery** — background workers + beat scheduler
- **MinIO** — S3-compatible object storage
- **AI providers:** OpenAI (GPT-4), Anthropic (Claude Sonnet), fal.ai (image/video)
- **CrewAI** — multi-agent AI framework for content generation
- **Docker** — containerized deployment on **Railway**

### 4.2 Project Structure (163 Python files)

```
backend/
├── app/
│   ├── main.py                  # FastAPI app, lifespan, CORS, middleware
│   ├── agents/                  # CrewAI agent framework
│   │   ├── agents/ (analyst, critic, researcher, strategist, writer)
│   │   ├── crews/ (content_crew, onboarding_crew, trends_crew)
│   │   ├── tasks/ (content_tasks, onboarding_tasks, trend_tasks)
│   │   └── tools/ (brand_knowledge, metrics_reader, trend_scanner, web_scraper)
│   ├── ai/
│   │   ├── market_analyzer.py   # GPT-4 market analysis
│   │   └── photo_studio.py      # DALL-E 3 photo generation
│   ├── api/v1/
│   │   ├── deps.py              # Dependency injection (CurrentUser, DBSession, get_brand)
│   │   ├── router.py            # 41 router includes
│   │   └── endpoints/ (44 files — see full list below)
│   ├── connectors/              # Social media adapters
│   │   ├── upload_post.py       # Upload-Post API (multi-platform OAuth)
│   │   ├── meta.py, tiktok.py, linkedin.py
│   │   └── base.py, factory.py
│   ├── core/
│   │   ├── config.py            # Pydantic settings (env vars)
│   │   ├── database.py          # Async SQLAlchemy engine
│   │   ├── security.py          # JWT, bcrypt, encryption
│   │   ├── resilience.py        # Circuit breaker, retry logic
│   │   └── degraded_middleware.py  # Runs without PostgreSQL
│   ├── middleware/
│   │   ├── rate_limit.py        # slowapi rate limiter
│   │   └── security_headers.py
│   ├── models/ (16 files)
│   │   ├── user.py              # User, Workspace, WorkspaceMember
│   │   ├── brand.py             # Brand (restaurant profile, expo_push_token)
│   │   ├── content.py           # Content items, Platform enum
│   │   ├── media.py             # MediaAsset (photos, videos)
│   │   ├── ai_proposal.py       # AI-generated social posts (brain_context JSONB)
│   │   ├── daily_brief.py       # Morning brief
│   │   ├── compiled_kb.py       # Knowledge base compilation
│   │   ├── cm_interaction.py    # Google reviews, comments
│   │   ├── cm_session.py        # CM Chat sessions + messages (iMessage-style)
│   │   ├── dish.py              # Menu items
│   │   ├── video_credits.py     # Video generation quota
│   │   ├── publishing.py        # Publishing config per platform
│   │   ├── autopilot.py         # Autopilot settings
│   │   └── audit.py             # GDPR audit log
│   ├── schemas/ (Pydantic request/response models)
│   ├── services/ (40 files — business logic)
│   ├── workers/
│   │   ├── celery_app.py        # Celery config + 15 periodic tasks
│   │   ├── tasks.py             # Publishing, metrics, ideas, tokens, autopilot, GMB
│   │   ├── cm_tasks.py          # Google reviews polling
│   │   ├── content_tasks.py     # Content pipeline tasks
│   │   ├── brain_tasks.py       # Weekly text + visual brain reflections
│   │   ├── orchestrator_tasks.py # Autopilot orchestration, trends, weekly planning, gap check
│   │   └── proactive_cm_tasks.py # Monday 8 AM proactive CM content generation + push
│   ├── prompts/caption_generator.py
│   └── utils/ (captcha, file_validation)
├── alembic/                     # Database migrations (8 versions)
├── tests/ (14 test files)
├── Dockerfile
├── requirements.txt
└── .env.example
```

### 4.3 API Endpoints (41 route groups)

All routes are prefixed with `/api/v1`.

| Prefix | File | Tags | Purpose |
|--------|------|------|---------|
| `/auth` | auth.py | Authentication | Login, register, tokens |
| `/users` | users.py | Users | Profile management |
| `/workspaces` | workspaces.py | Workspaces | Multi-workspace CRUD |
| `/brands` | brands.py | Brands | Brand CRUD |
| `/knowledge` | knowledge.py | Knowledge | Knowledge items |
| `/ideas` | ideas.py | Ideas | Content idea generation |
| `/drafts` | drafts.py | Drafts | Draft management |
| `/connectors` | connectors.py | Connectors | Social media connections |
| `/posts` | posts.py | Posts | Scheduled posts |
| `/metrics` | metrics.py | Metrics | Analytics data |
| `/ai` | ai.py | AI | AI content generation |
| `/media` | media.py | Media | File upload/management |
| `/agents` | agents.py | Agents | CrewAI agent orchestration |
| `/autopilot` | autopilot.py | Autopilot | Auto content generation |
| `/media-library` | media_library.py | Media Library | Asset management |
| `/onboarding` | onboarding.py | Onboarding | Onboarding flow |
| `/chat` | chat.py | Chat | Content studio chat |
| `/photos` | photos.py | Photos | Photo enhancement |
| `/scheduling` | scheduling.py | Scheduling | Smart scheduling |
| `/repurpose` | repurpose.py | Repurpose | Content adaptation |
| `/gbp` | gbp.py | GBP | Google Business Profile |
| `/analytics` | analytics.py | Analytics | Dashboard analytics |
| `/reputation` | reputation.py | Reputation | Review management |
| `/trends` | trends.py | Trends | Trend radar |
| `/competitor` | competitor.py | Competitor | Competitor intelligence |
| `/hyperlocal` | hyperlocal.py | Hyperlocal | Local intelligence |
| `/interview` | interview.py | Brand Interview | Brand interview AI |
| `/content-analysis` | content_analysis.py | Content Analysis | Instagram tone extraction |
| `/gdpr` | gdpr.py | GDPR | RGPD compliance |
| `/studio` | studio_ai.py | AI Studio | DALL-E 3 photo generation |
| `/strategy` | strategy.py | Strategy | Market analysis |
| `/cm` | cm.py | Community Manager | Google reviews AI |
| `/content` | content_library.py | Content Library | Content library |
| `/menu` | menu_scan.py | Menu Scan | OCR menu scanning |
| `/proposals` | proposals.py | Proposals | AI proposal pipeline |
| `/brief` | brief.py | Daily Brief | Morning brief |
| `/kb` | kb.py | Knowledge Base | KB score + rebuild |
| `/social` | social_accounts.py | Social Accounts | Upload-Post integration |
| `/video` | video_generation.py | Video Generation | fal.ai Kling 3.0 |
| `/health` | health.py | Health | Health checks |
| — | fallback.py | — | Fallback endpoints |

### 4.4 Services (40 files)

**Core AI:**
- `ai_service.py` — Content generation (Claude/GPT-4)
- `prompt_builder.py` — Dynamic prompt construction with brand context + 23 niches
- `knowledge_base_service.py` — KB management + completeness scoring
- `embeddings.py` — Vector embeddings (pgvector)
- `proposal_generator.py` — AI proposal pipeline
- `calendar_intelligence.py` — Temporal awareness (French holidays, Islamic events, weather via Open-Meteo)
- `cm_performance_tracker.py` — Detects published CM proposals, feeds engagement data to BrandBrain
- `cm_chat_service.py` — Conversational CM AI (GPT-4o) with rich Brand Brain system prompt
- `visual_brain.py` — Learns visual preferences, rewrites image/video prompts

**Media & Content:**
- `asset_processor.py` — Media processing
- `photo_enhancer.py` — fal.ai image enhancement
- `ocr_service.py` — Menu OCR
- `vision.py` — Computer vision
- `content_library.py` — Content management
- `content_repurposer.py` — Multi-platform adaptation

**Video:**
- `video_studio.py` — Brain-aware video generation (fal.ai Kling 3.0, VisualBrain optimization)
- `video_producer.py` — Video production
- `ffmpeg_processor.py` — FFmpeg integration
- `remotion_renderer.py` — Remotion rendering
- `transcription.py` — Audio transcription
- `tts.py` — Text-to-speech
- `music_library.py` — Music assets
- `pexels.py` — Pexels API stock footage

**Social & Publishing:**
- `social_publisher.py` — Multi-platform publishing
- `publisher.py` — Core publishing logic
- `gbp_publisher.py` — Google Business Profile
- `smart_scheduler.py` — Optimal time scheduling

**Intelligence & Brain:**
- `cm_agent.py` — Community Manager AI
- `google_reviews.py` — Google reviews sync
- `reputation_manager.py` — Review management
- `competitor_intel.py` — Competitor analysis
- `trend_radar.py` — Trend detection
- `hyperlocal_intel.py` — Local intelligence
- `analytics_engine.py` — Analytics processing
- `engagement_scorer.py` — Post scoring

**Communication:**
- `whatsapp.py` + `telegram.py` — Messaging bots
- `conversation_engine.py` — Conversation state
- `webchat.py` — Web chat
- `brand_interview.py` — AI brand interview

**Infrastructure:**
- `storage.py` — S3/MinIO

### 4.5 Celery Workers (15 periodic tasks)

| Task | Schedule | Purpose |
|------|----------|---------|
| `check-scheduled-posts` | Every 1 min | Publish due posts |
| `sync-all-metrics` | Every 1 hour | Sync analytics |
| `generate-daily-ideas` | 6:00 AM UTC | Daily idea generation |
| `refresh-expiring-tokens` | 3:00 AM UTC | Refresh OAuth tokens |
| `autopilot-daily-generate` | 7:00 AM UTC | Autopilot content |
| `autopilot-check-auto-publish` | Every 15 min | Auto-publish check |
| `poll-google-reviews` | Every 15 min | Sync Google reviews |
| `send-daily-brief-notif` | 7:00 AM UTC (8 AM Paris) | Brief notifications |
| `brain-weekly-reflection` | Sun 6:00 AM UTC | BrandBrain text reflection |
| `brain-weekly-visual-reflection` | Sun 7:00 AM UTC | VisualBrain reflection |
| `orchestrator-daily-generate` | 8:00 AM UTC | Orchestrator daily content |
| `orchestrator-check-publish` | Every 10 min | Orchestrator auto-publish |
| `detect-trends-daily` | 6:30 AM UTC | Trend detection |
| `orchestrator-weekly-planning` | Sun 20:00 UTC | Weekly content planning |
| `orchestrator-gap-check` | 8:30 AM UTC | Calendar gap detection |
| `gmb-weekly-post` | Mon 9:00 AM UTC | Google Business Profile post |
| `proactive-weekly-cm` | Mon 7:00 AM UTC (8 AM Paris) | Proactive CM content + push notification |

**Celery async pattern:** Workers use `asyncio.new_event_loop()` + `loop.run_until_complete(coro)` pattern (NOT `asyncio.run()` which fails in Celery). See `cm_tasks.py` and `proactive_cm_tasks.py` for reference. Each task creates its own DB session via `_make_session_maker()`.

### 4.6 Database Models (16)

`User`, `Workspace`, `WorkspaceMember`, `Brand`, `Content`, `MediaAsset`, `AIProposal`, `DailyBrief`, `CompiledKB`, `CMInteraction`, `CmSession`, `CmMessage`, `Dish`, `VideoCredits`, `PublishingConfig`, `AutopilotConfig`, `AuditLog`

### 4.7 Running Locally

```bash
# With Docker (recommended)
docker-compose up -d          # postgres, redis, minio, backend, celery, frontend

# Without Docker
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Celery worker + beat
celery -A app.workers.celery_app worker --loglevel=info
celery -A app.workers.celery_app beat --loglevel=info

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
```

### 4.8 Deployment

- **Platform:** Railway
- **Production URL:** `https://rs3-api-production.up.railway.app`
- **Docker image:** `python:3.11-slim` with ffmpeg, libmagic, libpq
- **Health check:** `GET /health` every 30s

---

## 5. Frontend (`/frontend`)

### 5.1 Tech Stack

- **Next.js 14** (App Router), React 18, TypeScript 5.3
- **Tailwind CSS** + **Radix UI** (shadcn/ui pattern) + Framer Motion
- **Zustand** — auth state management
- **TanStack React Query** — server state
- **TanStack React Table** — data tables
- **React Hook Form + Zod** — form validation
- **@dnd-kit** — drag & drop (planner)
- **Recharts** — analytics charts
- **next-auth** — authentication
- **PWA** — offline-capable with service worker

### 5.2 Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx           # Root layout (French, violet theme)
│   │   ├── page.tsx             # Landing page
│   │   ├── auth/ (login, register, forgot-password, reset-password)
│   │   ├── onboarding/page.tsx
│   │   ├── legal/ (privacy, terms)
│   │   └── (dashboard)/         # Protected routes
│   │       ├── layout.tsx       # Sidebar + brand switcher
│   │       ├── dashboard/       # Main dashboard
│   │       ├── accounts/        # Social accounts
│   │       ├── agents/          # AI agents
│   │       ├── analytics/       # Analytics
│   │       ├── autopilot/       # Autopilot config
│   │       ├── brain/           # Brand knowledge base
│   │       ├── create/          # Content creation studio
│   │       ├── ideas/           # Content ideas
│   │       ├── inbox/           # CM inbox
│   │       ├── media-library/   # Media assets
│   │       ├── photo-studio/    # AI photo generation
│   │       ├── planner/         # Calendar planner
│   │       ├── posts/           # Post management
│   │       ├── settings/        # User settings
│   │       ├── studio/          # AI studio
│   │       └── trends/          # Trend analysis
│   ├── components/ (26 categories, 100+ components)
│   ├── hooks/ (6 custom hooks)
│   ├── lib/
│   │   ├── api.ts               # Axios client (673 lines, 30+ modules)
│   │   ├── store.ts             # Zustand auth store
│   │   ├── utils.ts             # cn(), formatNumber(), etc.
│   │   ├── analytics.ts         # Mixpanel
│   │   ├── validation.ts        # Zod schemas
│   │   └── sanitize.ts          # DOMPurify
│   └── types/index.ts           # 50+ TypeScript interfaces
├── public/ (manifest, sw.js, icons)
├── next.config.js               # PWA, image CDN, API rewrite, security headers
├── tailwind.config.ts           # Custom colors, 20+ animations
└── package.json
```

### 5.3 Key Patterns

- **API proxy:** Next.js rewrites `/api/v1/*` to backend URL
- **Auth:** JWT in localStorage, Axios interceptor adds `Authorization` header
- **State:** Zustand for auth/workspace/brand, React Query for server data
- **UI:** shadcn/ui components (Radix primitives + Tailwind)
- **Localization:** French UI, French relative time formatting
- **PWA:** Service worker with NetworkFirst for API, CacheFirst for assets

---

## 6. Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    CLIENTS                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Mobile   │  │ Frontend │  │ WhatsApp/Telegram│  │
│  │ (Expo)   │  │ (Next.js)│  │ (Webhooks)       │  │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
└───────┼──────────────┼─────────────────┼────────────┘
        │              │                 │
        ▼              ▼                 ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend (Railway)                │
│  ┌─────────┐  ┌──────────┐  ┌────────────────────┐  │
│  │ 41 API  │  │ Auth/JWT │  │ Rate Limit/CORS    │  │
│  │ Routers │  │ Security │  │ Security Headers   │  │
│  └────┬────┘  └──────────┘  └────────────────────┘  │
│       │                                              │
│  ┌────▼────────────────────────────────────────┐     │
│  │           40 Business Services              │     │
│  │  AI, Publishing, Analytics, CM, Video...    │     │
│  └────┬───────────────────┬────────────────────┘     │
└───────┼───────────────────┼──────────────────────────┘
        │                   │
   ┌────▼────┐         ┌───▼────┐
   │ Celery  │         │External│
   │ Workers │         │  APIs  │
   │ + Beat  │         │        │
   └────┬────┘         └───┬────┘
        │                  │
   ┌────▼────┐    ┌────────▼────────────────────┐
   │  Redis  │    │ OpenAI, Anthropic, fal.ai   │
   └─────────┘    │ Upload-Post, Google, Pexels │
                  │ Firecrawl, Serper, Composio  │
   ┌──────────┐   └─────────────────────────────┘
   │PostgreSQL│
   │+pgvector │
   └──────────┘
   ┌──────────┐
   │  MinIO   │
   │(S3 store)│
   └──────────┘
```

---

## 7. Key Integrations

| Service | Purpose | Config Key |
|---------|---------|------------|
| **OpenAI** | GPT-4 content generation, DALL-E 3 images | `OPENAI_API_KEY` |
| **Anthropic** | Claude Sonnet alternative AI | `ANTHROPIC_API_KEY` |
| **fal.ai** | Image enhancement + Kling 3.0 video gen | `FAL_KEY` |
| **Upload-Post** | Multi-platform OAuth + social publishing | `UPLOAD_POST_API_KEY` |
| **Google** | Business Profile, reviews sync | `GOOGLE_CLIENT_ID/SECRET` |
| **Pexels** | Stock footage for video pipeline | (in services) |
| **Firecrawl** | Web scraping for trends | `FIRECRAWL_API_KEY` |
| **Serper** | Search API for research | `SERPER_API_KEY` |
| **Sentry** | Error monitoring | `SENTRY_DSN` |
| **Mixpanel** | Frontend analytics | (in frontend) |
| **Crisp** | Customer support chat | (in frontend) |
| **hCaptcha** | Bot protection | `HCAPTCHA_SECRET` |

---

## 8. Development Workflow

### Local Dev Setup

```bash
# 1. Start infrastructure
docker-compose up -d postgres redis minio

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Fill in API keys
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 3. Mobile
cd mobile
npm install
npx expo start  # Press i for iOS simulator, a for Android

# 4. Frontend (optional)
cd frontend
npm install
npm run dev  # Port 3001
```

### Mobile Development Notes

- **Dev mode:** Auto-login with test credentials, mock brand if API unreachable
- **Deep linking:** Scheme `rs3://` — OAuth callbacks + push notification navigation (see §3.3.1)
- **Social OAuth:** Opens `WebBrowser.openAuthSessionAsync` → Upload-Post → redirect `rs3://social-callback`
- **Hot reload:** Metro bundler (Expo), shake device or Ctrl+D for dev menu
- **TypeScript:** Strict mode, zero errors expected — verify with `npx tsc --noEmit`

### Backend Development Notes

- **Degraded mode:** Backend starts even without PostgreSQL (limited endpoints)
- **Health monitor:** Auto-recovery probes PostgreSQL/Redis every 30s
- **Structured logging:** `structlog` with JSON output
- **Testing:** `pytest` with async support — `pytest tests/`

---

## 9. Known Issues & Gotchas

1. **EAS iOS credentials:** Distribution Certificate not configured for `--non-interactive` builds. Either:
   - Run `npx eas credentials` interactively to set up
   - Or use xcodebuild directly (see §3.6)

2. **fal_client async:** Must use `fal_client.subscribe_async()` not `fal_client.subscribe()` — the sync version blocks the FastAPI event loop. Model mapping: `pro` for 5s/10s, `master` for 15s (`fal-ai/kling-video/v2.1/pro/text-to-video` or `fal-ai/kling-video/v2.1/master/text-to-video`).

3. **Upload-Post sync delay:** After OAuth connect, Upload-Post needs 1.5-3s to sync accounts. Mobile app has retry logic built in.

4. **Hermes + fetch:** No axios in mobile — Hermes engine has quirks with axios interceptors. Custom fetch wrapper handles everything.

5. **CNG mode:** Never commit `ios/` or `android/` dirs. They're generated on demand by `npx expo prebuild` and deleted after builds.

6. **Dev token bypass:** In `__DEV__` mode with no real token, API client sends `Bearer dev-token-presenceos`. Backend must accept this in dev.

7. **French UI only:** All mobile strings are in `src/constants/i18n.ts`. No i18n framework — just a constants file. Frontend is also French.

8. **Celery + asyncio:** NEVER use `asyncio.run()` in Celery tasks — it fails. Use `asyncio.new_event_loop()` + `loop.run_until_complete(coro)` pattern. See `cm_tasks.py` and `proactive_cm_tasks.py` for correct implementation. `brain_tasks.py` uses `asyncio.run()` which is buggy — do not follow that pattern.

9. **Push notification navigation:** `App.tsx` uses `createNavigationContainerRef` (NOT `useRef`) for programmatic navigation from push notification taps. The ref is exported at module level for use outside React components.

10. **Zustand in mobile:** `brandStore.ts` manages multi-brand state with Zustand. `BrandContext` in App.tsx bridges between Zustand store and React context for backwards compatibility.

---

## 10. Testing

### Backend
```bash
cd backend
pytest tests/                        # All tests
pytest tests/test_photo_studio.py    # Specific test
pytest --cov=app tests/              # With coverage
```

Test files (33): `test_agents`, `test_asset_processor`, `test_auth`, `test_autopilot`, `test_brands`, `test_calendar`, `test_calendar_intelligence`, `test_cm_agent`, `test_cm_chat_service`, `test_content_library`, `test_conversation_flow`, `test_daily_brief`, `test_ideas`, `test_knowledge_base`, `test_market_analyzer`, `test_media`, `test_media_library`, `test_ocr_service`, `test_photo_studio`, `test_posts`, `test_proposals`, `test_resilience`, `test_sprint7`, `test_sprint8`, `test_sprint9`, `test_sprint9b`, `test_sprint9c`, `test_sprint10`, `test_studio_ai_security`, `test_telegram`, `test_upload_post`, `test_webchat`

### Mobile
```bash
cd mobile
npx tsc --noEmit                     # TypeScript check (must be 0 errors)
```

### Frontend
```bash
cd frontend
npm run lint                         # ESLint
npx playwright test                  # E2E tests
```

---

## 11. Quick Reference — Common Tasks

| Task | Command |
|------|---------|
| Start mobile dev | `cd mobile && npx expo start` |
| Start backend | `cd backend && uvicorn app.main:app --reload --port 8000` |
| Start frontend | `cd frontend && npm run dev` |
| Run all infra | `docker-compose up -d` |
| iOS simulator build | `cd mobile && npx eas build -p ios --profile preview-simulator --local` |
| iOS device build | See §3.6 (xcodebuild method) |
| DB migration | `cd backend && alembic revision --autogenerate -m "msg" && alembic upgrade head` |
| TypeScript check | `cd mobile && npx tsc --noEmit` |
| Backend tests | `cd backend && pytest tests/` |
| Check API health | `curl https://rs3-api-production.up.railway.app/health` |

---

## 12. File Counts Summary

| Codebase | Files | Screens/Pages | Components | Services | Models | Endpoints |
|----------|-------|---------------|------------|----------|--------|-----------|
| Mobile | ~41 | 20 screens | 8 + 2 UI | 3 lib files (api.ts 11 modules) | 13+ types | — |
| Backend | 170+ | — | — | 44 services | 16 models | 41 route groups |
| Frontend | ~200 | 30+ pages | 100+ | 30+ API modules | 50+ types | — |

---

## 13. Environment Variables Reference

See `/backend/.env.example` for the complete list. Critical ones:

```env
# Required for backend to start
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/presenceos
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=<random-string>

# Required for AI features
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Required for social publishing
UPLOAD_POST_API_KEY=...

# Required for video generation
FAL_KEY=...

# Required for photo studio
# (uses OPENAI_API_KEY for DALL-E 3)

# Storage
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=presenceos
```

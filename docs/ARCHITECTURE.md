# PresenceOS Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                               │
│  ┌─────────────────┐                                                │
│  │   Next.js App   │  ← React + TypeScript + TailwindCSS            │
│  │   (Frontend)    │  ← TanStack Query for data fetching            │
│  └────────┬────────┘  ← Framer Motion for animations                │
│           │                                                          │
└───────────┼──────────────────────────────────────────────────────────┘
            │ HTTPS
            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           API LAYER                                  │
│  ┌─────────────────┐                                                │
│  │    FastAPI      │  ← REST API with OpenAPI docs                  │
│  │   (Backend)     │  ← JWT Authentication                          │
│  └────────┬────────┘  ← Pydantic validation                         │
│           │                                                          │
└───────────┼──────────────────────────────────────────────────────────┘
            │
   ┌────────┴────────┬────────────────┬─────────────────┐
   │                 │                │                 │
   ▼                 ▼                ▼                 ▼
┌──────────┐  ┌─────────────┐  ┌───────────┐  ┌──────────────┐
│PostgreSQL│  │   Redis     │  │   MinIO   │  │ AI Providers │
│+ pgvector│  │             │  │   (S3)    │  │ OpenAI/      │
│          │  │             │  │           │  │ Anthropic    │
└──────────┘  └──────┬──────┘  └───────────┘  └──────────────┘
                     │
                     ▼
              ┌──────────────┐
              │    Celery    │  ← Background tasks
              │   Workers    │  ← Scheduled publishing
              └──────────────┘  ← Metrics sync
```

## Components

### 1. Frontend (Next.js)

**Technology:** Next.js 14 (App Router), TypeScript, TailwindCSS

**Key Features:**
- Server-side rendering for SEO
- Client-side data fetching with TanStack Query
- Optimistic UI updates
- Dark mode premium design

**Directory Structure:**
```
frontend/src/
├── app/                 # Pages (App Router)
│   ├── auth/           # Login, Register
│   ├── dashboard/      # Main dashboard
│   ├── studio/         # Content creation
│   ├── planner/        # Calendar
│   └── settings/       # Configuration
├── components/
│   ├── ui/             # shadcn/ui components
│   ├── layout/         # Sidebar, Header
│   ├── dashboard/      # KPI cards, charts
│   └── studio/         # Content editor, preview
├── lib/                # API client, utilities
├── hooks/              # Custom React hooks
├── stores/             # Zustand stores
└── types/              # TypeScript definitions
```

### 2. Backend (FastAPI)

**Technology:** Python 3.11, FastAPI, SQLAlchemy, Pydantic v2

**Key Features:**
- Async/await for all I/O operations
- Automatic OpenAPI documentation
- Dependency injection for auth, db
- Structured logging with structlog

**Directory Structure:**
```
backend/app/
├── api/v1/
│   ├── endpoints/      # Route handlers
│   └── deps.py         # Dependencies (auth, db)
├── core/
│   ├── config.py       # Settings management
│   ├── security.py     # JWT, encryption
│   └── database.py     # SQLAlchemy setup
├── models/             # Database models
├── schemas/            # Pydantic schemas
├── services/           # Business logic
│   ├── ai_service.py   # AI generation
│   └── embeddings.py   # RAG embeddings
├── connectors/         # Social platform APIs
│   ├── meta.py         # Instagram/Facebook
│   ├── tiktok.py
│   └── linkedin.py
└── workers/            # Celery tasks
    ├── celery_app.py   # Celery config
    └── tasks.py        # Background jobs
```

### 3. Database (PostgreSQL + pgvector)

**Models:**
```
User
├── id (UUID)
├── email
├── hashed_password
└── oauth_provider

Workspace
├── id (UUID)
├── name, slug
└── billing_plan

Brand
├── id (UUID)
├── workspace_id (FK)
├── name, brand_type
├── target_persona (JSONB)
└── content_pillars (JSONB)

BrandVoice
├── brand_id (FK)
├── tone_* (sliders)
├── words_to_avoid
└── custom_instructions

KnowledgeItem
├── brand_id (FK)
├── knowledge_type
├── title, content
└── embedding (vector)

ContentIdea
├── brand_id (FK)
├── title, description
├── source, status
└── hooks (array)

ContentDraft
├── brand_id (FK)
├── platform
├── caption, hashtags
└── variants (relation)

SocialConnector
├── brand_id (FK)
├── platform
├── access_token_encrypted
└── status

ScheduledPost
├── brand_id (FK)
├── connector_id (FK)
├── scheduled_at
├── status
└── content_snapshot (JSONB)
```

### 4. Job Queue (Redis + Celery)

**Periodic Tasks:**
- `check_scheduled_posts` - Every minute, queue posts ready to publish
- `sync_all_metrics` - Hourly, fetch metrics from platforms
- `generate_daily_ideas` - Daily at 6 AM, generate content ideas
- `refresh_expiring_tokens` - Daily, refresh OAuth tokens

**On-demand Tasks:**
- `publish_post_task` - Publish a single post with retries
- `sync_connector_metrics` - Sync metrics for one connector

### 5. AI Services

**Provider Abstraction:**
```python
class AIService:
    def __init__(self, provider: str = "openai"):
        # Supports OpenAI and Anthropic

    async def generate_ideas(brand, count, pillars, ...)
    async def generate_draft(brand, platform, topic, ...)
    async def analyze_trends(brand, trends, ...)
    async def transcribe_audio(audio_content, filename)
```

**RAG Pipeline:**
1. Knowledge items are embedded using OpenAI text-embedding-3-small
2. Embeddings stored in PostgreSQL with pgvector
3. On draft generation, relevant knowledge is retrieved via cosine similarity
4. Knowledge context is injected into prompts

### 6. Social Connectors

**Interface:**
```python
class BaseConnector(ABC):
    def get_oauth_url(state) -> (url, state)
    async def exchange_code(code, redirect_uri) -> tokens
    async def refresh_token(refresh_token) -> tokens
    async def get_account_info(access_token) -> account
    async def publish(access_token, content, media) -> post_info
    async def get_post_metrics(access_token, post_id) -> metrics
```

**Implementations:**
- `MetaConnector` - Instagram/Facebook via Graph API
- `TikTokConnector` - TikTok Content Posting API
- `LinkedInConnector` - LinkedIn Posts API

## Data Flow

### Content Creation Flow

```
1. User enters topic in Studio
           │
           ▼
2. Frontend calls POST /ai/brands/{id}/drafts/generate
           │
           ▼
3. AIService retrieves brand context + voice
           │
           ▼
4. EmbeddingService finds relevant knowledge (RAG)
           │
           ▼
5. AIService generates draft + variants via OpenAI/Anthropic
           │
           ▼
6. Response returned with 3 variants (conservative/balanced/bold)
           │
           ▼
7. User selects variant and clicks "Schedule"
           │
           ▼
8. POST /posts/brands/{id} creates ScheduledPost
           │
           ▼
9. Celery beat detects scheduled time reached
           │
           ▼
10. publish_post_task executed via connector
           │
           ▼
11. Post published, status updated, metrics tracked
```

### OAuth Flow

```
1. User clicks "Connect Instagram"
           │
           ▼
2. GET /connectors/oauth/url → Returns Meta OAuth URL
           │
           ▼
3. User authorizes on Meta
           │
           ▼
4. Redirect to /api/auth/callback/meta with code
           │
           ▼
5. POST /connectors/oauth/callback exchanges code
           │
           ▼
6. MetaConnector stores encrypted tokens
           │
           ▼
7. SocialConnector created with status="connected"
```

## Security

### Authentication
- JWT tokens with 7-day expiry
- Passwords hashed with bcrypt
- OAuth tokens encrypted at rest (Fernet/AES-128)

### Authorization
- RBAC: Owner, Admin, Member roles
- Workspace-level isolation
- Brand-level access control

### Rate Limiting
- Platform quotas respected (e.g., 100 posts/day for Instagram)
- API rate limiting via middleware (future)

## Deployment

### Development
```bash
docker-compose up -d
```

### Production Checklist
1. Use managed PostgreSQL (e.g., Supabase, RDS)
2. Use managed Redis (e.g., Upstash, ElastiCache)
3. Use S3 for media storage
4. Configure Sentry for error tracking
5. Set up CI/CD with GitHub Actions
6. Use environment-specific secrets
7. Enable HTTPS with valid certificates
8. Configure CORS for your domain

### Scaling
- Backend: Multiple FastAPI instances behind load balancer
- Workers: Multiple Celery workers for parallel processing
- Database: Read replicas for heavy read workloads
- Cache: Redis for session and query caching

# Architecture Systeme PresenceOS

## Flux Principal

```
User Upload Photo
       |
       v
Frontend (Next.js 14)
       |
       v
Backend (FastAPI)
       |
       +---> S3 MinIO (stockage photo)
       |
       +---> OpenAI Vision API (analyse image)
       |
       +---> GPT-4 (generation 3 captions)
       |
       +---> Engagement Scorer (score 0-100)
       |
       v
Return to Frontend (3 suggestions + scores)
       |
       v
User Selects & Edits Caption
       |
       v
Schedule Post (Celery)
       |
       v
Upload-Post API / LinkedIn API
       |
       v
Instagram / Facebook / TikTok / LinkedIn
```

## Services Docker

| Service | Port | Role |
|---------|------|------|
| Backend (FastAPI) | 8000 | API REST, logique metier |
| Frontend (Next.js) | 3001 | Interface utilisateur |
| PostgreSQL | 5432 | Base de donnees + pgvector |
| Redis | 6379 | Cache + message broker |
| MinIO | 9000/9001 | Stockage S3 (photos, medias) |
| Celery Worker | - | Taches asynchrones (publish, metrics) |
| Celery Beat | - | Taches planifiees (scheduling, token refresh) |

## Base de Donnees

Tables principales :
- `users` : Comptes utilisateurs
- `workspaces` : Espaces de travail
- `brands` : Marques (avec voice, constraints, pillars)
- `social_connectors` : Connexions OAuth (Instagram, LinkedIn, etc.)
- `scheduled_posts` : Posts programmes
- `publish_jobs` : Tentatives de publication
- `content_drafts` : Brouillons de contenu
- `content_ideas` : Idees generees par IA
- `knowledge_items` : Base de connaissances par marque
- `metrics_snapshots` : Metriques de performance

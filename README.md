<div align="center">

# PresenceOS

**L'agent marketing IA qui transforme vos photos en campagnes sociales completes**

[![Docker](https://img.shields.io/badge/docker-ready-blue?logo=docker)](https://docker.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)](https://nextjs.org)
[![Python](https://img.shields.io/badge/python-3.11+-blue?logo=python)](https://python.org)
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue?logo=typescript)](https://typescriptlang.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Features](#features) &bull; [Architecture](#architecture) &bull; [Quick Start](#quick-start) &bull; [API](#api-endpoints) &bull; [Roadmap](#roadmap)

</div>

---

## Qu'est-ce que PresenceOS ?

PresenceOS est une plateforme SaaS de marketing automation qui permet aux entreprises (restaurants, e-commerce, coaching, immobilier, etc.) de **generer, optimiser et publier du contenu social en quelques clics**.

### Le probleme

Les entrepreneurs passent des heures a :
- Trouver quoi poster sur les reseaux sociaux
- Ecrire des captions engageantes
- Adapter le contenu pour chaque plateforme
- Trouver les bons hashtags
- Publier au bon moment

### La solution

**Upload une photo &rarr; Recois 3 variations de posts pretes a publier**

PresenceOS analyse votre photo, comprend votre marque, et genere automatiquement :
- 3 variations de captions (Gourmande, Promo, Story)
- Scores d'engagement predictifs (jusqu'a 92/100)
- Hashtags pertinents par secteur
- Suggestions d'emojis strategiques
- Meilleurs horaires de publication
- Adaptation multi-plateformes (Instagram, Facebook, LinkedIn, TikTok)

---

## Features

### IA Marketing de Pointe

- **Vision AI** : Analyse automatique des photos (produits, ambiance, couleurs)
- **3 Styles de Captions** :
  - **Gourmande** : Focus produit, sensoriel, desir
  - **Promo** : Urgence, offre limitee, FOMO
  - **Story** : Storytelling, emotion, authenticite
- **Scores d'Engagement** : Prediction 1-100 basee sur 15+ facteurs marketing
- **Regeneration Intelligente** :
  - Hashtags adaptes a votre secteur
  - Changement de ton (fun, premium, urgent)
  - Suggestions d'emojis pertinents

### Publication Automatisee

- **Multi-plateformes** : Instagram, Facebook, LinkedIn, TikTok
- **Scheduling Intelligent** : Detection automatique des meilleurs horaires
- **Publication en 1 clic** via Upload-Post API
- **Preview Multi-plateforme** : Voir le rendu exact sur chaque reseau

### Business Brain

- **Onboarding 5 Questions** : Capture l'identite de marque
- **Adaptation Automatique** : Ton de voix, valeurs, audience cible
- **6 Industries Supportees** : Restaurant, SaaS, E-commerce, Services, Coaching, Artisanat
- **Knowledge Base** : Se souvient des preferences et s'ameliore dans le temps

### Analytics & Insights

- Suivi des performances par post
- Engagement tracking (likes, comments, shares, reach)
- Suggestions basees sur ce qui marche

---

## Architecture

### Stack Technique

| Composant | Technologie |
|-----------|-------------|
| **Frontend** | Next.js 14, TypeScript, TailwindCSS, shadcn/ui, Framer Motion |
| **Backend** | FastAPI, SQLAlchemy async, Pydantic v2 |
| **Database** | PostgreSQL 16 + pgvector |
| **Queue** | Celery + Redis |
| **Storage** | MinIO (S3-compatible) |
| **AI** | OpenAI GPT-4 Vision + Anthropic Claude Sonnet 4.5 |
| **Publication** | Upload-Post API (Instagram, Facebook, TikTok) + LinkedIn natif |
| **Infrastructure** | Docker Compose (7 services) |

### 7 Services Docker

```
                    +-----------+
                    | Frontend  |  Next.js 14 (:3001)
                    |  (Web UI) |
                    +-----+-----+
                          |
                          | HTTP
                          v
                    +-----------+
                    |  Backend  |  FastAPI (:8000)
                    | (API REST)|
                    +-----+-----+
                          |
          +-------+-------+-------+-------+-------+
          |       |       |       |       |       |
          v       v       v       v       v       v
      +------+ +-----+ +-----+ +------+ +------+
      |Postgr| |Redis| |MinIO| |Celery| |Celery|
      |  SQL  | |     | | (S3)| |Worker| | Beat |
      +------+ +-----+ +-----+ +------+ +------+
```

---

## Quick Start

### Prerequis

- Docker & Docker Compose
- Node.js 18+
- Python 3.11+

### Installation

```bash
# 1. Cloner le repo
git clone https://github.com/FayceMOTIV/PresenceOS.git
cd PresenceOS

# 2. Configurer les variables d'environnement
cp .env.example .env
# Editer .env et ajouter :
#   OPENAI_API_KEY=sk-...
#   UPLOAD_POST_API_KEY=... (optionnel, pour publication)

# 3. Lancer l'infrastructure
docker compose up -d

# 4. Attendre que tous les services demarrent (~30 secondes)
docker compose ps

# 5. Acceder a l'application
open http://localhost:3001
```

### Verification

```bash
# Backend health
curl http://localhost:8000/health

# API docs (Swagger)
open http://localhost:8000/docs
```

---

## API Endpoints

### Captions IA

| Endpoint | Methode | Description |
|----------|---------|-------------|
| `/api/v1/ai/brands/{id}/photo/captions` | POST | Genere 3 variations de captions |
| `/api/v1/ai/brands/{id}/captions/regenerate-hashtags` | POST | Regenere des hashtags |
| `/api/v1/ai/brands/{id}/captions/change-tone` | POST | Change le ton (fun, premium, urgent) |
| `/api/v1/ai/brands/{id}/captions/suggest-emojis` | POST | Suggere des emojis pertinents |
| `/api/v1/ai/brands/{id}/captions/engagement-score` | POST | Calcule le score d'engagement |

### Publication

| Endpoint | Methode | Description |
|----------|---------|-------------|
| `/api/v1/posts/brands/{id}` | POST | Programmer un post |
| `/api/v1/connectors/oauth/url` | POST | URL OAuth pour connecter un reseau |
| `/api/v1/connectors/oauth/callback` | POST | Callback OAuth |
| `/api/v1/scheduling/optimal-times/{id}` | GET | Horaires optimaux |

### Brands & Content

| Endpoint | Methode | Description |
|----------|---------|-------------|
| `/api/v1/brands` | POST | Creer une marque |
| `/api/v1/brands/{id}/onboard` | POST | Onboarding IA (5 questions) |
| `/api/v1/ai/brands/{id}/ideas/generate` | POST | Generer des idees de contenu |
| `/api/v1/ai/brands/{id}/drafts/generate` | POST | Generer un brouillon |

Documentation complete : `http://localhost:8000/docs`

---

## Structure du Projet

```
presenceos/
|-- backend/                  # API FastAPI
|   |-- app/
|   |   |-- api/v1/endpoints/ # Endpoints REST (20+)
|   |   |-- models/           # SQLAlchemy models
|   |   |-- services/         # Business logic (AI, Vision, Publishing)
|   |   |-- prompts/          # Systeme de prompts IA
|   |   |-- connectors/       # Instagram, LinkedIn, TikTok, Facebook
|   |   +-- workers/          # Taches Celery (publish, metrics)
|   |-- tests/                # Tests pytest (390+)
|   +-- Dockerfile
|-- frontend/                 # Application Next.js
|   |-- src/
|   |   |-- app/              # Pages (App Router, 20 pages)
|   |   |-- components/       # Composants React
|   |   +-- hooks/            # Custom hooks
|   +-- Dockerfile
|-- docker-compose.yml        # Orchestration 7 services
|-- .env.example              # Variables d'environnement
+-- README.md
```

---

## Tests

```bash
# Backend (pytest)
cd backend && pytest -v

# Frontend build check
cd frontend && npx next build
```

---

## Roadmap

### v1.0 (Fevrier 2026) - Actuel

- [x] Upload photo & analyse vision
- [x] 3 variations de captions IA (gourmande/promo/story)
- [x] Scores d'engagement predictifs
- [x] Regeneration intelligente (hashtags, tone, emojis)
- [x] Publication Instagram/Facebook/TikTok via Upload-Post
- [x] Publication LinkedIn native
- [x] Brand onboarding (5 questions)
- [x] Docker 7 services
- [x] 20 pages frontend

### v1.1

- [ ] Calendrier de publications drag & drop
- [ ] Analytics dashboard
- [ ] Historique des posts publies
- [ ] Templates par industrie

### v2.0

- [ ] Generation video automatique
- [ ] WhatsApp/Telegram bot
- [ ] A/B Testing de captions
- [ ] Competitor Intelligence
- [ ] Trends Radar

---

## Contribution

1. Fork le projet
2. Cree une branche (`git checkout -b feature/ma-feature`)
3. Commit (`git commit -m 'feat: ma feature'`)
4. Push (`git push origin feature/ma-feature`)
5. Ouvre une Pull Request

---

## License

MIT License - voir [LICENSE](LICENSE) pour plus de details.

---

Construit par [Faical Kriouar](https://github.com/FayceMOTIV)

**Technologies** : [OpenAI](https://openai.com) | [Anthropic](https://anthropic.com) | [Upload-Post](https://upload-post.com) | [FastAPI](https://fastapi.tiangolo.com) | [Next.js](https://nextjs.org)

# Changelog

Toutes les modifications notables de ce projet seront documentees dans ce fichier.

Format base sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).

## [1.0.0] - 2026-02-12

### Ajoute

- **Systeme de Captions IA v2.0**
  - Generation de 3 variations (Gourmande, Promo, Story)
  - Scores d'engagement predictifs (1-100, 15+ criteres)
  - Regeneration intelligente (hashtags, tone, emojis)
  - Prompts marketing premium par industrie (restaurant, SaaS, e-commerce, coaching, artisanat, services)

- **Infrastructure Complete**
  - 7 services Docker (Backend, Frontend, PostgreSQL, Redis, Celery Worker, Celery Beat, MinIO)
  - Backend FastAPI avec 20+ endpoints
  - Frontend Next.js 14 avec 20 pages
  - Base de donnees PostgreSQL + pgvector
  - Queue Celery pour taches asynchrones
  - Stockage S3 MinIO

- **Features Marketing**
  - Upload photo & analyse vision (OpenAI GPT-4 Vision)
  - Business Brain (contexte marque, ton, valeurs)
  - Publication multi-plateformes (Instagram, Facebook, LinkedIn, TikTok)
  - Connecteurs OAuth (Meta, LinkedIn, TikTok) + Upload-Post API
  - Scheduling intelligent avec horaires optimaux
  - Preview avant publication

- **Brand Onboarding**
  - Wizard 5 questions (nom, secteur, ton, audience, objectifs)
  - Adaptation automatique des prompts IA
  - Brand voice configuration

- **UX Frontend**
  - Interface Content Studio dark theme
  - Animations Framer Motion
  - Drag & drop upload
  - Edition inline (caption, hashtags, tone, emojis)
  - Preview multi-plateforme
  - Score d'engagement visuel (gauge)

### Technique

- FastAPI 0.104+ avec async/await
- Next.js 14 App Router + TypeScript
- SQLAlchemy 2.0 async + Pydantic v2
- Docker Compose orchestration
- 390+ tests backend passing
- E2E flow teste : upload -> vision -> captions -> publication

## [Unreleased]

### Prevu pour v1.1

- Calendrier de publications drag & drop
- Analytics dashboard
- Historique des posts publies
- Templates par industrie

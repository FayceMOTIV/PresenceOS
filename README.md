# PresenceOS

Agent Marketing IA pour entrepreneurs - SaaS qui planifie, genere et publie du contenu adapte sur les reseaux sociaux.

## Description

PresenceOS est une plateforme SaaS alimentee par l'IA qui aide les entrepreneurs a gerer leur presence sur les reseaux sociaux. Elle planifie, genere et publie automatiquement du contenu adapte a chaque plateforme sociale.

## Stack Technique

- **Frontend**: Next.js 14, React 18, Tailwind CSS, shadcn/ui, Framer Motion
- **Backend**: FastAPI, Python 3.11+
- **Base de donnees**: PostgreSQL 16 avec pgvector
- **Cache & Files**: Redis 7, Celery
- **Stockage**: MinIO (S3-compatible)
- **IA**: OpenAI, Anthropic Claude
- **Infrastructure**: Docker, Docker Compose

## Architecture

```
presenceos/
├── frontend/          # Application Next.js 14
├── backend/           # API FastAPI
│   ├── app/
│   │   ├── api/       # Endpoints API
│   │   ├── models/    # Modeles SQLAlchemy
│   │   ├── schemas/   # Schemas Pydantic
│   │   ├── services/  # Logique metier
│   │   ├── workers/   # Taches Celery
│   │   └── core/      # Configuration & auth
│   ├── alembic/       # Migrations DB
│   ├── scripts/       # Scripts utilitaires
│   └── tests/         # Tests
└── docker-compose.yml # Orchestration services
```

## Demarrage Rapide

### Prerequis

- Docker & Docker Compose
- Git

### Installation

1. Cloner le depot:
```bash
git clone <repository-url>
cd presenceos
```

2. Demarrer tous les services:
```bash
docker-compose up -d
```

Cela demarre automatiquement:
- PostgreSQL (port 5432)
- Redis (port 6379)
- MinIO (ports 9000, 9001)
- Backend FastAPI (port 8000)
- Celery Worker
- Celery Beat
- Frontend Next.js (port 3001)

3. Initialiser la base de donnees (premiere fois):
```bash
docker exec -it presenceos-backend alembic upgrade head
docker exec -it presenceos-backend python scripts/seed.py
```

### URLs d'acces

- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8000
- **Documentation API**: http://localhost:8000/docs
- **Console MinIO**: http://localhost:9001

### Identifiants Demo

- **Email**: demo@presenceos.com
- **Mot de passe**: Demo123!

### Identifiants MinIO

- **Username**: minioadmin
- **Password**: minioadmin

## Services

### Frontend (Next.js)
Application web moderne avec interface utilisateur reactive.

### Backend (FastAPI)
API REST asynchrone avec documentation Swagger automatique.

### PostgreSQL + pgvector
Base de donnees avec support des vecteurs pour les embeddings IA.

### Redis
Cache et broker de messages pour Celery.

### MinIO
Stockage S3-compatible pour les medias (images, videos).

### Celery Worker
Traitement asynchrone des taches (generation de contenu, publication).

### Celery Beat
Planificateur de taches periodiques.

## Developpement Local

### Sans Docker

Voir les README specifiques:
- [Backend README](/Users/faicalkriouar/presenceos/backend/README.md)
- [Frontend README](/Users/faicalkriouar/presenceos/frontend/README.md)

### Commandes Docker Utiles

```bash
# Demarrer les services
docker-compose up -d

# Arreter les services
docker-compose down

# Voir les logs
docker-compose logs -f [service-name]

# Reconstruire les images
docker-compose build

# Reinitialiser completement
docker-compose down -v
docker-compose up -d --build
```

## Variables d'Environnement

Les variables d'environnement sont configurees dans `docker-compose.yml` pour le developpement.

Pour la production, configurez:
- `DATABASE_URL`: URL PostgreSQL
- `REDIS_URL`: URL Redis
- `S3_ENDPOINT_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`: Configuration S3/MinIO
- `OPENAI_API_KEY`: Cle API OpenAI
- `ANTHROPIC_API_KEY`: Cle API Anthropic

## Tests

```bash
# Backend
docker exec -it presenceos-backend pytest tests/ -v

# Frontend
cd frontend
npm test
```

## Documentation

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **API Redoc**: http://localhost:8000/redoc

## Structure des Pages

- **Landing**: Page d'accueil marketing
- **Auth**: Inscription / Connexion
- **Dashboard**: Vue d'ensemble
- **Studio**: Creation de contenu
- **Planner**: Calendrier de publication
- **Ideas**: Generateur d'idees
- **Analytics**: Statistiques
- **Settings**: Parametres
- **Brain**: Base de connaissances IA
- **Trends**: Tendances et insights

## Support

Pour toute question ou probleme, veuillez ouvrir une issue sur le depot GitHub.

## Licence

Proprietary - Tous droits reserves

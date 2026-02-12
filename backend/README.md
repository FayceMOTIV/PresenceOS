# PresenceOS Backend

API FastAPI pour la plateforme PresenceOS - Agent Marketing IA pour entrepreneurs.

## Technologies

- **Framework**: FastAPI 0.115+
- **Python**: 3.11+
- **Base de donnees**: PostgreSQL 16 + pgvector
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Cache**: Redis 7
- **Task Queue**: Celery
- **Stockage**: MinIO (S3-compatible)
- **IA**: OpenAI, Anthropic Claude
- **Tests**: pytest, pytest-asyncio

## Structure du Projet

```
backend/
├── app/
│   ├── main.py              # Point d'entree FastAPI
│   ├── api/                 # Endpoints API
│   │   ├── auth.py          # Authentification
│   │   ├── users.py         # Gestion utilisateurs
│   │   ├── brands.py        # Gestion marques
│   │   ├── posts.py         # Publications
│   │   └── ...
│   ├── models/              # Modeles SQLAlchemy
│   │   ├── user.py
│   │   ├── brand.py
│   │   ├── post.py
│   │   └── ...
│   ├── schemas/             # Schemas Pydantic
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── brand.py
│   │   └── ...
│   ├── services/            # Logique metier
│   │   ├── auth_service.py
│   │   ├── ai_service.py
│   │   ├── content_service.py
│   │   └── ...
│   ├── workers/             # Taches Celery
│   │   ├── celery_app.py
│   │   └── tasks.py
│   ├── connectors/          # Connecteurs reseaux sociaux
│   │   ├── facebook.py
│   │   ├── instagram.py
│   │   ├── linkedin.py
│   │   └── ...
│   └── core/                # Configuration
│       ├── config.py        # Variables d'environnement
│       ├── database.py      # Connexion DB
│       ├── security.py      # JWT, hashing
│       └── deps.py          # Dependances FastAPI
├── alembic/                 # Migrations DB
├── scripts/                 # Scripts utilitaires
│   └── seed.py              # Donnees de demo
├── tests/                   # Tests
├── requirements.txt         # Dependances
├── pytest.ini              # Config pytest
├── alembic.ini             # Config Alembic
└── Dockerfile              # Image Docker
```

## Installation & Configuration

### 1. Environnement Virtuel

```bash
# Creer l'environnement virtuel
python -m venv venv

# Activer (Linux/Mac)
source venv/bin/activate

# Activer (Windows)
venv\Scripts\activate
```

### 2. Installer les Dependances

```bash
pip install -r requirements.txt
```

### 3. Variables d'Environnement

Creer un fichier `.env` a la racine du backend:

```env
# Base de donnees
DATABASE_URL=postgresql+asyncpg://presenceos:presenceos@localhost:5432/presenceos
DATABASE_URL_SYNC=postgresql://presenceos:presenceos@localhost:5432/presenceos

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Stockage S3/MinIO
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=presenceos

# JWT
SECRET_KEY=votre-cle-secrete-tres-longue-et-aleatoire
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# IA
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# CORS
ALLOWED_ORIGINS=http://localhost:3001,http://localhost:3000

# Environment
ENVIRONMENT=development
```

### 4. Initialiser la Base de Donnees

```bash
# Appliquer les migrations
alembic upgrade head

# Charger les donnees de demo (optionnel)
python scripts/seed.py
```

## Lancement

### Mode Developpement

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Options:
- `--reload`: Rechargement automatique sur modification
- `--host 0.0.0.0`: Accessible depuis toutes les interfaces
- `--port 8000`: Port d'ecoute

### Lancer Celery Worker

Dans un terminal separe:

```bash
celery -A app.workers.celery_app worker --loglevel=info
```

### Lancer Celery Beat (Planificateur)

Dans un autre terminal:

```bash
celery -A app.workers.celery_app beat --loglevel=info
```

## Tests

### Executer Tous les Tests

```bash
pytest tests/ -v
```

### Tests avec Couverture

```bash
pytest tests/ --cov=app --cov-report=html
```

### Tests Specifiques

```bash
# Tests d'un module
pytest tests/test_auth.py -v

# Test specifique
pytest tests/test_auth.py::test_login -v

# Tests asynchrones
pytest tests/test_async.py -v --asyncio-mode=auto
```

## Migrations de Base de Donnees

### Creer une Nouvelle Migration

```bash
alembic revision --autogenerate -m "Description de la migration"
```

### Appliquer les Migrations

```bash
# Derniere version
alembic upgrade head

# Version specifique
alembic upgrade <revision_id>

# Voir l'historique
alembic history

# Version actuelle
alembic current
```

### Annuler une Migration

```bash
# Version precedente
alembic downgrade -1

# Version specifique
alembic downgrade <revision_id>
```

## API Documentation

Une fois le serveur lance:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Endpoints Principaux

### Authentification
- `POST /api/auth/register` - Inscription
- `POST /api/auth/login` - Connexion
- `POST /api/auth/refresh` - Rafraichir token
- `GET /api/auth/me` - Utilisateur actuel

### Utilisateurs
- `GET /api/users` - Liste utilisateurs
- `GET /api/users/{id}` - Details utilisateur
- `PUT /api/users/{id}` - Modifier utilisateur
- `DELETE /api/users/{id}` - Supprimer utilisateur

### Marques
- `GET /api/brands` - Liste marques
- `POST /api/brands` - Creer marque
- `GET /api/brands/{id}` - Details marque
- `PUT /api/brands/{id}` - Modifier marque
- `DELETE /api/brands/{id}` - Supprimer marque

### Publications
- `GET /api/posts` - Liste publications
- `POST /api/posts` - Creer publication
- `POST /api/posts/generate` - Generer avec IA
- `GET /api/posts/{id}` - Details publication
- `PUT /api/posts/{id}` - Modifier publication
- `DELETE /api/posts/{id}` - Supprimer publication
- `POST /api/posts/{id}/publish` - Publier

## Scripts Utilitaires

### Charger Donnees de Demo

```bash
python scripts/seed.py
```

Cree:
- Utilisateur demo (demo@presenceos.com / Demo123!)
- Marques exemples
- Publications exemples
- Idees de contenu

## Linting & Formatage

```bash
# Formatter avec Black
black app/ tests/

# Linter avec Ruff
ruff check app/ tests/

# Auto-fix
ruff check --fix app/ tests/
```

## Problemes Courants

### Port deja utilise
```bash
# Trouver le processus sur le port 8000
lsof -i :8000

# Tuer le processus
kill -9 <PID>
```

### Erreur de connexion PostgreSQL
Verifier que PostgreSQL est demarre:
```bash
docker-compose up -d postgres
```

### Erreur de connexion Redis
Verifier que Redis est demarre:
```bash
docker-compose up -d redis
```

### Erreurs de migration Alembic
```bash
# Reinitialiser
alembic downgrade base
alembic upgrade head
```

## Variables d'Environnement Principales

| Variable | Description | Defaut |
|----------|-------------|--------|
| `DATABASE_URL` | URL PostgreSQL async | - |
| `DATABASE_URL_SYNC` | URL PostgreSQL sync | - |
| `REDIS_URL` | URL Redis | redis://localhost:6379/0 |
| `SECRET_KEY` | Cle JWT | - |
| `OPENAI_API_KEY` | Cle API OpenAI | - |
| `ANTHROPIC_API_KEY` | Cle API Anthropic | - |
| `S3_ENDPOINT_URL` | URL MinIO/S3 | - |
| `S3_ACCESS_KEY` | Access Key S3 | - |
| `S3_SECRET_KEY` | Secret Key S3 | - |
| `ENVIRONMENT` | Environment | development |

## Performance

### Optimisations
- Connexions DB asynchrones (asyncpg)
- Pool de connexions configure
- Cache Redis pour requetes frequentes
- Indexation DB sur colonnes cles
- Compression des reponses API
- Rate limiting par IP/utilisateur

### Monitoring
- Logs structures avec structlog
- Metriques de performance
- Traces des requetes lentes

## Securite

- Hashing bcrypt pour mots de passe
- JWT pour authentification
- CORS configure
- Rate limiting
- Validation des entrees (Pydantic)
- Protection CSRF
- Headers de securite

## Contribution

1. Creer une branche feature
2. Ecrire les tests
3. Implementer les changements
4. Executer les tests et linters
5. Creer une Pull Request

## Support

Pour toute question, ouvrir une issue sur GitHub.

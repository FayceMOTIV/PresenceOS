# PresenceOS - Audit Complet

**Date** : 18 fevrier 2026
**Version auditee** : main@e47e0f83
**Auditeur** : Claude (Anthropic)
**Scope** : Backend (167 fichiers Python) + Frontend (234 fichiers TS/TSX) + Infrastructure

---

## Verdict Global : MOYEN

**Score qualite** : 6.4/10
**Production-ready** : Avec corrections (voir P0 ci-dessous)

### Resume en 3 points
1. **Architecture solide** : Separation claire backend/frontend, bonne utilisation d'async/await, modeles de donnees bien concuts, infrastructure Docker complete avec health checks
2. **Securite insuffisante pour la production** : Secrets exposes dans les .env, CORS trop permissif, salt statique pour le chiffrement, absence de validation d'inputs sur les endpoints AI, pas d'invalidation de tokens au logout
3. **Action prioritaire** : Corriger les 6 vulnerabilites critiques de securite avant tout deploiement, puis renforcer la validation des inputs et le rate limiting sur les endpoints AI couteux

---

## Scores Detailles

| Categorie | Score | Commentaire |
|-----------|-------|-------------|
| Architecture | 7.5/10 | Bien structuree, separation claire des concerns |
| Code Backend | 7.0/10 | Bonne qualite, manque de validation inputs |
| Code Frontend | 6.5/10 | Bon design, trop de `any` dans TypeScript |
| Securite | 5.0/10 | Plusieurs vulnerabilites critiques |
| Performance | 6.5/10 | Async correct, manque de caching |
| Tests | 6.0/10 | 454 tests mais 85.7% de pass rate |
| Infrastructure | 7.5/10 | Docker complet, bons health checks |
| Dette technique | 6.0/10 | TODO/FIXME nombreux, dead code present |
| **Score global** | **6.4/10** | **Moyenne ponderee** |

---

## Architecture

### Points Forts
- **Separation claire** : Backend FastAPI / Frontend Next.js / Infrastructure Docker bien isolees
- **7 services Docker** orchestres avec health checks et dependencies
- **Mode degrade** : Le backend fonctionne meme si PostgreSQL est down (`degraded_middleware.py`)
- **Health monitoring** : Background task qui probe PostgreSQL et Redis toutes les 30s
- **Service registry** avec statuts HEALTHY/UNAVAILABLE pour chaque service
- **Modele de donnees riche** : 12 modeles SQLAlchemy couvrant users, brands, content, publishing, media, autopilot, audit
- **Agent AI multi-provider** : Support OpenAI et Anthropic avec switch configurable
- **CrewAI integration** : 5 agents (analyst, writer, strategist, critic, researcher) + 3 crews
- **Connector pattern** : BaseConnector abstrait avec implementations Meta, LinkedIn, TikTok, Upload-Post

### Points Faibles
- **MetaConnector est du dead code** : `factory.py` route Instagram vers `UploadPostConnector`, pas `MetaConnector`
- **Pas de message broker dedicate** : Redis sert de cache, broker Celery, et result backend (3 DBs differentes mais meme instance)
- **Pas de CDN** : Les images sont servies depuis `/tmp/presenceos/uploads` via StaticFiles
- **Pas de API versioning strategy** : Tout est sous `/api/v1/` mais pas de plan pour v2
- **Frontend state management eclate** : Mix de localStorage, React Query, Zustand, et useState local
- **30+ fichiers d'endpoints** : Certains pourraient etre regroupes (posts/drafts/ideas par exemple)

### Recommandations
- Supprimer `meta.py` ou documenter pourquoi il est conserve
- Migrer les fichiers statiques vers S3/MinIO avec signed URLs
- Definir une strategie de versioning API claire
- Consolider le state management frontend (Zustand comme source unique)

---

## Qualite du Code

### Backend
**Score** : 7.0/10

**Bien fait :**
- PEP 8 globalement respecte avec ruff/black configures
- Type hints modernes (`str | None`, `dict[str, Any]`) utilises partout
- Structlog pour le logging structure (JSON)
- Pydantic v2 pour la validation des schemas
- Async/await correctement utilise avec SQLAlchemy async
- Retry avec backoff exponentiel dans `ai_service.py` (tenacity)
- Bon pattern de factory pour les connectors

**A ameliorer :**

1. **Validation d'inputs inexistante sur les endpoints AI**
   - `app/ai/market_analyzer.py:126-144` : `niche` et `location` acceptes sans limite de longueur ni de format
   - `app/ai/photo_studio.py:213-218` : `prompt` sans aucune validation, `size` non valide contre la whitelist DALL-E
   - `app/api/v1/endpoints/strategy.py:90-96` : `niche` et `location` injectes directement dans les prompts GPT-4
   - **Impact** : Prompt injection, DoS via inputs volumineux, couts API non controles

2. **Exception handling trop large**
   - `app/ai/market_analyzer.py:150-165` : `except Exception as exc` au lieu d'exceptions specifiques
   - `app/ai/photo_studio.py:245-255` : Meme probleme
   - `app/services/ai_service.py:168-170` : Meme probleme
   - **Impact** : Perte d'information sur les erreurs, pas de distinction entre erreur reseau/auth/rate-limit

3. **Brand ownership non verifie sur les endpoints AI**
   - `app/api/v1/endpoints/studio_ai.py:38-43` : `_get_brand_name()` ne verifie pas que le brand appartient au user
   - `app/api/v1/endpoints/strategy.py:42-84` : `_load_brand_context()` meme probleme
   - **Impact** : Un user peut generer du contenu AI pour le brand d'un autre user (IDOR)

4. **Generation sequentielle de variants**
   - `app/services/ai_service.py:310-328` : Boucle `for style in styles_to_generate` sequentielle
   - **Fix** : Utiliser `asyncio.gather()` comme dans `market_analyzer.py:152-157`

5. **JSON parsing fragile**
   - `app/services/ai_service.py:172-182` : `_parse_json_response()` utilise `find("{")` et `rfind("}")` - echoue si reponse contient plusieurs objets JSON
   - `app/ai/market_analyzer.py:231` : `json.loads()` sans validation de schema

6. **PKCE casse dans TikTok connector**
   - `app/connectors/tiktok.py:55` : Code challenge = plaintext au lieu de SHA256(code_verifier)
   - **Impact** : PKCE est inutile, la securite OAuth est degradee

### Frontend
**Score** : 6.5/10

**Bien fait :**
- Architecture Next.js 14 App Router bien utilisee
- shadcn/ui + Radix pour les composants accessibles de base
- Framer Motion pour les animations fluides
- Design system avec gradients (GradientCard, GradientButton)
- PWA configuree (next-pwa)
- React Query pour le data fetching
- Zustand pour le state management global
- Zod disponible pour la validation (mais peu utilise)

**A ameliorer :**

1. **60+ occurrences de `: any` dans `src/lib/api.ts`**
   - `api.ts:92` : `create: (workspaceId: string, data: any)`
   - `api.ts:102` : `list: (brandId: string, params?: any)`
   - `api.ts:105` : `create: (brandId: string, data: any)`
   - **Impact** : Annule les benefices de TypeScript, bugs runtime possibles

2. **`alert()` utilise a la place de toasts**
   - `src/app/(dashboard)/create/page.tsx:118` : `alert("Brouillon sauvegarde !")`
   - `src/components/studio/PostPreview.tsx:108` : `alert("La publication sera connectee...")`
   - **Impact** : UX degradee, bloque le thread principal

3. **Pas d'invalidation de token au logout**
   - `src/components/layout/sidebar.tsx:81-84` : `localStorage.removeItem("token")` seulement
   - Pas d'appel API pour invalider le token cote serveur
   - **Impact** : Token intercepte reste valide 30 min apres "logout"

4. **Accessibilite insuffisante**
   - `src/app/(dashboard)/studio/page.tsx:435-449` : Boutons toggle sans `aria-pressed`
   - `src/components/studio/PhotoGenerator.tsx:122-138` : Style selector non accessible au clavier
   - `src/components/studio/PostPreview.tsx:62-66` : Icones Heart/Message/Send sans `aria-label`
   - `src/app/(dashboard)/create/page.tsx:188-210` : Tabs sans `role="tab"` ni `aria-selected`

5. **`console.log` restants en production**
   - `src/app/(dashboard)/agents/page.tsx:124,129,134` : Debug logging a retirer

6. **Error handling minimal dans `api.ts`**
   - `api.ts:24-37` : Seul le 401 est gere, pas de retry sur 429, pas de message user-friendly sur 500

---

## Bugs Critiques (P0) - A corriger IMMEDIATEMENT

### Bug #1 : Secrets API exposes dans les fichiers .env
**Severite** : P0 (Critique)
**Fichiers** : `.env:57`, `backend/.env:23`, `backend/.env:48`, `.env:90`
**Description** : Les cles API OpenAI (sk-proj-...), token Telegram, et JWT Upload-Post sont en clair dans les fichiers .env qui sont dans le repertoire de travail. Meme si .gitignore les exclut, tout acces au filesystem expose toutes les cles.
**Impact** : Compromission des comptes OpenAI, Telegram, Upload-Post. Couts API non controles.
**Fix suggere** :
```bash
# 1. Revoquer et regenerer TOUTES les cles exposees
# 2. Utiliser un gestionnaire de secrets
# Pour dev: utiliser .env avec des valeurs placeholder
# Pour prod: AWS Secrets Manager, HashiCorp Vault, ou Doppler

# 3. Verifier que les cles n'ont jamais ete commitees
git log --all --oneline -S "sk-proj" -- "*.env"
```

### Bug #2 : CORS allow_methods=["*"] + allow_headers=["*"]
**Severite** : P0 (Critique)
**Fichier** : `backend/app/main.py:199-200`
**Description** : La configuration CORS autorise toutes les methodes HTTP et tous les headers depuis les origines autorisees. Combine avec `allow_credentials=True`, cela permet a n'importe quel script sur localhost:3000/3001 d'effectuer des DELETE, PUT, PATCH avec les cookies de l'utilisateur.
**Impact** : CSRF possible, manipulation de donnees via des requetes cross-origin.
**Fix suggere** :
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,  # Utiliser la config
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)
```

### Bug #3 : Salt statique pour le chiffrement des tokens
**Severite** : P0 (Critique)
**Fichier** : `backend/app/core/security.py:87`
**Description** : `salt=b"presenceos_salt_v1"` est un sel statique pour PBKDF2HMAC. Tous les tokens sont chiffres avec la meme derivation de cle, ce qui reduit considerablement la securite.
**Impact** : Si une cle est compromise, toutes les cles derivees sont compromises.
**Fix suggere** :
```python
import os

class TokenEncryption:
    def __init__(self, key: str | None = None):
        encryption_key = key or settings.token_encryption_key
        if not encryption_key or len(encryption_key) < 32:
            raise RuntimeError("TOKEN_ENCRYPTION_KEY must be at least 32 chars")

        # Utiliser un salt aleatoire stocke a cote du ciphertext
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        # Stocker le salt avec le ciphertext pour pouvoir dechiffrer
```

### Bug #4 : SECRET_KEY placeholder en dev
**Severite** : P0 (Critique)
**Fichiers** : `.env:10`, `backend/.env:5`
**Description** : `SECRET_KEY=dev-secret-key-change-in-production-32chars` et `SECRET_KEY=change-me-to-a-random-string-min-32-chars` sont des valeurs placeholder. Cette cle signe les JWT d'authentification.
**Impact** : N'importe qui connaissant cette valeur peut forger des tokens JWT valides.
**Fix suggere** :
```bash
# Generer une cle aleatoire
python -c "import secrets; print(secrets.token_urlsafe(64))"
# Remplacer dans .env
```

### Bug #5 : IDOR sur les endpoints AI (brand_id non verifie)
**Severite** : P0 (Critique)
**Fichiers** : `app/api/v1/endpoints/studio_ai.py:38-43`, `app/api/v1/endpoints/strategy.py:42-84`
**Description** : Les fonctions `_get_brand_name()` et `_load_brand_context()` chargent n'importe quel brand sans verifier qu'il appartient au user authentifie.
**Impact** : Un user peut generer des photos AI, analyser le marche, et acceder aux donnees de brand d'un autre user.
**Fix suggere** :
```python
# studio_ai.py
async def _get_brand_name(db: AsyncSession, brand_id: UUID, user_id: UUID) -> str | None:
    result = await db.execute(
        select(Brand.name)
        .join(Workspace, Brand.workspace_id == Workspace.id)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(Brand.id == brand_id, WorkspaceMember.user_id == user_id)
    )
    return result.scalar_one_or_none()
```

### Bug #6 : PKCE casse dans le connector TikTok
**Severite** : P0 (Critique)
**Fichier** : `app/connectors/tiktok.py:55`
**Description** : Le code_challenge est le code_verifier en clair au lieu de son hash SHA256. Le commentaire dit "Simplified, should be hashed" mais ce n'est pas un simplification, c'est une vulnerabilite.
**Impact** : La protection PKCE est completement inoperante. Un attaquant interceptant la redirection OAuth peut voler le token TikTok.
**Fix suggere** :
```python
import hashlib
import base64

code_verifier = secrets.token_urlsafe(32)
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b"=").decode()
```

---

## Bugs Majeurs (P1) - A corriger rapidement

### Bug #7 : Pas de validation d'inputs sur les prompts AI
**Severite** : P1
**Fichiers** : `app/ai/market_analyzer.py:192`, `app/ai/photo_studio.py:213`, `app/services/ai_service.py:213`
**Description** : Les parametres `niche`, `location`, `prompt`, `brand_name`, et `context` sont injectes directement dans les prompts GPT-4/DALL-E via f-strings. Aucune limite de longueur, aucune sanitization.
**Impact** : Prompt injection (manipulation des reponses AI), DoS via prompts de 10MB, couts API non controles.
**Fix suggere** :
```python
# Dans les endpoints Pydantic
class GeneratePhotoRequest(BaseModel):
    prompt: str = Field(..., max_length=2000, description="...")
    style: Literal["natural", "editorial", "cinematic", "artistic"] = "natural"
    size: Literal["1024x1024", "1792x1024", "1024x1792"] = "1024x1024"
    niche: str = Field(default="restaurant", max_length=100)
```

### Bug #8 : Pas de rate limiting sur les endpoints AI
**Severite** : P1
**Fichiers** : `app/api/v1/endpoints/studio_ai.py`, `app/api/v1/endpoints/strategy.py`
**Description** : Le rate limiter global (200/min) existe mais les endpoints AI n'ont pas de limites specifiques. Un appel a `analyze_niche` declenche 5 appels GPT-4 en parallele.
**Impact** : Un user malveillant peut generer des couts OpenAI illimites. 100 requetes = 500 appels GPT-4.
**Fix suggere** :
```python
from app.middleware.rate_limit import limiter

@router.post("/generate-photo")
@limiter.limit("10/minute")  # Max 10 generations/min
async def generate_photo(...):
    ...

@router.post("/analyze-niche")
@limiter.limit("5/minute")  # Max 5 analyses/min
async def analyze_niche(...):
    ...
```

### Bug #9 : URLs DALL-E ephemeres non persistees
**Severite** : P1
**Fichier** : `app/ai/photo_studio.py:257-258`
**Description** : Les URLs d'images DALL-E expirent apres 1 heure (politique OpenAI). Le code retourne l'URL directement sans la telecharger et la stocker sur S3/MinIO.
**Impact** : Toute image generee est perdue apres 1h. L'utilisateur voit une 404 s'il revient plus tard.
**Fix suggere** :
```python
# Apres generation, telecharger et stocker sur MinIO
async def _persist_image(self, url: str, user_id: str, brand_id: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()

    key = f"ai-photos/{user_id}/{brand_id}/{uuid4()}.png"
    # Upload vers MinIO/S3
    s3_client.put_object(Bucket=settings.s3_bucket_name, Key=key, Body=response.content)
    return f"{settings.s3_public_url}/{key}"
```

### Bug #10 : OAuth callback sans validation du state
**Severite** : P1
**Fichier** : `app/api/v1/endpoints/connectors.py:58-59`
**Description** : Le callback OAuth ne valide pas le parametre `state` contre la valeur stockee. L'endpoint accepte n'importe quel code d'autorisation.
**Impact** : Attaque CSRF possible sur le flow OAuth. Un attaquant peut lier son compte social au compte de la victime.
**Fix** : Verifier que `state` correspond a la valeur generee lors de la redirection.

### Bug #11 : Password reset token logue en clair
**Severite** : P1
**Fichier** : `app/api/v1/endpoints/auth.py:381-397`
**Description** : Le token de reset password est imprime dans les logs ET sur stdout. Meme si c'est pour le dev, ces logs peuvent etre captes par Sentry ou un systeme de monitoring.
**Impact** : Compromission de compte via les logs.
**Fix** : Supprimer les print/logger.info du token brut. Envoyer par email uniquement.

### Bug #12 : Subprocess avec input non valide
**Severite** : P1
**Fichiers** : `app/services/remotion_renderer.py:141`, `app/services/ffmpeg_processor.py:36-40`
**Description** : Les commandes subprocess/ffmpeg sont construites avec des inputs utilisateur (props JSON, zoom_direction) sans sanitization.
**Impact** : Injection de commande possible via des parametres craftes.
**Fix** : Valider strictement les inputs avec une whitelist avant de les passer a subprocess.

### Bug #13 : Erreurs internes exposees au client
**Severite** : P1
**Fichier** : `app/api/v1/endpoints/studio_ai.py:127-130`
**Description** : `detail=f"Photo generation failed: {str(exc)}"` expose les messages d'erreur internes (potentiellement des infos sur l'API key, le provider, etc.).
**Impact** : Information disclosure.
**Fix** : Logger le detail, retourner un message generique au client.

---

## Bugs Mineurs (P2) - A corriger quand possible

| # | Description | Fichier | Impact |
|---|-------------|---------|--------|
| 14 | `VariantStyle` contient `FAICAL_STYLE` hardcode | `models/content.py:59` | Pas generique |
| 15 | `get_account_metrics()` retourne 0 hardcode | `connectors/meta.py:370` | Metriques fausses |
| 16 | Date parsing assume ISO format sans try/except | `services/ai_service.py:254-256` | Crash si format different |
| 17 | Transcription audio hardcodee en francais | `services/ai_service.py:401` | Echoue en anglais |
| 18 | Caption TikTok tronquee sans notification | `connectors/tiktok.py:196` | User pas informe |
| 19 | `quick_create_post` ne permet pas les medias | `endpoints/posts.py:515-518` | Feature incomplete |
| 20 | `generate_variations` silencieusement limite a 4 | `ai/photo_studio.py:292-305` | User attend plus |
| 21 | `revised_prompt` DALL-E expose au client | `ai/photo_studio.py:258,264` | Information disclosure |
| 22 | `console.log` debug dans agents/page.tsx | `frontend/src/app/(dashboard)/agents/page.tsx:124,129,134` | Fuite d'info |
| 23 | `alert()` au lieu de toast pour les notifications | `frontend - create/page.tsx, PostPreview.tsx` | UX degradee |
| 24 | Minio credentials par defaut (minioadmin) | `.env:45-46` | Securite dev |
| 25 | `sync_connector_metrics` endpoint non implemente | `endpoints/connectors.py:346` | Dead endpoint |

---

## Securite

**Score** : 5.0/10

### Bien securise
- **Bcrypt** pour le hashing des mots de passe (`security.py:25-34`)
- **JWT avec expiration** : 30 min access, 7 jours refresh (`security.py:20-21`)
- **Rotation des refresh tokens** avec detection de reutilisation (famille de tokens, `auth.py:222-232`)
- **Rate limiting** via slowapi : 200 req/min global, 5/min sur auth (`middleware/rate_limit.py`)
- **Security headers** : X-Frame-Options: DENY, HSTS, X-Content-Type-Options: nosniff (`middleware/security_headers.py`)
- **Sentry filtering** : Filtre password, token, api_key, secret avant envoi (`main.py:26-43`)
- **SQLAlchemy ORM** : Pas de SQL brut, protection contre injection SQL
- **Access control** : Brand ownership verifie dans `deps.py:142-174` (mais pas dans les endpoints AI)
- **Captcha disponible** : hCaptcha integre frontend (`@hcaptcha/react-hcaptcha`)
- **DomPurify** dans les dependances frontend (protection XSS)
- **Mode degrade** : Fallback gracieux si DB down

### Vulnerabilites detectees

| # | Vulnerabilite | Severite | Fichier |
|---|--------------|----------|---------|
| 1 | Cles API en clair dans .env | CRITIQUE | `.env`, `backend/.env` |
| 2 | CORS wildcard methods/headers | CRITIQUE | `main.py:199-200` |
| 3 | Salt statique PBKDF2 | CRITIQUE | `security.py:87` |
| 4 | SECRET_KEY placeholder | CRITIQUE | `.env:10`, `backend/.env:5` |
| 5 | IDOR sur endpoints AI | CRITIQUE | `studio_ai.py`, `strategy.py` |
| 6 | PKCE TikTok casse | CRITIQUE | `tiktok.py:55` |
| 7 | Prompt injection possible | HAUTE | `market_analyzer.py`, `photo_studio.py` |
| 8 | OAuth state non valide | HAUTE | `connectors.py:58` |
| 9 | Subprocess avec input non sanitise | HAUTE | `remotion_renderer.py:141` |
| 10 | Token reset logue en clair | MOYENNE | `auth.py:381-397` |
| 11 | Password validation faible (8 chars min) | MOYENNE | `auth.py:408-413` |
| 12 | Credentials DB/MinIO par defaut | MOYENNE | `.env:27-28,45-46` |
| 13 | DEBUG=true | BASSE | `.env:9`, `backend/.env:4` |

### Recommandations securite
1. **Immediate** : Revoquer et regenerer toutes les cles API exposees
2. **Immediate** : Restreindre CORS aux methodes et headers necessaires
3. **Immediate** : Remplacer le salt statique par un salt aleatoire
4. **Semaine 1** : Implementer un gestionnaire de secrets (Vault, AWS Secrets Manager)
5. **Semaine 1** : Ajouter la validation d'inputs sur tous les endpoints AI
6. **Semaine 2** : Implementer CSP (Content-Security-Policy) dans next.config.js
7. **Semaine 2** : Migrer les tokens de localStorage vers httpOnly cookies
8. **Semaine 3** : Ajouter des regles de complexite pour les mots de passe

---

## Performance

**Score** : 6.5/10

### Points forts
- **Async natif** : FastAPI + SQLAlchemy async + asyncpg
- **Parallelisation AI** : `asyncio.gather()` dans market_analyzer (4 appels GPT-4 en parallele)
- **Retry avec backoff** : Tenacity dans ai_service.py (3 tentatives, backoff exponentiel)
- **Redis disponible** pour le caching (mais sous-utilise)
- **Health monitoring background** toutes les 30s
- **Connection pooling** PostgreSQL via SQLAlchemy

### Problemes identifies

| Probleme | Impact | Fichier |
|----------|--------|---------|
| Pas de caching des analyses AI | Chaque appel = 5 requetes GPT-4 | `market_analyzer.py` |
| Pas de caching des reponses AI | Chaque caption = 1 requete GPT-4 | `ai_service.py` |
| Variants generes sequentiellement | 3x plus lent que necessaire | `ai_service.py:310-328` |
| Nouveau httpx.AsyncClient par requete | Pas de connection pooling HTTP | Tous les connectors |
| Images chargees en memoire | OOM possible avec gros fichiers | `upload_post.py:115` |
| URLs DALL-E non persistees | Expiration 1h, re-generation necessaire | `photo_studio.py:257` |
| Pas de timeout sur les appels OpenAI | Requetes peuvent bloquer indefiniment | `photo_studio.py:246-252` |
| Calendar genere tous les jours de la range | Lent pour les ranges > 30 jours | `posts.py:435-437` |
| Frontend : pas de virtualisation des listes | Lag avec 50+ messages dans studio | `studio/page.tsx:481-485` |
| Frontend : animations infinies | Consommation batterie mobile | `GradientCard.tsx:38-48` |

### Optimisations recommandees

1. **Cache Redis pour les analyses AI** (TTL 24h, cle: hash(niche+location+brand_context))
   - Impact estime : -80% d'appels GPT-4 pour les memes parametres

2. **Paralleliser la generation de variants** dans `ai_service.py`
   ```python
   # Avant (sequentiel)
   for style in styles:
       variant = await self._complete(prompt)

   # Apres (parallele)
   tasks = [self._complete(prompt.format(style=s)) for s in styles]
   variants = await asyncio.gather(*tasks)
   ```
   - Impact estime : 3x plus rapide

3. **Connection pooling HTTP** : Creer un AsyncClient partage par connector
   - Impact estime : -50% de latence sur les appels API sociaux

4. **Timeout sur les appels OpenAI** :
   ```python
   response = await asyncio.wait_for(
       client.images.generate(...),
       timeout=60.0
   )
   ```

5. **Virtualisation des listes** dans le frontend avec `react-window`

---

## Tests & Coverage

**Tests** : ~454 fonctions de test dans 21 fichiers
**Pass rate rapporte** : 395/461 (85.7%)

### Analyse de la suite de tests

| Fichier | Tests | Description |
|---------|-------|-------------|
| test_auth.py | 27 | Authentification, JWT, refresh tokens |
| test_agents.py | 34 | Agents CrewAI |
| test_sprint9c.py | 38 | Sprint 9C (video, conversation) |
| test_media_library.py | 33 | Media library |
| test_sprint9.py | 32 | Sprint 9 |
| test_sprint10.py | 28 | Sprint 10 |
| test_autopilot.py | 28 | Autopilot scheduling |
| test_sprint8.py | 28 | Sprint 8 |
| test_upload_post.py | 24 | Upload-Post connector |
| test_brands.py | 22 | Brand management |
| test_sprint9b.py | 21 | Sprint 9B |
| test_ideas.py | 20 | Content ideas |
| test_posts.py | 19 | Post management |
| test_sprint7.py | 19 | Sprint 7 |
| test_telegram.py | 18 | Telegram bot |
| test_calendar.py | 15 | Calendar |
| test_resilience.py | 14 | Mode degrade |
| test_media.py | 11 | Media assets |
| test_conversation_flow.py | 10 | Conversation |
| test_webchat.py | 9 | Webchat |
| conftest.py | 4 | Fixtures |

### Points forts
- **Bonne couverture fonctionnelle** : Auth, brands, posts, media, connectors, autopilot
- **Fixtures bien structurees** dans conftest.py (test_user, test_workspace, test_brand, auth_headers)
- **Async tests** avec pytest-asyncio
- **Test database isolee** (`presenceos_test`)
- **Tables recreees pour chaque test** (isolation parfaite)

### Problemes
- **66 tests en echec** (14.3%) - non trivial
- **Nomenclature inconsistante** : `test_sprint7.py`, `test_sprint8.py`, etc. ne sont pas descriptifs
- **Pas de tests pour les nouveaux endpoints AI** : studio_ai.py et strategy.py non couverts
- **Pas de tests d'integration** pour les flows complets (photo upload -> AI caption -> publish)
- **Pas de tests de securite** (IDOR, injection, auth bypass)
- **Pas de tests frontend** (Playwright configure mais pas de fichiers dans `tests/e2e/`)

### Tests manquants (priorite)
1. Tests unitaires pour `market_analyzer.py` et `photo_studio.py`
2. Tests de validation d'inputs sur les endpoints AI
3. Tests IDOR (verifier qu'un user ne peut pas acceder au brand d'un autre)
4. Tests de rate limiting
5. Tests E2E Playwright pour les flows critiques (login, create post, photo studio)
6. Tests de regression pour les 66 echecs existants

---

## Dette Technique

**Score dette** : 6.0/10

### TODO/FIXME dans le code

**Backend (selection) :**
| Fichier | Ligne | TODO |
|---------|-------|------|
| `endpoints/metrics.py` | 141 | `TODO: Calculate from historical data` |
| `endpoints/connectors.py` | 346 | `TODO: Trigger async metrics sync job` |
| `endpoints/posts.py` | 450 | `TODO: Add ideas suggested for this date` |
| `connectors/tiktok.py` | 216 | `TODO: Implement polling for async publish` |

**Frontend :**
| Fichier | TODO |
|---------|------|
| `agents/page.tsx` | `TODO: Implement approval logic` |
| `agents/page.tsx` | `TODO: Implement edit logic` |
| `agents/page.tsx` | `TODO: Implement rejection logic` |

### Code smells detectes
1. **Code duplique** : `_get_brand_name()` dans studio_ai.py et `_load_brand_context()` dans strategy.py font la meme chose differemment
2. **Noms de fichiers sprints** : `test_sprint7.py` a `test_sprint10.py` ne sont pas maintenables
3. **French/English mix** : Prompts en francais, code en anglais, comments en mix
4. **MetaConnector dead code** : `meta.py` existe mais n'est jamais utilise par la factory
5. **`FAICAL_STYLE`** hardcode dans les enums de content.py
6. **Carousel creation sans transaction** : Si un child item echoue, le carousel est casse

### Dead code
- `app/connectors/meta.py` : Non utilise par `factory.py`
- `VariantStyle.FAICAL_STYLE` : Specifique a un dev
- `get_account_metrics()` dans meta.py : Retourne des 0 hardcodes
- `sync_connector_metrics` endpoint : Non implemente (TODO)
- Possiblement des imports inutilises (a verifier avec pylint)

---

## Infrastructure

**Score** : 7.5/10

### Points forts
- **Docker Compose complet** : 7 services bien configures
- **Health checks** sur tous les services (postgres, redis, minio, backend, celery, frontend)
- **Dependencies** : Les services attendent les dependances saines (`condition: service_healthy`)
- **Volumes persistes** : postgres_data, redis_data, minio_data
- **Start period** configure pour les services lents (backend 30s, frontend 60s)
- **Network isolee** : Bridge network `presenceos`
- **pgvector** pour les embeddings (postgresql 16 + pgvector)
- **Celery Worker + Beat** pour les taches asynchrones

### Points faibles
1. **`npm install` a chaque demarrage du frontend** (`command: sh -c "npm install && npm run dev"`)
   - Devrait utiliser un Dockerfile avec les deps pre-installees
2. **Pas de Dockerfile pour le frontend** en dev (utilise `node:20-alpine` direct)
3. **Backend volumes monte le code source** : Bon pour dev, pas pour prod
4. **Pas de config production** : Pas de docker-compose.prod.yml
5. **Redis non securise** : Pas de mot de passe configure
6. **MinIO avec credentials par defaut** : `minioadmin:minioadmin`
7. **Pas de backup strategy** : Pas de cron pour les dumps PostgreSQL
8. **Pas de reverse proxy** : Pas de Nginx/Traefik pour le SSL

### Recommandations
1. Creer un `docker-compose.prod.yml` avec :
   - Images pre-built (pas de volume mount)
   - Redis avec mot de passe
   - MinIO avec credentials forts
   - Nginx reverse proxy avec SSL
   - Resource limits (memory, CPU)
2. Ajouter un service de backup PostgreSQL (pg_dump cron)
3. Configurer des log drivers pour la centralisation

---

## Features Audit

### Multi-Account Support
- **Status** : Fonctionnel (3 Instagram + 2 Facebook par user)
- **Issue** : La race condition sur les limites de comptes (`connectors.py:147-161`) n'est pas atomique
- **Issue** : Le rate limiting par compte social n'est pas implemente

### AI Photo Studio (DALL-E 3)
- **Status** : Fonctionnel mais URLs ephemeres
- **Qualite DALL-E** : Bons prompts avec 4 styles (natural, editorial, cinematic, artistic) et 23 niches
- **Issue critique** : URLs expirent apres 1h (pas de persistence S3)
- **Issue** : Pas de validation de `size` contre les valeurs DALL-E valides
- **Issue** : `generate_variations` limite silencieusement a 4

### AI Market Analyzer (GPT-4)
- **Status** : Fonctionnel avec parallelisation
- **Pertinence** : Bon systeme en 2 phases (4 analyses paralleles + synthese strategie)
- **Issue** : Pas de caching (5 appels GPT-4 par analyse)
- **Issue** : Pas de validation des inputs

### Brand Context
- **Status** : Bien injecte dans market_analyzer et photo_studio
- **Implementation** : `_build_brand_block()` construit un bloc texte avec name, type, description, voice, constraints
- **Issue** : `ensure_ascii=False` dans json.dumps peut injecter des caracteres de controle dans les prompts

### Auto-Scheduling (Autopilot)
- **Status** : Modele de donnees present, mais `approval_window_hours` sans gestion de timezone
- **Issue** : `generation_hour` est en UTC mais devrait utiliser la timezone de la brand
- **Issue** : `expires_at` sur PendingPost sans logique d'auto-expiration

### Analytics
- **Status** : Partiel
- **Issue** : `get_account_metrics()` dans MetaConnector retourne des 0 hardcodes
- **Issue** : `best_posting_time` est `None` (TODO dans le code)

---

## Plan d'Action Recommande

### URGENT (Cette semaine)

1. **Revoquer et regenerer toutes les cles API** exposees dans les .env
2. **Corriger CORS** : Restreindre allow_methods et allow_headers
3. **Generer un vrai SECRET_KEY** cryptographiquement aleatoire
4. **Corriger le salt statique** dans TokenEncryption
5. **Ajouter la verification brand ownership** dans studio_ai.py et strategy.py
6. **Fixer PKCE TikTok** : Implementer SHA256 hash
7. **Ajouter DEBUG=false** dans la config production

### IMPORTANT (Ce mois)

1. **Validation d'inputs** sur tous les endpoints AI (max_length, Literal types, regex)
2. **Rate limiting specifique** sur les endpoints AI (10/min photos, 5/min analyses)
3. **Persister les images DALL-E** sur MinIO au lieu de retourner les URLs ephemeres
4. **Valider le state OAuth** dans tous les callbacks de connectors
5. **Supprimer le logging du token reset** en clair
6. **Typer api.ts** : Remplacer les 60+ `any` par des interfaces TypeScript
7. **Ajouter des tests** pour market_analyzer, photo_studio, et les endpoints AI
8. **Fixer les 66 tests en echec** ou les marquer skip avec raison
9. **Sanitiser les inputs subprocess** dans remotion_renderer et ffmpeg_processor
10. **Implementer le logout serveur** : Endpoint pour invalider les tokens

### NICE TO HAVE (Plus tard)

1. **Implementer CSP** (Content-Security-Policy) dans next.config.js
2. **Migrer tokens** de localStorage vers httpOnly cookies
3. **Cache Redis** pour les analyses AI (TTL 24h)
4. **Paralleliser** la generation de variants dans ai_service.py
5. **Connection pooling HTTP** dans les connectors
6. **Virtualiser** les listes de messages dans studio/page.tsx
7. **Creer docker-compose.prod.yml** avec reverse proxy et SSL
8. **Ajouter des tests E2E** Playwright pour les flows critiques
9. **Nettoyer le dead code** : meta.py, FAICAL_STYLE, endpoints TODO
10. **Renommer les fichiers test_sprint*.py** avec des noms descriptifs
11. **Ajouter backup PostgreSQL** automatise
12. **Implementer le polling TikTok** pour le statut de publication
13. **Completer get_account_metrics** dans MetaConnector

---

## Conclusion

PresenceOS est un projet ambitieux avec une **architecture solide** et un **scope fonctionnel impressionnant** (20+ pages, 30+ endpoints, 5 agents AI, 4 connectors sociaux). Le code est globalement bien structure et suit les bonnes pratiques modernes (async, Pydantic v2, structlog).

Cependant, **le projet n'est pas pret pour la production** en l'etat. Les 6 vulnerabilites critiques de securite (secrets exposes, CORS permissif, salt statique, SECRET_KEY placeholder, IDOR, PKCE casse) doivent etre corrigees en priorite absolue. Le taux d'echec des tests (14.3%) et l'absence de tests sur les nouvelles features AI sont egalement preoccupants.

La bonne nouvelle : **aucun de ces problemes n'est architectural**. Ce sont des corrections ponctuelles qui peuvent etre resolues en 1-2 semaines de travail concentre. Une fois ces corrections appliquees, PresenceOS sera dans une bonne position pour un lancement beta.

**Score final : 6.4/10** - Bon potentiel, corrections de securite requises avant production.

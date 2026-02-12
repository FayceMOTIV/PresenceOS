# OAuth Setup Guide

Ce guide explique comment configurer les applications OAuth pour chaque plateforme sociale.

## Meta (Instagram / Facebook)

### 1. Créer une App Meta

1. Rendez-vous sur [Meta for Developers](https://developers.facebook.com/)
2. Cliquez sur "My Apps" → "Create App"
3. Choisissez "Business" comme type d'app
4. Remplissez les informations de base

### 2. Configurer les produits

1. Dans le dashboard de l'app, ajoutez les produits :
   - **Facebook Login**
   - **Instagram Graph API**

2. Pour Facebook Login :
   - Settings → Valid OAuth Redirect URIs : `http://localhost:3000/api/auth/callback/meta`
   - (Production) : `https://votre-domaine.com/api/auth/callback/meta`

3. Pour Instagram :
   - Nécessite un compte Instagram Business connecté à une Page Facebook
   - Demandez les permissions : `instagram_basic`, `instagram_content_publish`, `instagram_manage_comments`, `instagram_manage_insights`

### 3. Récupérer les credentials

Dans Settings → Basic :
- **App ID** → `META_APP_ID`
- **App Secret** → `META_APP_SECRET`

### 4. Permissions requises

```
instagram_basic
instagram_content_publish
instagram_manage_comments
instagram_manage_insights
pages_show_list
pages_read_engagement
business_management
```

### 5. Limites API

- **Publishing** : 100 posts par 24h par compte Instagram Business
- **Rate limits** : Voir [Meta Graph API Rate Limiting](https://developers.facebook.com/docs/graph-api/overview/rate-limiting/)

---

## TikTok

### 1. Créer une App TikTok

1. Rendez-vous sur [TikTok for Developers](https://developers.tiktok.com/)
2. Créez un compte développeur
3. Créez une nouvelle application

### 2. Configurer Content Posting API

1. Dans votre app, ajoutez le produit "Content Posting API"
2. Configurez les scopes :
   - `user.info.basic`
   - `video.publish`
   - `video.upload`

3. Ajoutez les Redirect URIs :
   - `http://localhost:3000/api/auth/callback/tiktok`
   - (Production) : `https://votre-domaine.com/api/auth/callback/tiktok`

### 3. Récupérer les credentials

- **Client Key** → `TIKTOK_CLIENT_KEY`
- **Client Secret** → `TIKTOK_CLIENT_SECRET`

### 4. Particularités TikTok

- Les vidéos doivent être uploadées via URL (pas d'upload direct)
- Utilisez MinIO/S3 pour héberger temporairement les vidéos
- Le statut de publication est asynchrone (polling ou webhooks)

### 5. Sandbox vs Production

- En sandbox, seuls les comptes de test peuvent poster
- Pour la production, soumettez votre app à review

---

## LinkedIn

### 1. Créer une App LinkedIn

1. Rendez-vous sur [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Créez une nouvelle application
3. Vérifiez votre entreprise (Company Page requise)

### 2. Configurer les produits

1. Dans Products, demandez l'accès à :
   - **Share on LinkedIn** (publishing)
   - **Sign In with LinkedIn using OpenID Connect**

2. Configurez OAuth 2.0 :
   - Authorized redirect URLs : `http://localhost:3000/api/auth/callback/linkedin`
   - (Production) : `https://votre-domaine.com/api/auth/callback/linkedin`

### 3. Récupérer les credentials

Dans Auth :
- **Client ID** → `LINKEDIN_CLIENT_ID`
- **Client Secret** → `LINKEDIN_CLIENT_SECRET`

### 4. Scopes requis

```
openid
profile
w_member_social
r_organization_social (pour pages entreprise)
w_organization_social (pour pages entreprise)
```

### 5. Notes importantes

- LinkedIn utilise le nouveau Posts API (pas UGC Posts)
- Les tokens expirent après 60 jours
- Refresh token disponible pour renouvellement automatique

---

## Configuration dans .env

```env
# Meta (Instagram/Facebook)
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
META_REDIRECT_URI=http://localhost:3000/api/auth/callback/meta
META_GRAPH_VERSION=v19.0

# TikTok
TIKTOK_CLIENT_KEY=your_tiktok_client_key
TIKTOK_CLIENT_SECRET=your_tiktok_client_secret
TIKTOK_REDIRECT_URI=http://localhost:3000/api/auth/callback/tiktok

# LinkedIn
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
LINKEDIN_REDIRECT_URI=http://localhost:3000/api/auth/callback/linkedin
```

---

## Tester les connexions

1. Lancez l'application en local
2. Créez un compte et un workspace
3. Créez une brand
4. Allez dans Settings → Connections
5. Cliquez sur "Connect" pour chaque plateforme
6. Autorisez l'accès
7. Vérifiez que le compte apparaît comme connecté

---

## Troubleshooting

### Meta
- **Error: Invalid redirect_uri** → Vérifiez que l'URI est exactement la même dans l'app Meta
- **Error: Instagram account not found** → Le compte doit être un compte Business connecté à une Page Facebook

### TikTok
- **Error: Invalid scope** → Vérifiez que Content Posting API est activé
- **Video upload fails** → L'URL doit être publiquement accessible

### LinkedIn
- **Error: Unauthorized scope** → Soumettez votre app à review pour les scopes de publication
- **Error: Invalid token** → Le token a peut-être expiré, utilisez le refresh token

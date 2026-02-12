# PresenceOS Frontend

Application web Next.js 14 pour la plateforme PresenceOS - Agent Marketing IA pour entrepreneurs.

## Technologies

- **Framework**: Next.js 14.1 (App Router)
- **React**: 18.2
- **TypeScript**: 5.3
- **Styling**: Tailwind CSS 3.4
- **Composants UI**: shadcn/ui (Radix UI)
- **Animations**: Framer Motion 11
- **Gestion d'etat**: Zustand 4.5
- **Requetes API**: TanStack Query (React Query) 5.18
- **Formulaires**: React Hook Form + Zod
- **Graphiques**: Recharts 2.12
- **Icones**: Lucide React
- **Drag & Drop**: dnd-kit

## Structure du Projet

```
frontend/
├── src/
│   ├── app/                      # App Router Next.js 14
│   │   ├── page.tsx              # Landing page
│   │   ├── layout.tsx            # Layout principal
│   │   ├── globals.css           # Styles globaux
│   │   ├── auth/                 # Authentification
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── (dashboard)/          # Pages protegees
│   │   │   ├── layout.tsx        # Layout dashboard
│   │   │   ├── dashboard/        # Vue d'ensemble
│   │   │   ├── studio/           # Creation contenu
│   │   │   ├── planner/          # Calendrier
│   │   │   ├── ideas/            # Generateur d'idees
│   │   │   ├── analytics/        # Statistiques
│   │   │   ├── settings/         # Parametres
│   │   │   ├── brain/            # Base connaissances
│   │   │   ├── trends/           # Tendances
│   │   │   └── posts/            # Gestion posts
│   │   ├── onboarding/           # Onboarding
│   │   └── brands/               # Gestion marques
│   ├── components/               # Composants React
│   │   ├── ui/                   # Composants shadcn/ui
│   │   ├── layouts/              # Layouts
│   │   ├── forms/                # Formulaires
│   │   └── ...
│   ├── lib/                      # Utilitaires
│   │   ├── api.ts                # Client API
│   │   ├── utils.ts              # Fonctions utilitaires
│   │   └── ...
│   ├── hooks/                    # Custom hooks
│   ├── store/                    # State management (Zustand)
│   ├── types/                    # Types TypeScript
│   └── styles/                   # Styles additionnels
├── public/                       # Fichiers statiques
│   ├── images/
│   └── ...
├── package.json                  # Dependencies
├── tsconfig.json                 # Config TypeScript
├── tailwind.config.ts            # Config Tailwind
├── next.config.js                # Config Next.js
├── postcss.config.js             # Config PostCSS
└── Dockerfile                    # Image Docker
```

## Installation & Configuration

### 1. Installer les Dependances

```bash
npm install
```

### 2. Variables d'Environnement

Creer un fichier `.env.local` a la racine du frontend:

```env
# API Backend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Environment
NEXT_PUBLIC_ENV=development

# Analytics (optionnel)
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
```

## Lancement

### Mode Developpement

```bash
npm run dev
```

L'application sera accessible sur http://localhost:3001

### Build Production

```bash
npm run build
npm start
```

### Linting

```bash
npm run lint
```

### Formatage

```bash
npm run format
```

## Pages et Fonctionnalites

### Landing Page (`/`)
- Page d'accueil marketing
- Presentation des fonctionnalites
- Call-to-action inscription
- Design moderne et responsive

### Authentification (`/auth`)

#### Connexion (`/auth/login`)
- Formulaire de connexion
- Validation en temps reel
- Gestion des erreurs
- Redirection apres login

#### Inscription (`/auth/register`)
- Formulaire d'inscription
- Validation email et mot de passe
- Creation de compte
- Onboarding automatique

### Dashboard (`/dashboard`)
- Vue d'ensemble de l'activite
- Statistiques cles (posts, engagement, reach)
- Publications recentes
- Graphiques de performance
- Actions rapides

### Studio (`/studio`)
- Creation de contenu assiste par IA
- Editeur de texte riche
- Generation de variations
- Previsualisation multi-plateformes
- Ajout de medias
- Planification de publication

### Planner (`/planner`)
- Calendrier de publications
- Vue mensuelle/hebdomadaire/quotidienne
- Drag & drop pour reorganiser
- Filtres par plateforme
- Statuts de publication
- Edition rapide

### Ideas (`/ideas`)
- Generateur d'idees de contenu IA
- Brainstorming assiste
- Categories de contenu
- Sauvegarde d'idees
- Transformation en posts
- Historique d'idees

### Analytics (`/analytics`)
- Statistiques detaillees
- Graphiques interactifs (Recharts)
- Metriques par plateforme
- Evolution temporelle
- Top performing posts
- Insights et recommandations

### Settings (`/settings`)
- Profil utilisateur
- Marques et reseaux sociaux
- Preferences de generation IA
- Parametres de notification
- Gestion de l'abonnement
- Securite et confidentialite

### Brain (`/brain`)
- Base de connaissances IA
- Documents et ressources
- Training du modele
- Tone of voice
- Exemples de contenu
- Gestion des embeddings

### Trends (`/trends`)
- Tendances actuelles
- Sujets populaires
- Hashtags recommandes
- Opportunites de contenu
- Veille concurrentielle

## Composants Principaux

### UI Components (`components/ui/`)
Composants shadcn/ui bases sur Radix UI:
- `button`, `input`, `select`, `checkbox`, etc.
- `dialog`, `popover`, `tooltip`, `dropdown-menu`
- `card`, `badge`, `avatar`, `separator`
- `tabs`, `accordion`, `scroll-area`
- `table`, `progress`, `slider`

### Custom Components
- `PostCard`: Carte de publication
- `ContentEditor`: Editeur de contenu
- `CalendarView`: Vue calendrier
- `StatsCard`: Carte de statistiques
- `PlatformSelector`: Selecteur de plateformes
- `MediaUpload`: Upload de medias
- `IdeaGenerator`: Interface generateur d'idees

## Gestion de l'Etat

### Zustand Stores
- `useAuthStore`: Authentification et session
- `useBrandStore`: Marques actives
- `usePostStore`: Publications et brouillons
- `useUIStore`: Etat UI (modals, sidebar, etc.)

### React Query
- Mise en cache des requetes API
- Invalidation automatique
- Optimistic updates
- Gestion des erreurs
- Pagination

## API Client

### Configuration (`lib/api.ts`)
```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour ajouter le token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### Utilisation
```typescript
import { api } from '@/lib/api';

// GET
const posts = await api.get('/api/posts');

// POST
const newPost = await api.post('/api/posts', data);

// PUT
const updated = await api.put(`/api/posts/${id}`, data);

// DELETE
await api.delete(`/api/posts/${id}`);
```

## Styling

### Tailwind CSS
Utilisez les classes utilitaires Tailwind pour le styling:
```tsx
<div className="flex items-center gap-4 p-4 rounded-lg bg-white shadow-md">
  <h2 className="text-2xl font-bold text-gray-900">Titre</h2>
</div>
```

### Variants avec CVA
```tsx
import { cva } from 'class-variance-authority';

const buttonVariants = cva('px-4 py-2 rounded-md', {
  variants: {
    variant: {
      primary: 'bg-blue-600 text-white',
      secondary: 'bg-gray-200 text-gray-900',
    },
    size: {
      sm: 'text-sm',
      lg: 'text-lg',
    },
  },
});
```

### Dark Mode
Support du dark mode avec `next-themes`:
```tsx
import { useTheme } from 'next-themes';

const { theme, setTheme } = useTheme();
```

## Animations

### Framer Motion
```tsx
import { motion } from 'framer-motion';

<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  exit={{ opacity: 0, y: -20 }}
  transition={{ duration: 0.3 }}
>
  Contenu anime
</motion.div>
```

## Formulaires

### React Hook Form + Zod
```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

const { register, handleSubmit, formState: { errors } } = useForm({
  resolver: zodResolver(schema),
});
```

## Tests

### Playwright (E2E)
```bash
# Installer Playwright
npx playwright install

# Lancer les tests
npx playwright test

# Mode UI
npx playwright test --ui
```

## Build & Deploy

### Build Production
```bash
npm run build
```

### Analyse du Bundle
```bash
npm run build -- --analyze
```

### Variables d'Environnement Production
```env
NEXT_PUBLIC_API_URL=https://api.presenceos.com
NEXT_PUBLIC_ENV=production
```

## Optimisations

### Images Next.js
```tsx
import Image from 'next/image';

<Image
  src="/logo.png"
  alt="Logo"
  width={200}
  height={50}
  priority
/>
```

### Lazy Loading
```tsx
import dynamic from 'next/dynamic';

const HeavyComponent = dynamic(() => import('@/components/HeavyComponent'), {
  loading: () => <Spinner />,
  ssr: false,
});
```

### Metadata SEO
```tsx
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'PresenceOS - Agent Marketing IA',
  description: 'Plateforme SaaS pour gerer votre presence sociale',
  openGraph: {
    title: 'PresenceOS',
    description: '...',
    images: ['/og-image.png'],
  },
};
```

## Structure de Fichiers Recommandee

```
components/
├── ui/              # shadcn/ui components
├── layouts/         # Layout components
├── posts/           # Post-related components
│   ├── PostCard.tsx
│   ├── PostEditor.tsx
│   └── PostList.tsx
├── calendar/        # Calendar components
├── analytics/       # Analytics components
└── shared/          # Shared components
```

## Conventions de Code

- Utiliser TypeScript pour tous les fichiers
- Composants fonctionnels avec hooks
- Props typees avec TypeScript
- Destructuration des props
- Export nomme pour les composants
- PascalCase pour les composants
- camelCase pour les fonctions
- UPPER_CASE pour les constantes

## Problemes Courants

### Port deja utilise
```bash
# Changer le port
PORT=3002 npm run dev
```

### Erreur de build
```bash
# Nettoyer le cache
rm -rf .next
npm run build
```

### Problemes de types
```bash
# Regenerer les types
npm run type-check
```

## Contribution

1. Creer une branche feature
2. Implementer les changements
3. Tester localement
4. Executer linter et formatter
5. Creer une Pull Request

## Support

Pour toute question, ouvrir une issue sur GitHub.

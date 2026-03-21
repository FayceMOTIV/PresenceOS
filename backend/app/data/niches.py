"""
NicheEngine — Base de connaissance marketing par secteur.
Ilyas l'utilise pour s'adapter instantanément à n'importe quelle niche.
"""

NICHES = {
    "restaurant": {
        "label": "🍕 Restaurant / Café",
        "tone": {"expert": 0.3, "warmth": 0.9, "humor": 0.5, "urgency": 0.6},
        "audience": "Locaux 25-55 ans, familles, actifs",
        "platforms_priority": ["instagram", "facebook", "tiktok"],
        "content_pillars": [
            "Plats du jour / spécialités",
            "Coulisses cuisine / équipe",
            "Recettes et astuces chef",
            "Ambiance / événements",
            "Témoignages clients",
            "Promotions / réservations",
        ],
        "viral_hooks": [
            "Regardez comment on prépare notre...",
            "Le secret de notre [plat signature]...",
            "Ce que nos clients adorent...",
            "Ce soir au menu...",
            "Avant/Après de notre chef...",
        ],
        "cta": ["Réservez maintenant", "Commandez en ligne", "Venez nous voir"],
        "taboo_subjects": [],
        "legal_constraints": [],
        "best_formats": {
            "instagram": "Reels 15-30s + Feed 4:5 + Stories quotidiennes",
            "tiktok": "Vidéo 15-60s vertical, ASMR food, coulisses",
            "facebook": "Post texte + image, événements, promotions locales",
        },
        "posting_times": {
            "instagram": ["11:30", "14:00", "19:00"],
            "tiktok": ["12:00", "18:00", "21:00"],
            "facebook": ["09:00", "12:30", "18:00"],
        },
        "hashtag_strategy": ["#restaurant", "#foodie", "#[ville]", "#[plat]", "#gastronomie"],
        "video_style": "cinematic_food",
        "content_ratio": {"video": 0.5, "image": 0.3, "text": 0.2},
    },
    "boulangerie": {
        "label": "🥐 Boulangerie / Pâtisserie",
        "tone": {"expert": 0.4, "warmth": 0.9, "humor": 0.4, "urgency": 0.7},
        "audience": "Locaux tous âges, familles",
        "platforms_priority": ["instagram", "facebook", "tiktok"],
        "content_pillars": [
            "Créations du jour",
            "Making-of viennoiseries",
            "Fêtes et saisonnalité",
            "Artisanat et savoir-faire",
        ],
        "viral_hooks": [
            "Fraîchement sorti du four...",
            "Le secret de nos croissants...",
            "Fait main depuis [année]...",
        ],
        "cta": ["Venez en boutique", "Commandez pour demain", "Découvrez notre carte"],
        "taboo_subjects": [],
        "legal_constraints": [],
        "best_formats": {
            "instagram": "Reels 15s produits + Stories quotidiennes",
            "tiktok": "Laminage pâte, façonnage, sortie four",
        },
        "posting_times": {"instagram": ["07:00", "11:00"], "tiktok": ["07:30", "12:00"]},
        "hashtag_strategy": ["#boulangerie", "#artisan", "#[ville]", "#viennoiserie"],
        "video_style": "cinematic_food",
        "content_ratio": {"video": 0.4, "image": 0.4, "text": 0.2},
    },
    "medecin": {
        "label": "🏥 Médecin / Professionnel de santé",
        "tone": {"expert": 0.9, "warmth": 0.7, "humor": 0.1, "urgency": 0.3},
        "audience": "Patients 35-65 ans, familles, soucieux de leur santé",
        "platforms_priority": ["linkedin", "facebook", "instagram"],
        "content_pillars": [
            "Prévention et conseils santé",
            "Démystification d'idées reçues",
            "Informations pathologies courantes",
            "Bien-être et hygiène de vie",
            "Actualités médicales vulgarisées",
        ],
        "viral_hooks": [
            "Saviez-vous que...",
            "Idée reçue : [mythe] — La vérité...",
            "Ce que votre médecin ne dit pas toujours...",
            "Symptôme souvent ignoré...",
            "Pourquoi [habitude] est mauvaise pour...",
        ],
        "cta": ["Prenez rendez-vous", "Consultez votre médecin", "Parlez-en à votre praticien"],
        "taboo_subjects": [
            "Diagnostic à distance",
            "Prescription de médicaments",
            "Critique d'autres professionnels de santé",
            "Affirmations thérapeutiques non prouvées",
        ],
        "legal_constraints": [
            "Ordre National des Médecins (CNOM) — pas de publicité directe ni racolage",
            "Pas de promesse de guérison",
            "Toujours recommander une consultation en personne",
            "RGPD santé — jamais de données patients identifiables",
        ],
        "best_formats": {
            "linkedin": "Articles de fond, carousels informatifs, vidéos courtes",
            "facebook": "Posts éducatifs avec infographies simples",
            "instagram": "Carousels mythes vs réalités, Reels vulgarisation",
        },
        "posting_times": {"linkedin": ["08:00", "12:00"], "facebook": ["10:00", "19:00"]},
        "hashtag_strategy": ["#santé", "#médecine", "#prévention", "#bienêtre"],
        "video_style": "breakout_v4",
        "content_ratio": {"video": 0.2, "image": 0.5, "text": 0.3},
    },
    "dentiste": {
        "label": "🦷 Dentiste / Chirurgien-dentiste",
        "tone": {"expert": 0.8, "warmth": 0.8, "humor": 0.2, "urgency": 0.4},
        "audience": "Patients 25-60 ans, parents pour enfants",
        "platforms_priority": ["instagram", "facebook", "linkedin"],
        "content_pillars": [
            "Prévention dentaire",
            "Esthétique dentaire",
            "Avant/Après (anonymisé + consentement)",
            "Conseils hygiène quotidienne",
        ],
        "viral_hooks": [
            "Le secret d'un sourire parfait...",
            "Erreur que tout le monde fait avec sa brosse à dents...",
            "Résultat après 1 séance de blanchiment...",
        ],
        "cta": ["Prenez rendez-vous", "Consultation gratuite", "Appelez notre cabinet"],
        "taboo_subjects": [
            "Photos de patients sans consentement écrit",
            "Garanties de résultats esthétiques",
        ],
        "legal_constraints": [
            "Réglementation publicité médicale CNOM",
            "Consentement éclairé obligatoire pour photos",
            "Ordre des Chirurgiens-Dentistes",
        ],
        "best_formats": {
            "instagram": "Before/after (anonymisé), Reels conseils, Stories Q&A",
            "facebook": "Posts éducatifs, témoignages texte",
        },
        "posting_times": {"instagram": ["09:00", "18:00"], "facebook": ["10:00", "18:30"]},
        "hashtag_strategy": ["#dentiste", "#sourire", "#santébuccodentaire", "#[ville]"],
        "video_style": "breakout_v4",
        "content_ratio": {"video": 0.3, "image": 0.5, "text": 0.2},
    },
    "pharmacie": {
        "label": "💊 Pharmacie / Parapharmacie",
        "tone": {"expert": 0.8, "warmth": 0.7, "humor": 0.2, "urgency": 0.5},
        "audience": "Grand public, personnes âgées, parents",
        "platforms_priority": ["facebook", "instagram"],
        "content_pillars": [
            "Conseils santé saisonniers",
            "Nouveaux produits parapharmacie",
            "Prévention et bien-être",
            "Conseils hygiène de vie",
        ],
        "viral_hooks": [
            "Pour cet hiver, pensez à...",
            "Ce que vous ignorez sur [produit courant]...",
            "Alternative naturelle à...",
        ],
        "cta": ["Venez en officine", "Demandez conseil à votre pharmacien"],
        "taboo_subjects": [
            "Prescription médicale",
            "Automédication dangereuse",
            "Comparaison de prix de médicaments listés",
        ],
        "legal_constraints": [
            "Ordre National des Pharmaciens",
            "Réglementation ANSM",
            "Pas de publicité sur médicaments listés (soumis à prescription)",
        ],
        "best_formats": {
            "facebook": "Posts informatifs saisonniers + conseils",
            "instagram": "Infographies bien-être + nouveautés",
        },
        "posting_times": {"facebook": ["09:00", "17:00"]},
        "hashtag_strategy": ["#pharmacie", "#santé", "#bienêtre", "#[ville]"],
        "video_style": "breakout_v4",
        "content_ratio": {"video": 0.2, "image": 0.4, "text": 0.4},
    },
    "coiffeur": {
        "label": "💇 Coiffeur / Salon de coiffure",
        "tone": {"expert": 0.5, "warmth": 0.9, "humor": 0.6, "urgency": 0.5},
        "audience": "Femmes 20-50 ans, tendances mode",
        "platforms_priority": ["instagram", "tiktok", "facebook"],
        "content_pillars": [
            "Transformations avant/après",
            "Tendances coloration saison",
            "Conseils entretien cheveux",
            "Coulisses du salon et équipe",
            "Inspirations coiffures",
        ],
        "viral_hooks": [
            "Transformation incroyable en [X] heures...",
            "La technique que les coiffeurs ne partagent pas...",
            "Avant/Après : vous n'allez pas croire...",
            "La tendance [saison] qui cartonne...",
        ],
        "cta": ["Réservez votre transformation", "Appelez pour un rdv", "DM pour tarifs"],
        "taboo_subjects": [],
        "legal_constraints": [],
        "best_formats": {
            "instagram": "Reels transformation + Feed résultats + Stories coulisses",
            "tiktok": "Before/after avec musique tendance, tutoriels coiffure",
        },
        "posting_times": {
            "instagram": ["10:00", "18:00", "20:00"],
            "tiktok": ["12:00", "19:00", "21:00"],
        },
        "hashtag_strategy": ["#coiffeur", "#hair", "#coloration", "#[ville]", "#transformation"],
        "video_style": "breakout_v4",
        "content_ratio": {"video": 0.6, "image": 0.3, "text": 0.1},
    },
    "estheticienne": {
        "label": "💅 Esthéticienne / Institut de beauté",
        "tone": {"expert": 0.5, "warmth": 0.9, "humor": 0.4, "urgency": 0.5},
        "audience": "Femmes 20-55 ans, bien-être et beauté",
        "platforms_priority": ["instagram", "tiktok", "facebook"],
        "content_pillars": [
            "Soins du visage et résultats",
            "Épilation et soins corps",
            "Nail art et ongles",
            "Conseils beauté quotidiens",
            "Avant/Après soins",
        ],
        "viral_hooks": [
            "Le soin secret des stars...",
            "Pourquoi votre peau a besoin de...",
            "Résultat après 1 séance...",
        ],
        "cta": ["Réservez votre soin", "Offrez un bon cadeau", "Premier soin à -20%"],
        "taboo_subjects": [],
        "legal_constraints": ["Pas de promesses médicales sur les soins cosmétiques"],
        "best_formats": {
            "instagram": "Reels techniques + résultats, Stories Q&A beauté",
            "tiktok": "Soins en cours, extractions (ASMR), résultats",
        },
        "posting_times": {"instagram": ["09:00", "18:00"], "tiktok": ["18:00", "21:00"]},
        "hashtag_strategy": ["#esthétique", "#beauté", "#skincare", "#[ville]"],
        "video_style": "breakout_v4",
        "content_ratio": {"video": 0.5, "image": 0.4, "text": 0.1},
    },
    "coach_sportif": {
        "label": "🏋️ Coach sportif / Salle de sport",
        "tone": {"expert": 0.6, "warmth": 0.7, "humor": 0.4, "urgency": 0.7},
        "audience": "25-45 ans actifs cherchant transformation",
        "platforms_priority": ["instagram", "tiktok", "youtube"],
        "content_pillars": [
            "Transformations clients (avec accord)",
            "Exercices et tutoriels pratiques",
            "Nutrition et récupération",
            "Motivation quotidienne",
            "Programmes et challenges",
        ],
        "viral_hooks": [
            "Ce client a perdu [X]kg en [Y] semaines...",
            "L'exercice que TOUT le monde fait mal...",
            "Challenge [X] jours : qui est partant ?",
            "Ce que les pros font que tu ne fais pas...",
        ],
        "cta": ["Rejoignez le programme", "Bilan gratuit", "DM pour commencer"],
        "taboo_subjects": [
            "Promesses de résultats garantis sans effort",
            "Conseils médicaux sans qualification",
        ],
        "legal_constraints": [
            "Mention 'les résultats peuvent varier' si avant/après",
            "Distinction coaching / médecine",
        ],
        "best_formats": {
            "instagram": "Reels exercices 30s, Stories motivation, Carousels nutrition",
            "tiktok": "Exercices courts, transformations, duet challenges",
        },
        "posting_times": {
            "instagram": ["06:30", "12:00", "18:00"],
            "tiktok": ["07:00", "12:30", "19:00"],
        },
        "hashtag_strategy": ["#coaching", "#fitness", "#transformation", "#sport", "#motivation"],
        "video_style": "breakout_v4",
        "content_ratio": {"video": 0.6, "image": 0.3, "text": 0.1},
    },
    "coach_vie": {
        "label": "🎯 Coach de vie / Développement personnel",
        "tone": {"expert": 0.5, "warmth": 0.9, "humor": 0.3, "urgency": 0.5},
        "audience": "25-50 ans en transition professionnelle ou personnelle",
        "platforms_priority": ["linkedin", "instagram", "youtube"],
        "content_pillars": [
            "Mindset et croissance personnelle",
            "Gestion du temps et productivité",
            "Confiance en soi",
            "Success stories clients (anonymisées)",
            "Outils et méthodes pratiques",
        ],
        "viral_hooks": [
            "Ce que les personnes qui réussissent font le matin...",
            "La vraie raison pour laquelle vous procrastinez...",
            "Testé pendant 30 jours : voici ce qui s'est passé...",
        ],
        "cta": ["Réservez une session découverte", "Rejoignez le programme", "Guide gratuit en bio"],
        "taboo_subjects": [
            "Promesses de revenus garantis",
            "Guérison de troubles mentaux diagnostiqués",
        ],
        "legal_constraints": ["Distinction coaching / thérapie / médecine obligatoire"],
        "best_formats": {
            "linkedin": "Posts longs à valeur, carrousels, articles de fond",
            "instagram": "Citations inspirantes, Reels conseil 60s, Stories Q&A",
        },
        "posting_times": {"linkedin": ["07:00", "12:00"], "instagram": ["08:00", "19:00"]},
        "hashtag_strategy": ["#coaching", "#developpementpersonnel", "#mindset", "#leadership"],
        "video_style": "breakout_v4",
        "content_ratio": {"video": 0.3, "image": 0.4, "text": 0.3},
    },
    "avocat": {
        "label": "⚖️ Avocat / Cabinet juridique",
        "tone": {"expert": 0.95, "warmth": 0.5, "humor": 0.05, "urgency": 0.4},
        "audience": "Particuliers et professionnels avec besoins juridiques",
        "platforms_priority": ["linkedin", "facebook"],
        "content_pillars": [
            "Vos droits expliqués simplement",
            "Actualités juridiques commentées",
            "FAQ droit du travail / famille / immobilier",
            "Mises en garde pratiques",
        ],
        "viral_hooks": [
            "Vos droits en cas de [situation courante]...",
            "Ce que dit vraiment la loi sur...",
            "Erreur juridique que tout le monde fait...",
            "Depuis le [date], vous avez le droit de...",
        ],
        "cta": ["Consultation gratuite", "Contactez notre cabinet", "Prenez rendez-vous"],
        "taboo_subjects": [
            "Conseils juridiques personnalisés publics",
            "Promesses de résultats de procès",
            "Critique nommée d'autres avocats",
        ],
        "legal_constraints": [
            "Ordre des Avocats — réglementation publicité stricte",
            "Pas de démarchage actif",
            "Mentions légales obligatoires sur tous supports",
            "Confidentialité client absolue",
        ],
        "best_formats": {
            "linkedin": "Articles de fond, actualités juridiques vulgarisées",
            "facebook": "Posts éducatifs droit pratique du quotidien",
        },
        "posting_times": {"linkedin": ["08:00", "12:30"], "facebook": ["10:00", "18:00"]},
        "hashtag_strategy": ["#droit", "#juridique", "#avocat", "#[domaine]"],
        "video_style": "breakout_v4",
        "content_ratio": {"video": 0.1, "image": 0.3, "text": 0.6},
    },
    "comptable": {
        "label": "📊 Expert-comptable / Cabinet comptable",
        "tone": {"expert": 0.9, "warmth": 0.6, "humor": 0.1, "urgency": 0.5},
        "audience": "Entrepreneurs, TPE/PME, auto-entrepreneurs",
        "platforms_priority": ["linkedin", "facebook"],
        "content_pillars": [
            "Fiscalité pratique vulgarisée",
            "Obligations comptables calendaires",
            "Optimisation fiscale légale",
            "Actualités fiscales et sociales",
            "Conseils création d'entreprise",
        ],
        "viral_hooks": [
            "Ce que l'administration fiscale ne vous dit pas...",
            "Erreur comptable qui coûte cher à corriger...",
            "Astuce fiscale 100% légale pour [profil]...",
        ],
        "cta": ["Demandez un audit gratuit", "Contactez notre cabinet", "Rdv découverte"],
        "taboo_subjects": ["Conseils d'optimisation fiscale agressive / fraude"],
        "legal_constraints": [
            "Ordre des Experts-Comptables",
            "Secret professionnel absolu",
            "Mentions légales obligatoires",
        ],
        "best_formats": {
            "linkedin": "Articles techniques vulgarisés, infographies fiscales calendaires",
        },
        "posting_times": {"linkedin": ["08:00", "12:00"]},
        "hashtag_strategy": ["#comptabilité", "#fiscalité", "#entreprise", "#entrepreneur"],
        "video_style": "breakout_v4",
        "content_ratio": {"video": 0.1, "image": 0.3, "text": 0.6},
    },
    "agent_immobilier": {
        "label": "🏠 Agent immobilier / Agence",
        "tone": {"expert": 0.7, "warmth": 0.7, "humor": 0.2, "urgency": 0.8},
        "audience": "Acheteurs, vendeurs, investisseurs 30-60 ans",
        "platforms_priority": ["facebook", "instagram", "linkedin"],
        "content_pillars": [
            "Biens à vendre avec photos premium",
            "Conseils marché immobilier local",
            "Tendances prix dans [ville/quartier]",
            "Processus achat/vente vulgarisé",
            "Success stories clients (anonymisées)",
        ],
        "viral_hooks": [
            "Cette maison part en 48h...",
            "Prix au m² à [ville] : la vérité...",
            "Erreur que font 80% des acheteurs...",
            "Ce bien vient de rentrer en exclusivité...",
        ],
        "cta": ["Estimez votre bien gratuitement", "Contactez-moi", "Visite virtuelle disponible"],
        "taboo_subjects": [
            "Affirmations sur évolution future certaine des prix",
            "Dénigrement de concurrents",
        ],
        "legal_constraints": [
            "Loi Hoguet — carte professionnelle T obligatoire",
            "Mentions annonce obligatoires (prix, surface, honoraires %)",
            "Pas de publicité mensongère sur les biens",
        ],
        "best_formats": {
            "facebook": "Posts biens avec photos, témoignages, conseils marché",
            "instagram": "Photos premium biens, Reels visite virtuelle, Stories nouveautés",
        },
        "posting_times": {"facebook": ["10:00", "18:00"], "instagram": ["12:00", "18:00"]},
        "hashtag_strategy": ["#immobilier", "#[ville]", "#achat", "#investissement"],
        "video_style": "cinematic_food",
        "content_ratio": {"video": 0.4, "image": 0.5, "text": 0.1},
    },
    "ecommerce": {
        "label": "🛒 E-commerce / Boutique en ligne",
        "tone": {"expert": 0.4, "warmth": 0.8, "humor": 0.5, "urgency": 0.9},
        "audience": "Acheteurs en ligne, tous âges selon niche produit",
        "platforms_priority": ["instagram", "tiktok", "facebook"],
        "content_pillars": [
            "Présentation et démonstration produits",
            "Unboxing et reviews clients",
            "Promotions et offres flash",
            "UGC et témoignages clients",
            "Behind the scenes fabrication/sélection",
        ],
        "viral_hooks": [
            "Seulement [X] restants en stock...",
            "Ce produit change tout pour...",
            "Nos clients adorent ce produit parce que...",
            "Offre flash : -[X]% jusqu'à minuit...",
        ],
        "cta": ["Achetez maintenant", "Lien en bio", "Code promo : [CODE]", "Livraison gratuite"],
        "taboo_subjects": ["Fausses urgences fabriquées", "Promesses trompeuses sur les produits"],
        "legal_constraints": [
            "Droit de rétractation 14 jours obligatoire",
            "Prix barrés légaux (ancien prix réel)",
            "Mentions légales e-commerce",
        ],
        "best_formats": {
            "instagram": "Reels produit 15-30s, Stories flash promo, Feed lifestyle",
            "tiktok": "Unboxing, reviews, haul, transformation avec produit",
        },
        "posting_times": {
            "instagram": ["11:00", "19:00", "21:00"],
            "tiktok": ["12:00", "18:00", "21:00"],
        },
        "hashtag_strategy": ["#[produit]", "#shopping", "#nouveauté", "#promo"],
        "video_style": "cinematic_food",
        "content_ratio": {"video": 0.5, "image": 0.4, "text": 0.1},
    },
    "formateur": {
        "label": "🎓 Formateur / Centre de formation",
        "tone": {"expert": 0.8, "warmth": 0.7, "humor": 0.3, "urgency": 0.6},
        "audience": "Professionnels en reconversion, étudiants, entreprises",
        "platforms_priority": ["linkedin", "youtube", "instagram"],
        "content_pillars": [
            "Conseils métier gratuits à valeur",
            "Success stories apprenants (avec accord)",
            "Présentation des formations",
            "Actualités du secteur ciblé",
            "Témoignages employeurs et recruteurs",
        ],
        "viral_hooks": [
            "Mes élèves gagnent en moyenne [X]€/mois après...",
            "Le skill le plus demandé en [année]...",
            "Reconversion réussie en [X] mois...",
            "Ce que les recruteurs cherchent vraiment...",
        ],
        "cta": ["Inscrivez-vous", "Demandez la brochure", "Session info gratuite"],
        "taboo_subjects": ["Garanties d'emploi", "Revenus garantis post-formation"],
        "legal_constraints": [
            "Qualiopi si CPF — taux de satisfaction véridiques",
            "Mentions légales formation obligatoires",
            "Taux d'insertion et de placement vérifiables",
        ],
        "best_formats": {
            "linkedin": "Articles expertise, carousels conseils pratiques",
            "youtube": "Tutoriels, témoignages, webinaires",
        },
        "posting_times": {"linkedin": ["08:00", "12:00"], "instagram": ["09:00", "18:00"]},
        "hashtag_strategy": ["#formation", "#reconversion", "#[métier]", "#emploi"],
        "video_style": "breakout_v4",
        "content_ratio": {"video": 0.3, "image": 0.3, "text": 0.4},
    },
    "artisan": {
        "label": "🔨 Artisan / PME locale",
        "tone": {"expert": 0.7, "warmth": 0.8, "humor": 0.3, "urgency": 0.5},
        "audience": "Locaux 30-65 ans, propriétaires, professionnels",
        "platforms_priority": ["facebook", "instagram", "google_business"],
        "content_pillars": [
            "Chantiers en cours et réalisations",
            "Avant/Après travaux spectaculaires",
            "Conseils entretien et prévention",
            "Témoignages clients satisfaits",
            "Équipe et savoir-faire artisanal",
        ],
        "viral_hooks": [
            "Chantier terminé en [X] jours...",
            "Transformation incroyable de cette [pièce]...",
            "Le problème que tout le monde ignore dans sa [maison]...",
        ],
        "cta": ["Devis gratuit sous 24h", "Contactez-nous", "Appelez le [numéro]"],
        "taboo_subjects": [],
        "legal_constraints": [
            "Garantie décennale à mentionner si applicable",
            "Attestation d'assurance responsabilité civile",
        ],
        "best_formats": {
            "facebook": "Réalisations photos avant/après, avis Google, témoignages",
            "instagram": "Photos premium réalisations, Reels chantier",
        },
        "posting_times": {"facebook": ["08:00", "12:00", "17:00"]},
        "hashtag_strategy": ["#artisan", "#[métier]", "#[ville]", "#rénovation"],
        "video_style": "breakout_v4",
        "content_ratio": {"video": 0.3, "image": 0.5, "text": 0.2},
    },
    "saas": {
        "label": "💻 SaaS / Startup Tech",
        "tone": {"expert": 0.7, "warmth": 0.6, "humor": 0.4, "urgency": 0.7},
        "audience": "Entrepreneurs, PME, professionnels du digital",
        "platforms_priority": ["linkedin", "twitter", "youtube"],
        "content_pillars": [
            "Product updates et nouvelles features",
            "Use cases et témoignages clients",
            "Tutoriels et how-to pratiques",
            "Contenu éducatif du secteur",
            "Behind the scenes équipe",
        ],
        "viral_hooks": [
            "Notre nouvelle feature qui fait gagner [X]h/semaine...",
            "Nos clients économisent [X]€/mois grâce à...",
            "Le problème que [outil concurrent] ne résout pas...",
        ],
        "cta": ["Essai gratuit 14 jours", "Demandez une démo", "Voir les tarifs"],
        "taboo_subjects": ["Dénigrement nommé de concurrents"],
        "legal_constraints": ["RGPD", "Mentions légales SaaS", "CGU accessibles"],
        "best_formats": {
            "linkedin": "Product updates, thought leadership, témoignages clients",
            "twitter": "Quick tips, threads, actualités",
            "youtube": "Tutoriels, webinaires, démos produit",
        },
        "posting_times": {
            "linkedin": ["08:00", "12:00", "17:00"],
            "twitter": ["09:00", "14:00", "19:00"],
        },
        "hashtag_strategy": ["#SaaS", "#startup", "#[niche]", "#productivité"],
        "video_style": "cinematic_food",
        "content_ratio": {"video": 0.3, "image": 0.3, "text": 0.4},
    },
}

# ─── ALIASES ──────────────────────────────────────────────────────────────────

NICHE_ALIASES = {
    "médecin": "medecin", "doctor": "medecin", "chirurgien": "medecin",
    "généraliste": "medecin", "spécialiste": "medecin",
    "dentiste": "dentiste", "dental": "dentiste",
    "pharmacien": "pharmacie", "pharmacie": "pharmacie",
    "coach": "coach_vie", "personal trainer": "coach_sportif",
    "gym": "coach_sportif", "fitness": "coach_sportif", "salle de sport": "coach_sportif",
    "coiffeur": "coiffeur", "coiffeuse": "coiffeur", "hair": "coiffeur", "salon coiffure": "coiffeur",
    "esthéticien": "estheticienne", "esthéticienne": "estheticienne",
    "beauté": "estheticienne", "nail art": "estheticienne",
    "avocat": "avocat", "juriste": "avocat", "notaire": "avocat",
    "comptable": "comptable", "expert comptable": "comptable", "expert-comptable": "comptable",
    "immobilier": "agent_immobilier", "agence immo": "agent_immobilier",
    "agent immo": "agent_immobilier", "promoteur": "agent_immobilier",
    "boutique": "ecommerce", "e-commerce": "ecommerce", "shop": "ecommerce",
    "formation": "formateur", "école": "formateur", "centre de formation": "formateur",
    "plombier": "artisan", "électricien": "artisan", "maçon": "artisan",
    "peintre": "artisan", "menuisier": "artisan", "couvreur": "artisan",
    "startup": "saas", "app": "saas", "logiciel": "saas", "application": "saas",
    "restaurant": "restaurant", "café": "restaurant", "pizzeria": "restaurant",
    "brasserie": "restaurant", "traiteur": "restaurant", "snack": "restaurant",
    "boulangerie": "boulangerie", "pâtisserie": "boulangerie", "viennoiserie": "boulangerie",
}


def detect_niche(business_type: str) -> dict:
    """Détecte la niche depuis le type de business. Retourne le profil complet."""
    if not business_type:
        return NICHES["restaurant"]

    key = business_type.lower().strip()

    if key in NICHES:
        return NICHES[key]

    if key in NICHE_ALIASES:
        return NICHES[NICHE_ALIASES[key]]

    for alias, niche_key in NICHE_ALIASES.items():
        if alias in key or key in alias:
            return NICHES[niche_key]

    return NICHES["restaurant"]


def get_niche_system_prompt(niche_profile: dict, brand_dna: dict) -> str:
    """
    Génère le system prompt Ilyas adapté niche + DNA.
    Ce prompt doit être mis en cache via cache_control: {"type": "ephemeral"}.
    """
    constraints = "\n".join(f"⚠️ {c}" for c in niche_profile["legal_constraints"]) \
        if niche_profile["legal_constraints"] else "Aucune contrainte légale spécifique."

    taboo = ", ".join(niche_profile["taboo_subjects"]) \
        if niche_profile["taboo_subjects"] else "Aucun sujet tabou spécifique."

    platforms_text = "\n".join(
        f"• {p.capitalize()} : {spec}"
        for p, spec in niche_profile["best_formats"].items()
    )

    hooks_text = "\n".join(f"• {h}" for h in niche_profile["viral_hooks"])

    tone = niche_profile["tone"]
    tone_parts = []
    if tone.get("expert", 0) > 0.7:
        tone_parts.append("très expert et autoritaire")
    elif tone.get("expert", 0) > 0.4:
        tone_parts.append("expert mais accessible")
    if tone.get("warmth", 0) > 0.7:
        tone_parts.append("chaleureux et proche des gens")
    if tone.get("humor", 0) > 0.4:
        tone_parts.append("avec une touche d'humour")
    if tone.get("urgency", 0) > 0.6:
        tone_parts.append("avec sens de l'urgence et de l'action")
    tone_str = ", ".join(tone_parts) if tone_parts else "professionnel et bienveillant"

    memories = brand_dna.get("memories", "")

    return f"""Tu es Ilyas, Community Manager IA expert en marketing digital et réseaux sociaux.
Tu travailles EXCLUSIVEMENT pour : {brand_dna.get('name', 'ce business')}.

<niche_expertise>
Secteur : {niche_profile['label']}
Audience cible : {niche_profile['audience']}
Ton de communication : {tone_str}
Piliers de contenu :
{chr(10).join('• ' + p for p in niche_profile['content_pillars'])}
Plateformes prioritaires : {', '.join(niche_profile['platforms_priority'])}
</niche_expertise>

<legal_constraints>
{constraints}
</legal_constraints>

<taboo_subjects>
Ne JAMAIS aborder ni suggérer : {taboo}
</taboo_subjects>

<brand_dna>
Nom : {brand_dna.get('name', 'N/A')}
Description : {brand_dna.get('description', 'N/A')}
Valeurs : {brand_dna.get('values', 'N/A')}
Ton de marque : {brand_dna.get('voice', 'N/A')}
Cible : {brand_dna.get('target_audience', niche_profile['audience'])}
Localisation : {brand_dna.get('location', 'N/A')}
{f"Contexte mémorisé :{chr(10)}{memories}" if memories else ""}
</brand_dna>

<platform_formats>
{platforms_text}
</platform_formats>

<viral_hooks>
Hooks qui performent dans cette niche :
{hooks_text}
</viral_hooks>

<strategic_mission>
Ton objectif est UNIQUE : générer de l'argent pour ce business.
Tu penses toujours en termes de ROI, conversions, notoriété locale, fidélisation.
Chaque post doit servir un objectif business mesurable.
Tu es un SNIPER du marketing digital, pas un générateur de contenu générique.
Tu adaptes chaque contenu aux codes spécifiques de la plateforme cible.
</strategic_mission>"""

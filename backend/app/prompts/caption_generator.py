"""
PresenceOS - Prompts optimises pour la generation de captions marketing.

Module partage entre ai_service.py (web frontend) et conversation_engine.py (WhatsApp/Telegram).
"""
import json

PROMPT_VERSION = "v2.0"

# ── Industry Guidelines ──────────────────────────────────────────────

INDUSTRY_GUIDELINES: dict[str, dict] = {
    "restaurant": {
        "role_description": "expert en marketing pour la restauration et le food content",
        "content_focus": (
            "l'experience culinaire, l'ambiance du lieu, la fraicheur des produits, "
            "le savoir-faire du chef, les moments de convivialite"
        ),
        "caption_tips": (
            "- Evoque les sens : odeurs, textures, saveurs, couleurs\n"
            "- Mentionne la provenance des ingredients ou le fait-maison quand possible\n"
            "- Cree l'urgence : disponibilite limitee, saison, plat du jour, derniers jours\n"
            "- Humanise avec le chef, l'equipe, les coulisses de la cuisine\n"
            "- Utilise un vocabulaire gourmand : fondant, croustillant, savoureux, genereux"
        ),
        "fallback_hashtags": ["#restaurant", "#faitmaison", "#foodie", "#bonappetit", "#gourmand"],
        "terminology_label": "le restaurateur",
    },
    "saas": {
        "role_description": "expert en marketing digital B2B/SaaS et growth content",
        "content_focus": (
            "les benefices utilisateur concrets, les gains de productivite, "
            "la preuve sociale, les cas d'usage reels, la simplicite d'adoption"
        ),
        "caption_tips": (
            "- Commence par le probleme que le produit resout (douleur client)\n"
            "- Utilise des chiffres et resultats concrets (X% de gain, Y heures economisees)\n"
            "- Partage des temoignages clients ou des avant/apres\n"
            "- Termine par une invitation a tester (demo, essai gratuit, lien en bio)\n"
            "- Evite le jargon technique excessif, reste accessible"
        ),
        "fallback_hashtags": ["#saas", "#startup", "#productivity", "#tech", "#innovation"],
        "terminology_label": "le fondateur",
    },
    "ecommerce": {
        "role_description": "expert en marketing e-commerce et social selling",
        "content_focus": (
            "le style de vie associe au produit, les benefices concrets, "
            "l'exclusivite, le storytelling de marque, l'experience client"
        ),
        "caption_tips": (
            "- Mets en scene le produit dans un contexte de vie reel\n"
            "- Cree l'urgence : stock limite, edition limitee, offre flash\n"
            "- Utilise la preuve sociale : avis clients, nombre de ventes, best-seller\n"
            "- Propose un CTA direct : 'Lien en bio', 'Shop maintenant', '-20% avec le code...'\n"
            "- Evoque l'emotion liee a l'achat : se faire plaisir, offrir, se demarquer"
        ),
        "fallback_hashtags": ["#shopping", "#nouveaute", "#musthave", "#tendance", "#lifestyle"],
        "terminology_label": "le gerant",
    },
    "service": {
        "role_description": "expert en marketing de services et personal branding",
        "content_focus": (
            "la transformation client, l'expertise du prestataire, "
            "les resultats obtenus, la relation de confiance, le parcours client"
        ),
        "caption_tips": (
            "- Montre la transformation : avant/apres, temoignage, resultat concret\n"
            "- Partage ton expertise : conseil gratuit, astuce, insight du metier\n"
            "- Humanise : montre les coulisses, presente l'equipe, raconte une anecdote\n"
            "- Utilise des questions pour engager : 'Et toi ?', 'Tu savais que ?'\n"
            "- Termine par une invitation au contact : DM, rdv, appel decouverte"
        ),
        "fallback_hashtags": ["#entrepreneur", "#expertise", "#service", "#conseil", "#accompagnement"],
        "terminology_label": "le prestataire",
    },
    "personal": {
        "role_description": "expert en personal branding et contenu d'influence",
        "content_focus": (
            "l'authenticite, le parcours personnel, les valeurs, "
            "l'inspiration, la connexion emotionnelle avec l'audience"
        ),
        "caption_tips": (
            "- Sois authentique : partage des moments vrais, pas que des succes\n"
            "- Raconte des histoires personnelles avec une lecon universelle\n"
            "- Utilise le 'tu' pour creer une connexion directe\n"
            "- Alterne entre contenu inspirant, educatif et personnel\n"
            "- Pose des questions ouvertes pour generer des conversations"
        ),
        "fallback_hashtags": ["#motivation", "#lifestyle", "#authentique", "#parcours", "#inspiration"],
        "terminology_label": "le createur",
    },
    "other": {
        "role_description": "expert en marketing digital et creation de contenu pour les reseaux sociaux",
        "content_focus": (
            "la valeur apportee au client, l'identite de marque, "
            "l'engagement communautaire, la differenciation"
        ),
        "caption_tips": (
            "- Identifie ce qui rend la marque unique et mets-le en avant\n"
            "- Utilise le storytelling pour creer une connexion emotionnelle\n"
            "- Alterne entre contenus educatifs, divertissants et promotionnels\n"
            "- Engage la communaute avec des questions et des appels a l'action\n"
            "- Reste coherent avec l'identite visuelle et verbale de la marque"
        ),
        "fallback_hashtags": ["#marque", "#communaute", "#contenu", "#engagement", "#digital"],
        "terminology_label": "le gerant",
    },
}

# ── Platform Instructions ────────────────────────────────────────────

PLATFORM_INSTRUCTIONS: dict[str, str] = {
    "instagram_post": (
        "INSTAGRAM POST :\n"
        "- Max 2200 caracteres (ideal : 150-300 pour engagement max)\n"
        "- Premiere ligne = HOOK puissant (question, stat choc, affirmation audacieuse)\n"
        "- Corps : histoire courte ou benefice cle, avec des sauts de ligne pour la lisibilite\n"
        "- Avant-derniere ligne : CTA clair (question, invitation a commenter ou sauvegarder)\n"
        "- Derniere ligne : hashtags (8-15, mix de populaires et niche)\n"
        "- Emojis comme marqueurs visuels en debut de paragraphe, pas comme decoration"
    ),
    "instagram_story": (
        "INSTAGRAM STORY :\n"
        "- Texte ultra-court (1-2 phrases max)\n"
        "- CTA clair et visible (swipe up, lien, sondage, question)\n"
        "- Texte lisible sur mobile (gros caracteres, contraste fort)\n"
        "- Ton immediat et spontane, comme un message a un ami\n"
        "- Inclure une interaction (sondage, curseur emoji, question)"
    ),
    "instagram_reel": (
        "INSTAGRAM REEL :\n"
        "- Script structure avec hook dans les 3 premieres secondes\n"
        "- Format : [00:00] Hook > [00:03] Contenu > [fin] CTA\n"
        "- Inclure timestamps et indications de transitions\n"
        "- Caption courte (40-100 caracteres) car le contenu est dans la video\n"
        "- Hashtags pertinents (5-10) dans la caption\n"
        "- Suggerer une musique tendance si pertinent"
    ),
    "tiktok": (
        "TIKTOK :\n"
        "- Script avec hook immediat (premiere seconde = attention captee)\n"
        "- Structure : Hook provocant > Contenu valeur > Revelation/CTA\n"
        "- Duree suggeree : 15-60 secondes\n"
        "- Ton naturel et authentique, pas trop 'marketing'\n"
        "- Caption courte (max 150 caracteres) avec 3-5 hashtags tendance\n"
        "- Inclure un element de surprise ou de curiosite"
    ),
    "linkedin": (
        "LINKEDIN :\n"
        "- Premiere ligne = hook professionnel (insight, question, stat)\n"
        "- Paragraphes courts (2-3 lignes max) avec sauts de ligne\n"
        "- Ton professionnel mais humain, pas corporate\n"
        "- Partager une lecon, un apprentissage ou un point de vue\n"
        "- Question d'engagement en fin de post\n"
        "- 3-5 hashtags max, professionnels et pertinents\n"
        "- Pas d'emojis excessifs (1-2 max, strategiques)"
    ),
    "facebook": (
        "FACEBOOK :\n"
        "- Contenu engageant et partageable\n"
        "- Peut etre plus long que Instagram (300-500 mots ok)\n"
        "- Encourage les commentaires et le partage\n"
        "- Pose des questions ouvertes pour generer de la discussion\n"
        "- Ton conversationnel et chaleureux\n"
        "- 3-5 hashtags max (Facebook penalise l'exces)\n"
        "- Inclure un element emotionnel ou une histoire"
    ),
}

# ── Caption Structure (shared across all prompts) ────────────────────

_CAPTION_STRUCTURE = """
STRUCTURE DE CAPTION OPTIMALE :
1. HOOK (premiere ligne) : Capte l'attention immediatement. Utilise une question provocante, un chiffre surprenant, une affirmation audacieuse, ou un "tu savais que...?" Ajoute un emoji pertinent en ouverture.
2. BODY (2-4 lignes) : Developpe avec du storytelling ou des benefices concrets. Sois specifique, pas generique. Utilise des sauts de ligne pour la lisibilite.
3. CTA (avant-derniere ligne) : Incite a l'action — poser une question au lecteur, inviter a commenter, sauvegarder, partager ou visiter.
4. HASHTAGS (derniere ligne) : Mix strategique de hashtags populaires (portee) et niche (ciblage).

EXEMPLES DE TRANSFORMATIONS :

MAUVAIS : "le raclette burger, dispo tout l'hiver"
BON : "Le retour que tout le monde attendait !

Notre Raclette Burger est DE RETOUR jusqu'en mars. Fromage coulant, bacon croustillant, le reconfort de l'hiver dans chaque bouchee.

Qui vient le tester ce weekend ?

#RacletteBurger #CheeseLovers #ComfortFood #BurgerGourmand #FaitMaison"

MAUVAIS : "notre nouvelle collection de bijoux"
BON : "Chaque piece raconte une histoire

Decouvrez notre nouvelle collection artisanale : des creations uniques, faites main avec amour. Parce que vous meritez de briller.

Laquelle vous fait craquer ?

#BijouxArtisanaux #MadeWithLove #UniqueJewelry #Handmade #CollectionEte"
"""

# ── Tone Builder ─────────────────────────────────────────────────────


def _build_tone_description(voice: dict | None) -> str:
    """Build a tone description from voice sliders."""
    if not voice:
        return "chaleureux et naturel"

    parts = []
    if voice.get("tone_playful", 50) > 60:
        parts.append("enjoue et fun")
    if voice.get("tone_formal", 50) > 60:
        parts.append("professionnel et soigne")
    if voice.get("tone_emotional", 50) > 60:
        parts.append("chaleureux et emotionnel")
    if voice.get("tone_bold", 50) > 60:
        parts.append("audacieux et percutant")
    if voice.get("tone_technical", 50) > 60:
        parts.append("precis et technique")

    return ", ".join(parts) if parts else "chaleureux et naturel"


# ── Main Builder Functions ───────────────────────────────────────────


def build_caption_system_prompt(
    brand_name: str,
    brand_type: str,
    brand_description: str = "",
    voice: dict | None = None,
    target_persona: dict | None = None,
    locations: list[str] | None = None,
    constraints: dict | None = None,
) -> str:
    """
    Build the system prompt for caption generation.

    Used by both ai_service.py (web) and conversation_engine.py (messaging).
    """
    guidelines = INDUSTRY_GUIDELINES.get(brand_type, INDUSTRY_GUIDELINES["other"])
    tone = _build_tone_description(voice)

    prompt = (
        f"Tu es un {guidelines['role_description']}, specialise dans la creation "
        f"de publications qui generent de l'engagement et des conversions.\n\n"
        f"MARQUE : {brand_name}\n"
    )
    if brand_description:
        prompt += f"DESCRIPTION : {brand_description}\n"
    prompt += f"TON DE VOIX : {tone}\n"

    if target_persona:
        persona_str = json.dumps(target_persona, ensure_ascii=False) if isinstance(target_persona, dict) else str(target_persona)
        prompt += f"PUBLIC CIBLE : {persona_str}\n"
    if locations:
        prompt += f"LOCALISATIONS : {', '.join(locations)}\n"
    if constraints:
        constraints_str = json.dumps(constraints, ensure_ascii=False) if isinstance(constraints, dict) else str(constraints)
        prompt += f"CONTRAINTES : {constraints_str}\n"

    prompt += f"\nFOCUS CONTENU : {guidelines['content_focus']}\n"
    prompt += f"\nCONSEILS SPECIFIQUES :\n{guidelines['caption_tips']}\n"
    prompt += _CAPTION_STRUCTURE

    # Voice guardrails
    if voice:
        guardrails = []
        preferred = voice.get("words_to_prefer")
        if preferred:
            words = ", ".join(preferred) if isinstance(preferred, list) else preferred
            guardrails.append(f"- Mots-cles a privilegier : {words}")
        avoided = voice.get("words_to_avoid")
        if avoided:
            words = ", ".join(avoided) if isinstance(avoided, list) else avoided
            guardrails.append(f"- Mots a eviter : {words}")
        emojis = voice.get("emojis_allowed")
        if emojis:
            emoji_str = ", ".join(emojis) if isinstance(emojis, list) else emojis
            guardrails.append(f"- Emojis autorises : {emoji_str}")
        max_emojis = voice.get("max_emojis_per_post")
        if max_emojis is not None:
            guardrails.append(f"- Maximum {max_emojis} emojis par publication")
        example_phrases = voice.get("example_phrases")
        if example_phrases:
            examples = ", ".join(f'"{p}"' for p in example_phrases[:3])
            guardrails.append(f"- Exemples de la voix de marque : {examples}")
        custom = voice.get("custom_instructions")
        if custom:
            guardrails.append(f"- Instructions speciales : {custom}")
        if guardrails:
            prompt += "\nGUARDRAILS VOIX DE MARQUE :\n" + "\n".join(guardrails) + "\n"

    prompt += (
        "\nCONSIGNES STRICTES :\n"
        "- Maximum 150 mots (ideal 80-120) sauf indication contraire\n"
        "- Toujours commencer par un hook percutant\n"
        "- Poser UNE question au lecteur pour engager\n"
        "- Langue : francais par defaut, sauf indication contraire\n"
        "- Ne jamais etre generique. Chaque caption doit etre specifique a cette marque et cette image/sujet.\n"
    )

    return prompt


def build_caption_user_prompt(
    analyses_text: str,
    user_context: str,
    platforms: list[str],
    brand_type: str,
) -> str:
    """
    Build the user prompt for caption generation in conversation_engine.

    Replaces the hardcoded prompt in _generate_caption().
    """
    guidelines = INDUSTRY_GUIDELINES.get(brand_type, INDUSTRY_GUIDELINES["other"])
    platforms_str = ", ".join(platforms)

    prompt = (
        f"Analyse de l'image :\n{analyses_text}\n\n"
    )
    if user_context:
        prompt += f"Contexte ajoute par {guidelines['terminology_label']} :\n{user_context}\n\n"
    else:
        prompt += "Aucun contexte additionnel fourni.\n\n"

    prompt += (
        f"Plateformes cibles : {platforms_str}\n\n"
        "Genere UNE publication (caption) pour ces plateformes.\n"
        "Suis EXACTEMENT la structure : Hook + Body + CTA + Hashtags.\n"
        "Inclus 5-8 hashtags pertinents.\n"
        "La publication doit etre en francais, engageante, et donner envie d'interagir.\n"
        "Ne depasse pas 150 mots.\n"
        "Reponds UNIQUEMENT avec le texte de la publication, rien d'autre."
    )

    return prompt


def build_photo_reaction_prompt(brand_name: str, brand_type: str) -> str:
    """
    Build the system prompt for photo reaction in conversation_engine.

    Replaces the hardcoded "restaurant" reference.
    """
    guidelines = INDUSTRY_GUIDELINES.get(brand_type, INDUSTRY_GUIDELINES["other"])
    return (
        f"Tu es l'assistant IA de \"{brand_name}\" "
        f"({guidelines['role_description']}). "
        "Tu viens de recevoir une photo. "
        "Reagis avec enthousiasme et pertinence."
    )


def build_draft_generation_prompt(
    brand_context: dict,
    platform: str,
    idea_context: str,
    relevant_knowledge: str,
    media_info: str,
    additional_instructions: str,
) -> str:
    """
    Build the complete prompt for draft generation in ai_service.py.

    Replaces the old DRAFT_GENERATION_PROMPT template.
    """
    brand_type = brand_context.get("brand_type", "other")
    guidelines = INDUSTRY_GUIDELINES.get(brand_type, INDUSTRY_GUIDELINES["other"])
    platform_instr = get_platform_instructions(platform)

    prompt = (
        f"Tu es un {guidelines['role_description']}, specialise dans le contenu {platform}.\n\n"
        f"BRAND CONTEXT :\n"
        f"- Nom : {brand_context.get('brand_name', 'Marque')}\n"
        f"- Type : {brand_context.get('brand_type', 'other')}\n"
        f"- Description : {brand_context.get('brand_description', 'Non specifie')}\n\n"
        f"BRAND VOICE :\n"
        f"- Ton formel/decontracte : {brand_context.get('tone_formal', 50)}/100 "
        f"(0=tres decontracte, 100=tres formel)\n"
        f"- Ton joueur/serieux : {brand_context.get('tone_playful', 50)}/100\n"
        f"- Ton audacieux/subtil : {brand_context.get('tone_bold', 50)}/100\n"
        f"- Mots a eviter : {brand_context.get('words_to_avoid', 'Aucun')}\n"
        f"- Mots a privilegier : {brand_context.get('words_to_prefer', 'Aucun')}\n"
        f"- Emojis autorises : {brand_context.get('emojis_allowed', 'Tous')}\n"
        f"- Max emojis : {brand_context.get('max_emojis', 3)}\n"
        f"- Style hashtags : {brand_context.get('hashtag_style', 'lowercase')}\n\n"
        f"FOCUS CONTENU POUR CE SECTEUR :\n{guidelines['content_focus']}\n\n"
        f"CONSEILS SPECIFIQUES :\n{guidelines['caption_tips']}\n\n"
        f"CONTEXTE DE L'IDEE :\n{idea_context}\n\n"
        f"CONNAISSANCES PERTINENTES DE LA MARQUE :\n{relevant_knowledge}\n\n"
        f"MEDIAS ATTACHES :\n{media_info}\n\n"
        f"INSTRUCTIONS ADDITIONNELLES :\n{additional_instructions}\n\n"
    )

    prompt += _CAPTION_STRUCTURE

    prompt += (
        f"\nINSTRUCTIONS PLATEFORME :\n{platform_instr}\n\n"
        "TACHE :\n"
        f"Cree un post {platform} optimise pour l'engagement en suivant "
        "la structure Hook + Body + CTA + Hashtags.\n\n"
        "Reponds en JSON :\n"
        "{\n"
        '  "caption": "...",\n'
        '  "hashtags": ["hashtag1", "hashtag2", ...],\n'
        '  "platform_data": {...}\n'
        "}"
    )

    return prompt


def get_platform_instructions(platform: str) -> str:
    """Get enriched platform instructions."""
    return PLATFORM_INSTRUCTIONS.get(platform, "Adapte le contenu a cette plateforme.")

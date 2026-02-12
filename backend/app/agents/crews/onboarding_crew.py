"""
PresenceOS — Onboarding Intelligent Adaptatif (Phase 2).

3 modes: FULL_AUTO, SEMI_AUTO, INTERVIEW.
~30 questions adaptatives organisees par categorie.
Skip automatique des reponses deja connues via scraping.
"""
import json
import re
from enum import Enum
from typing import Optional

from crewai import Crew, Agent, Process
from app.agents.config import get_crew_llm, get_crew_verbose
from app.agents.tools.web_scraper import WebScraperTool


# ── Modes d'onboarding ──────────────────────────────────────────────

class OnboardingMode(str, Enum):
    FULL_AUTO = "full_auto"       # site web + reseaux sociaux fournis
    SEMI_AUTO = "semi_auto"       # seulement site web OU reseaux sociaux
    INTERVIEW = "interview"       # rien fourni → questions conversationnelles


# ── Categories de questions ──────────────────────────────────────────

CATEGORY_ORDER = ["identity", "product", "audience", "voice", "goals"]


# ── Questions adaptatives (~30) ──────────────────────────────────────

ONBOARDING_QUESTIONS = [
    # ══════════════════════════════════════════════════════════════════
    # IDENTITY — Qui etes-vous ?
    # ══════════════════════════════════════════════════════════════════
    {
        "key": "business_name",
        "question": "Quel est le nom de votre entreprise ou marque ?",
        "type": "text",
        "category": "identity",
        "required": True,
        "modes": ["interview", "semi_auto"],
        "placeholder": "Ex: Family's Restaurant, Appy Solution...",
        "maps_to": "business_name",
    },
    {
        "key": "business_type",
        "question": "Quel est votre secteur d'activite ?",
        "type": "select",
        "category": "identity",
        "required": True,
        "modes": ["interview", "semi_auto"],
        "options": [
            {"value": "restaurant", "label": "Restaurant / Food"},
            {"value": "saas", "label": "SaaS / Tech"},
            {"value": "ecommerce", "label": "E-commerce"},
            {"value": "service", "label": "Service / Consulting"},
            {"value": "agency", "label": "Agence / Freelance"},
            {"value": "personal", "label": "Personal Branding"},
            {"value": "health", "label": "Sante / Bien-etre"},
            {"value": "education", "label": "Education / Formation"},
            {"value": "other", "label": "Autre"},
        ],
        "maps_to": "industry",
    },
    {
        "key": "description",
        "question": "Decrivez votre activite en 2-3 phrases.",
        "type": "textarea",
        "category": "identity",
        "required": True,
        "modes": ["interview"],
        "placeholder": "Que faites-vous ? Quelle est votre proposition de valeur unique ?",
        "maps_to": "description",
    },
    {
        "key": "website_url",
        "question": "Avez-vous un site web ? Si oui, partagez l'URL.",
        "type": "url",
        "category": "identity",
        "required": False,
        "modes": ["interview"],
        "placeholder": "https://www.votre-site.com",
        "skip_label": "Je n'ai pas de site web",
    },
    {
        "key": "tagline",
        "question": "Avez-vous un slogan ou une baseline ?",
        "type": "text",
        "category": "identity",
        "required": False,
        "modes": ["interview"],
        "placeholder": "Ex: 'Just Do It', 'Think Different'...",
        "skip_label": "Pas encore de slogan",
        "maps_to": "tagline",
    },
    {
        "key": "year_founded",
        "question": "En quelle annee votre activite a-t-elle demarre ?",
        "type": "text",
        "category": "identity",
        "required": False,
        "modes": ["interview"],
        "placeholder": "Ex: 2020",
        "skip_label": "Passer",
    },

    # ══════════════════════════════════════════════════════════════════
    # PRODUCT — Que vendez-vous ?
    # ══════════════════════════════════════════════════════════════════
    {
        "key": "products_services",
        "question": "Quels sont vos principaux produits ou services ?",
        "type": "textarea",
        "category": "product",
        "required": True,
        "modes": ["interview", "semi_auto"],
        "placeholder": "Listez vos produits/services phares...",
        "maps_to": "products",
    },
    {
        "key": "price_range",
        "question": "Dans quelle gamme de prix se situent vos offres ?",
        "type": "select",
        "category": "product",
        "required": False,
        "modes": ["interview"],
        "options": [
            {"value": "low", "label": "Accessible (< 50 EUR)"},
            {"value": "mid", "label": "Milieu de gamme (50-200 EUR)"},
            {"value": "premium", "label": "Premium (200-1000 EUR)"},
            {"value": "luxury", "label": "Luxe (> 1000 EUR)"},
            {"value": "varies", "label": "Ca depend du produit"},
        ],
        "skip_label": "Passer",
    },
    {
        "key": "unique_selling_point",
        "question": "Qu'est-ce qui vous differencie de vos concurrents ?",
        "type": "textarea",
        "category": "product",
        "required": False,
        "modes": ["interview"],
        "placeholder": "Ex: Livraison en 24h, ingredients bio, expertise unique...",
        "skip_label": "Passer",
    },

    # ══════════════════════════════════════════════════════════════════
    # AUDIENCE — A qui vendez-vous ?
    # ══════════════════════════════════════════════════════════════════
    {
        "key": "target_audience",
        "question": "Qui sont vos clients ideaux ? Decrivez votre audience cible.",
        "type": "textarea",
        "category": "audience",
        "required": True,
        "modes": ["interview"],
        "placeholder": "Ex: Familles CSP+ en Ile-de-France, 30-50 ans...",
        "maps_to": "target_audience",
    },
    {
        "key": "audience_age",
        "question": "Quelle est la tranche d'age principale de votre audience ?",
        "type": "select",
        "category": "audience",
        "required": False,
        "modes": ["interview"],
        "options": [
            {"value": "18-24", "label": "18-24 ans (Gen Z)"},
            {"value": "25-34", "label": "25-34 ans (Millennials)"},
            {"value": "35-44", "label": "35-44 ans"},
            {"value": "45-54", "label": "45-54 ans"},
            {"value": "55+", "label": "55 ans et plus"},
            {"value": "mixed", "label": "Mixte / Toutes les tranches"},
        ],
    },
    {
        "key": "locations",
        "question": "Ou se trouvent vos clients ? (villes, regions, pays)",
        "type": "text",
        "category": "audience",
        "required": False,
        "modes": ["interview"],
        "placeholder": "Ex: Paris, Lyon, toute la France...",
    },
    {
        "key": "social_profiles",
        "question": "Quels reseaux sociaux utilisez-vous deja ?",
        "type": "multi_select",
        "category": "audience",
        "required": False,
        "modes": ["interview", "semi_auto"],
        "options": [
            {"value": "instagram", "label": "Instagram"},
            {"value": "linkedin", "label": "LinkedIn"},
            {"value": "facebook", "label": "Facebook"},
            {"value": "tiktok", "label": "TikTok"},
            {"value": "twitter", "label": "X (Twitter)"},
            {"value": "youtube", "label": "YouTube"},
        ],
        "skip_label": "Aucun pour l'instant",
    },

    # ══════════════════════════════════════════════════════════════════
    # VOICE — Comment parlez-vous ?
    # ══════════════════════════════════════════════════════════════════
    {
        "key": "tone_style",
        "question": "Comment decririez-vous le ton de votre communication ?",
        "type": "select",
        "category": "voice",
        "required": True,
        "modes": ["interview", "semi_auto"],
        "options": [
            {"value": "professional", "label": "Professionnel & serieux"},
            {"value": "friendly", "label": "Amical & accessible"},
            {"value": "bold", "label": "Audacieux & provocant"},
            {"value": "educational", "label": "Educatif & expert"},
            {"value": "fun", "label": "Fun & decale"},
        ],
        "maps_to": "tone_of_voice",
    },
    {
        "key": "brand_personality",
        "question": "Si votre marque etait une personne, comment serait-elle ?",
        "type": "textarea",
        "category": "voice",
        "required": False,
        "modes": ["interview"],
        "placeholder": "Ex: Un ami expert qui explique simplement des sujets complexes...",
    },
    {
        "key": "languages",
        "question": "En quelle(s) langue(s) communiquez-vous ?",
        "type": "multi_select",
        "category": "voice",
        "required": False,
        "modes": ["interview", "semi_auto"],
        "options": [
            {"value": "fr", "label": "Francais"},
            {"value": "en", "label": "Anglais"},
            {"value": "ar", "label": "Arabe"},
            {"value": "es", "label": "Espagnol"},
            {"value": "de", "label": "Allemand"},
            {"value": "other", "label": "Autre"},
        ],
    },
    {
        "key": "content_constraints",
        "question": "Y a-t-il des sujets ou mots a eviter dans votre communication ?",
        "type": "textarea",
        "category": "voice",
        "required": False,
        "modes": ["interview"],
        "placeholder": "Ex: Pas de jargon technique, eviter les anglicismes...",
        "skip_label": "Rien de particulier",
    },
    {
        "key": "emojis_preference",
        "question": "Utilisez-vous des emojis dans vos communications ?",
        "type": "select",
        "category": "voice",
        "required": False,
        "modes": ["interview"],
        "options": [
            {"value": "heavy", "label": "Oui, beaucoup !"},
            {"value": "moderate", "label": "Avec moderation"},
            {"value": "minimal", "label": "Tres rarement"},
            {"value": "never", "label": "Jamais"},
        ],
    },

    # ══════════════════════════════════════════════════════════════════
    # GOALS — Ou allez-vous ?
    # ══════════════════════════════════════════════════════════════════
    {
        "key": "marketing_goals",
        "question": "Quels sont vos principaux objectifs sur les reseaux sociaux ?",
        "type": "multi_select",
        "category": "goals",
        "required": True,
        "modes": ["interview", "semi_auto"],
        "options": [
            {"value": "awareness", "label": "Notoriete / Visibilite"},
            {"value": "engagement", "label": "Engagement / Communaute"},
            {"value": "leads", "label": "Generation de leads"},
            {"value": "sales", "label": "Ventes directes"},
            {"value": "recruitment", "label": "Recrutement / Employer branding"},
            {"value": "education", "label": "Education / Thought leadership"},
        ],
    },
    {
        "key": "posting_frequency",
        "question": "A quelle frequence souhaitez-vous publier ?",
        "type": "select",
        "category": "goals",
        "required": False,
        "modes": ["interview"],
        "options": [
            {"value": "daily", "label": "Tous les jours"},
            {"value": "3_per_week", "label": "3 fois par semaine"},
            {"value": "weekly", "label": "1 fois par semaine"},
            {"value": "unsure", "label": "Je ne sais pas encore"},
        ],
    },
    {
        "key": "content_types",
        "question": "Quels types de contenu souhaitez-vous creer ?",
        "type": "multi_select",
        "category": "goals",
        "required": False,
        "modes": ["interview"],
        "options": [
            {"value": "posts", "label": "Posts / Carrousels"},
            {"value": "stories", "label": "Stories / Reels"},
            {"value": "articles", "label": "Articles longs"},
            {"value": "videos", "label": "Videos"},
            {"value": "infographics", "label": "Infographies"},
        ],
    },
    {
        "key": "hashtag_preferences",
        "question": "Avez-vous des hashtags fetiches ou un style de hashtag prefere ?",
        "type": "text",
        "category": "goals",
        "required": False,
        "modes": ["interview"],
        "placeholder": "Ex: #FoodParis #RestaurantHalal ...",
        "skip_label": "Passer",
    },
    {
        "key": "competitors",
        "question": "Qui sont vos principaux concurrents ? (noms ou URLs)",
        "type": "textarea",
        "category": "goals",
        "required": False,
        "modes": ["interview", "semi_auto"],
        "placeholder": "Ex: competitor1.com, @concurrent_instagram...",
        "skip_label": "Je ne sais pas",
    },
    {
        "key": "inspiration_accounts",
        "question": "Quels comptes ou marques vous inspirent sur les reseaux ?",
        "type": "textarea",
        "category": "goals",
        "required": False,
        "modes": ["interview"],
        "placeholder": "Ex: @nike, @hubspot, @lfrfrancais...",
        "skip_label": "Passer",
    },
    {
        "key": "biggest_challenge",
        "question": "Quel est votre plus grand defi marketing actuellement ?",
        "type": "select",
        "category": "goals",
        "required": False,
        "modes": ["interview"],
        "options": [
            {"value": "time", "label": "Manque de temps"},
            {"value": "ideas", "label": "Manque d'idees de contenu"},
            {"value": "consistency", "label": "Regularite de publication"},
            {"value": "engagement", "label": "Faible engagement"},
            {"value": "growth", "label": "Croissance de l'audience"},
            {"value": "conversion", "label": "Convertir les followers en clients"},
        ],
    },

    # ══════════════════════════════════════════════════════════════════
    # UPSELL — Conditionnel (pas de site web)
    # ══════════════════════════════════════════════════════════════════
    {
        "key": "upsell_website",
        "question": "Saviez-vous que PresenceOS peut creer un site web professionnel pour votre marque ?",
        "type": "upsell",
        "category": "upsell",
        "required": False,
        "modes": ["interview"],
        "condition": "no_website",
        "upsell_data": {
            "price": "79 EUR/mois",
            "features": [
                "Site web optimise SEO",
                "Integration reseaux sociaux",
                "Blog automatise",
                "Analytics integres",
            ],
        },
    },
]


# ── Determination du mode ────────────────────────────────────────────

def determine_onboarding_mode(
    website_url: Optional[str] = None,
    social_profiles: Optional[list[str]] = None,
) -> OnboardingMode:
    """Determine le mode d'onboarding optimal selon les sources disponibles."""
    has_website = bool(website_url and website_url.strip())
    has_socials = bool(social_profiles and len(social_profiles) > 0)

    if has_website and has_socials:
        return OnboardingMode.FULL_AUTO
    elif has_website or has_socials:
        return OnboardingMode.SEMI_AUTO
    else:
        return OnboardingMode.INTERVIEW


def get_questions_for_mode(
    mode: OnboardingMode,
    context: Optional[dict] = None,
    extracted_data: Optional[dict] = None,
) -> list[dict]:
    """
    Retourne les questions filtrees pour le mode donne.
    - context: reponses deja collectees (pour filtrer les conditionnelles)
    - extracted_data: donnees extraites par scraping (pour skip adaptatif)
    """
    context = context or {}
    extracted_data = extracted_data or {}
    questions = []

    for q in ONBOARDING_QUESTIONS:
        # Verifier si la question est pertinente pour ce mode
        if mode.value not in q.get("modes", []):
            continue

        # Verifier les conditions (ex: upsell seulement si pas de site)
        if not _should_show_question(q, context):
            continue

        # Skip adaptatif: si le scraping a deja fourni la donnee
        maps_to = q.get("maps_to")
        if maps_to and maps_to in extracted_data and extracted_data[maps_to]:
            continue

        questions.append(q)

    return questions


# ── Extraction automatique ───────────────────────────────────────────

def run_onboarding_extraction(website_url: str) -> dict:
    """
    Scrape un site web et extrait les infos pour pre-remplir le Business Brain.

    Returns:
        dict avec cles: business_name, description, industry, products,
        target_audience, tone_of_voice, colors, tagline
    """
    extractor = Agent(
        role="Analyste de Marque",
        goal="Extraire toutes les informations d'identite de marque a partir d'un site web.",
        backstory=(
            "Tu es un consultant en branding qui analyse les sites web pour "
            "comprendre l'identite d'une marque. Tu identifies le nom, la description, "
            "les produits/services, l'audience cible, le ton de communication, "
            "et le positionnement."
        ),
        tools=[WebScraperTool()],
        llm=get_crew_llm(),
        verbose=get_crew_verbose(),
    )

    from app.agents.tasks.onboarding_tasks import create_brand_extraction_task
    extraction_task = create_brand_extraction_task(extractor, website_url)

    crew = Crew(
        agents=[extractor],
        tasks=[extraction_task],
        process=Process.sequential,
        verbose=get_crew_verbose(),
    )

    result = crew.kickoff()

    raw = str(result)
    json_match = re.search(r'\{[\s\S]*"business_name"[\s\S]*\}', raw)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    return {
        "business_name": "",
        "description": "",
        "error": "Extraction echouee",
        "raw": raw[:500],
    }


# ── Traitement d'une reponse d'interview ─────────────────────────────

def process_interview_answer(
    question_key: str,
    answer: str,
    collected_data: dict,
    extracted_data: Optional[dict] = None,
) -> dict:
    """
    Traite une reponse d'interview et retourne les donnees mises a jour
    + un insight contextuel optionnel genere par l'IA.
    """
    extracted_data = extracted_data or {}

    # Mettre a jour les donnees collectees
    collected_data[question_key] = answer

    # Trouver la question
    question = next((q for q in ONBOARDING_QUESTIONS if q["key"] == question_key), None)
    if not question:
        return {
            "collected_data": collected_data,
            "insight": None,
            "next_question": _get_next_question(collected_data, extracted_data),
        }

    # Generer un insight contextuel
    insight = _generate_contextual_insight(question_key, answer, collected_data)

    # Si l'utilisateur n'a pas de site web, on flag l'upsell
    upsell = None
    if question_key == "website_url" and (not answer or answer.strip().lower() in ["non", "no", ""]):
        collected_data["_no_website"] = True
        upsell = _handle_website_upsell_insight()

    # Si des concurrents sont mentionnes, lancer l'analyse
    competitor_analysis = None
    if question_key == "competitors" and answer and answer.strip():
        competitor_analysis = _run_competitor_analysis(answer)

    # Determiner la prochaine question (adaptive: skip si deja connu)
    next_question = _get_next_question(collected_data, extracted_data)

    return {
        "collected_data": collected_data,
        "insight": insight,
        "upsell": upsell,
        "competitor_analysis": competitor_analysis,
        "next_question": next_question,
        "progress": _calculate_progress(collected_data, extracted_data),
    }


# ── Helpers prives ───────────────────────────────────────────────────

def _should_show_question(question: dict, context: dict) -> bool:
    """Determine si une question doit etre affichee selon le contexte."""
    condition = question.get("condition")
    if not condition:
        return True

    if condition == "no_website":
        return context.get("_no_website", False)

    return True


def _get_next_question(
    collected_data: dict,
    extracted_data: Optional[dict] = None,
) -> Optional[dict]:
    """Trouve la prochaine question non repondue pertinente."""
    extracted_data = extracted_data or {}

    for q in ONBOARDING_QUESTIONS:
        # Deja repondu
        if q["key"] in collected_data:
            continue
        # Cle interne
        if q["key"].startswith("_"):
            continue
        # Pas disponible en mode interview
        if "interview" not in q.get("modes", []):
            continue
        # Condition non remplie
        if not _should_show_question(q, collected_data):
            continue
        # Skip adaptatif: donnee deja extraite par scraping
        maps_to = q.get("maps_to")
        if maps_to and maps_to in extracted_data and extracted_data[maps_to]:
            # On skip mais on sauvegarde la donnee extraite
            collected_data[q["key"]] = str(extracted_data[maps_to])
            continue

        return q

    return None  # Toutes les questions ont ete posees


def _calculate_progress(
    collected_data: dict,
    extracted_data: Optional[dict] = None,
) -> dict:
    """Calcule la progression de l'onboarding (% du Brain rempli)."""
    extracted_data = extracted_data or {}

    total_questions = len([
        q for q in ONBOARDING_QUESTIONS
        if "interview" in q.get("modes", [])
        and _should_show_question(q, collected_data)
        and not (q.get("maps_to") and q["maps_to"] in extracted_data and extracted_data[q["maps_to"]])
    ])

    answered = len([
        k for k in collected_data.keys()
        if not k.startswith("_")
    ])

    percentage = round((answered / max(total_questions, 1)) * 100)

    return {
        "answered": answered,
        "total": total_questions,
        "percentage": min(percentage, 100),
    }


def _generate_contextual_insight(
    question_key: str,
    answer: str,
    collected_data: dict,
) -> Optional[str]:
    """Genere un insight contextuel base sur la reponse."""
    insight_templates = {
        "business_type": {
            "restaurant": "Le secteur de la restauration est tres visuel. Instagram et TikTok seront vos meilleurs allies !",
            "saas": "Pour le SaaS, LinkedIn et le content marketing long-format fonctionnent particulierement bien.",
            "ecommerce": "L'e-commerce performe tres bien avec les carrousels Instagram et les videos produit TikTok.",
            "service": "Les services beneficient enormement des temoignages clients et du contenu educatif.",
            "personal": "Le personal branding fonctionne mieux avec du contenu authentique et des stories.",
            "agency": "Les agences performent bien en montrant des etudes de cas et du contenu behind-the-scenes.",
            "health": "Le secteur sante/bien-etre cartonne sur Instagram et TikTok avec du contenu educatif et inspirant.",
            "education": "Le contenu educatif genere enormement de partages organiques sur LinkedIn et YouTube.",
        },
        "tone_style": {
            "professional": "Un ton professionnel inspire confiance. Ideal pour LinkedIn et les articles experts.",
            "friendly": "Un ton amical cree de la proximite. Parfait pour Instagram Stories et Facebook.",
            "bold": "Un ton audacieux se demarque ! Attention a rester coherent avec votre audience.",
            "educational": "Le contenu educatif genere beaucoup d'engagement et de partages organiques.",
            "fun": "Le contenu fun performe tres bien sur TikTok et Instagram Reels.",
        },
        "biggest_challenge": {
            "time": "PresenceOS va vous faire gagner du temps grace a la generation automatique de contenu !",
            "ideas": "Notre IA va generer des idees adaptees a votre marque chaque semaine.",
            "consistency": "L'autopilot PresenceOS peut publier automatiquement pour vous.",
            "engagement": "Nous allons optimiser vos contenus pour maximiser l'engagement.",
            "growth": "Nos analyses de tendances vous aideront a toucher de nouvelles audiences.",
            "conversion": "Des CTAs intelligents et du contenu cible augmenteront vos conversions.",
        },
        "audience_age": {
            "18-24": "La Gen Z adore les formats courts : Reels, TikTok, carrousels creatifs.",
            "25-34": "Les Millennials sont actifs sur Instagram et LinkedIn. Un bon mix de formats.",
            "35-44": "Cette tranche apprecie le contenu de valeur : articles, etudes de cas, temoignages.",
            "45-54": "Facebook et LinkedIn sont les canaux privilegies pour cette audience.",
            "55+": "Le contenu informatif et rassurant fonctionne bien. Privilegiez Facebook.",
            "mixed": "Avec une audience mixte, variez les formats et plateformes pour toucher tout le monde.",
        },
    }

    if question_key in insight_templates:
        template = insight_templates[question_key]
        if answer in template:
            return template[answer]

    return None


def _handle_website_upsell_insight() -> dict:
    """Retourne les donnees d'upsell pour la creation de site web."""
    return {
        "type": "website_upsell",
        "title": "Creez votre site web professionnel",
        "message": (
            "Sans site web, vous perdez une source majeure de credibilite et de trafic. "
            "PresenceOS peut creer un site web optimise pour votre marque."
        ),
        "price": "79 EUR/mois",
        "features": [
            "Site web responsive optimise SEO",
            "Integration automatique avec vos reseaux sociaux",
            "Blog alimente par vos contenus IA",
            "Analytics et tracking integres",
            "Domaine personnalise inclus",
        ],
        "cta": "En savoir plus",
    }


def _run_competitor_analysis(competitors_text: str) -> Optional[dict]:
    """
    Analyse les concurrents mentionnes par l'utilisateur.
    Scrape les sites/profils disponibles.
    """
    urls = re.findall(r'https?://[^\s,]+', competitors_text)
    names = [
        n.strip() for n in competitors_text.replace(",", "\n").split("\n")
        if n.strip() and not n.strip().startswith("http")
    ]

    if not urls and not names:
        return None

    competitors = []
    scraper = WebScraperTool()

    for url in urls[:3]:
        try:
            content = scraper._run(url=url)
            competitors.append({
                "url": url,
                "name": _extract_name_from_content(content),
                "summary": content[:300] if content else "Contenu non accessible",
                "scraped": True,
            })
        except Exception:
            competitors.append({
                "url": url,
                "name": url,
                "summary": "Impossible d'acceder au site",
                "scraped": False,
            })

    for name in names[:3]:
        if not any(c.get("name", "").lower() == name.lower() for c in competitors):
            competitors.append({
                "name": name,
                "url": None,
                "summary": f"Concurrent identifie: {name}",
                "scraped": False,
            })

    return {
        "type": "competitor_analysis",
        "competitors": competitors,
        "count": len(competitors),
        "message": f"{len(competitors)} concurrent(s) identifie(s). Ces donnees aideront a differencier votre contenu.",
    }


def _extract_name_from_content(content: str) -> str:
    """Extrait un nom de marque du contenu scrape."""
    lines = content.split("\n")
    for line in lines[:5]:
        clean = line.strip().strip("#").strip()
        if clean and len(clean) < 100:
            return clean
    return "Concurrent"


# ── Conversion des donnees collectees en Brand model ─────────────────

def convert_to_brand_data(collected_data: dict) -> dict:
    """
    Convertit les donnees collectees pendant l'interview en format
    compatible avec le modele Brand pour sauvegarde.
    """
    tone_mapping = {
        "professional": {"tone_formal": 80, "tone_playful": 20, "tone_bold": 30, "tone_emotional": 20},
        "friendly": {"tone_formal": 30, "tone_playful": 70, "tone_bold": 40, "tone_emotional": 60},
        "bold": {"tone_formal": 40, "tone_playful": 50, "tone_bold": 90, "tone_emotional": 50},
        "educational": {"tone_formal": 70, "tone_playful": 30, "tone_bold": 40, "tone_emotional": 30},
        "fun": {"tone_formal": 10, "tone_playful": 90, "tone_bold": 60, "tone_emotional": 70},
    }

    tone_style = collected_data.get("tone_style", "friendly")
    tones = tone_mapping.get(tone_style, tone_mapping["friendly"])

    # Parse locations
    locations_raw = collected_data.get("locations", "")
    locations = [loc.strip() for loc in locations_raw.split(",") if loc.strip()] if locations_raw else []

    # Parse target audience into persona
    target_text = collected_data.get("target_audience", "")
    age_range = collected_data.get("audience_age", "")
    target_persona = {
        "name": "Audience cible",
        "description": target_text,
        "age_range": age_range,
    } if target_text else None

    # Parse content constraints
    constraints_text = collected_data.get("content_constraints", "")
    words_to_avoid = [w.strip() for w in constraints_text.split(",") if w.strip()] if constraints_text else []

    # Language mapping
    languages = collected_data.get("languages", ["fr"])
    primary_language = languages[0] if isinstance(languages, list) and languages else "fr"

    return {
        "brand": {
            "name": collected_data.get("business_name", ""),
            "brand_type": collected_data.get("business_type", "other"),
            "description": collected_data.get("description", ""),
            "website_url": collected_data.get("website_url", ""),
            "target_persona": target_persona,
            "locations": locations,
        },
        "voice": {
            **tones,
            "tone_technical": 30,
            "words_to_avoid": words_to_avoid,
            "primary_language": primary_language,
            "custom_instructions": collected_data.get("brand_personality", ""),
        },
        "metadata": {
            "social_profiles": collected_data.get("social_profiles", []),
            "marketing_goals": collected_data.get("marketing_goals", []),
            "posting_frequency": collected_data.get("posting_frequency", ""),
            "content_types": collected_data.get("content_types", []),
            "hashtag_preferences": collected_data.get("hashtag_preferences", ""),
            "products_services": collected_data.get("products_services", ""),
            "competitors": collected_data.get("competitors", ""),
            "tagline": collected_data.get("tagline", ""),
            "year_founded": collected_data.get("year_founded", ""),
            "price_range": collected_data.get("price_range", ""),
            "unique_selling_point": collected_data.get("unique_selling_point", ""),
            "inspiration_accounts": collected_data.get("inspiration_accounts", ""),
            "biggest_challenge": collected_data.get("biggest_challenge", ""),
            "emojis_preference": collected_data.get("emojis_preference", ""),
        },
    }

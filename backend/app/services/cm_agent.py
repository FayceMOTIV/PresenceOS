"""
PresenceOS - Community Manager AI Agent

AI-powered service for classifying interactions (reviews, comments, DMs)
and generating personalized responses based on the Business Brain.

Uses Claude Haiku for fast classification and simple responses.
Uses Claude Sonnet for complex/negative cases requiring nuance.
"""
import json
import re
from typing import Any

import anthropic
import structlog

from app.core.config import settings
from app.models.brand import Brand, BrandVoice, KnowledgeItem
from app.models.cm_interaction import CMInteraction

logger = structlog.get_logger()

# ── Crisis keywords (any language) ──────────────────────────────────────────
CRISIS_KEYWORDS_FR = [
    "intoxication", "allergie", "allergique", "accident", "arnaque",
    "avocat", "plainte", "signalement", "procès", "danger", "poison",
    "urgence", "hôpital", "malade", "empoisonnement", "hygiène",
    "insalubre", "rat", "cafard", "discrimination", "harcèlement",
    "vol", "agression", "menace",
]

CRISIS_KEYWORDS_EN = [
    "food poisoning", "allergy", "allergic", "accident", "scam",
    "lawyer", "lawsuit", "complaint", "report", "danger", "poison",
    "emergency", "hospital", "sick", "health violation", "hygiene",
    "unsanitary", "rat", "cockroach", "discrimination", "harassment",
    "theft", "assault", "threat",
]

CRISIS_KEYWORDS = set(CRISIS_KEYWORDS_FR + CRISIS_KEYWORDS_EN)

# Pre-compiled regex pattern for word-boundary matching of crisis keywords
_CRISIS_PATTERN = re.compile(
    r"\b(?:" + "|".join(re.escape(kw) for kw in sorted(CRISIS_KEYWORDS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


def _has_crisis_keyword(text: str) -> bool:
    """Check if text contains any crisis keyword using word boundaries."""
    return bool(_CRISIS_PATTERN.search(text))


# ── Niche-specific tone guidance ────────────────────────────────────────────

NICHE_TONE_GUIDE: dict[str, dict[str, str]] = {
    "restaurant": {
        "personality": "chaleureux, gourmand et passionné de bonne cuisine",
        "greeting": "Merci infiniment pour votre avis",
        "negative_empathy": "Nous sommes sincèrement désolés que votre expérience n'ait pas été à la hauteur",
        "signature_vibe": "local, convivial, authentique",
    },
    "saas": {
        "personality": "professionnel, réactif et orienté solution",
        "greeting": "Merci pour votre retour",
        "negative_empathy": "Nous prenons votre retour très au sérieux",
        "signature_vibe": "innovant, fiable, expert",
    },
    "ecommerce": {
        "personality": "dynamique, attentionné et orienté client",
        "greeting": "Merci pour votre avis",
        "negative_empathy": "Nous sommes navrés de cette mésaventure",
        "signature_vibe": "rapide, fiable, à l'écoute",
    },
    "service": {
        "personality": "professionnel, empathique et expert",
        "greeting": "Merci pour votre confiance et votre retour",
        "negative_empathy": "Nous regrettons sincèrement cette situation",
        "signature_vibe": "de confiance, expert, humain",
    },
    "personal": {
        "personality": "authentique, inspirant et accessible",
        "greeting": "Merci beaucoup pour ce retour",
        "negative_empathy": "Je suis désolé(e) que cela n'ait pas été à la hauteur",
        "signature_vibe": "personnel, passionné, transparent",
    },
}

DEFAULT_NICHE_TONE = {
    "personality": "professionnel, chaleureux et attentionné",
    "greeting": "Merci pour votre avis",
    "negative_empathy": "Nous sommes désolés de cette situation",
    "signature_vibe": "professionnel, fiable, humain",
}


class CMAgent:
    """AI Community Manager agent powered by Claude.

    Classifies interactions, generates personalized responses using
    the brand's Business Brain (voice, knowledge, FAQ, hours, etc.).
    """

    HAIKU_MODEL = "claude-haiku-4-5-20251001"
    SONNET_MODEL = "claude-sonnet-4-6"

    def __init__(self, brand: Brand) -> None:
        self.brand = brand
        self._client: anthropic.AsyncAnthropic | None = None

    def _get_client(self) -> anthropic.AsyncAnthropic:
        if self._client is None:
            if not settings.anthropic_api_key:
                raise RuntimeError(
                    "Anthropic API key is not configured. "
                    "Set ANTHROPIC_API_KEY in your environment."
                )
            self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        return self._client

    # ── System Prompt Builder ────────────────────────────────────────────────

    def build_system_prompt(self) -> str:
        """Build a dynamic system prompt from the brand's Business Brain.

        Includes: niche, brand voice, hours, services, FAQ, contact info,
        escalation rules, and auto-publish confidence threshold.
        """
        brand = self.brand
        niche_key = brand.brand_type.value if brand.brand_type else "service"
        tone_guide = NICHE_TONE_GUIDE.get(niche_key, DEFAULT_NICHE_TONE)

        language = "français"
        if brand.voice and brand.voice.primary_language:
            lang_map = {"fr": "français", "en": "anglais", "es": "espagnol", "de": "allemand"}
            language = lang_map.get(brand.voice.primary_language, brand.voice.primary_language)

        sections = []

        # Identity
        sections.append(
            f"Tu es le Community Manager IA de « {brand.name} ».\n"
            f"Secteur : {niche_key}.\n"
            f"Personnalité de la marque : {tone_guide['personality']}.\n"
            f"Identité de marque : {tone_guide['signature_vibe']}.\n"
            f"Tu réponds en {language}."
        )

        # Brand description
        if brand.description:
            sections.append(f"Description du business : {brand.description}")

        # Brand voice
        if brand.voice:
            v = brand.voice
            voice_lines = []

            formality = "formel" if v.tone_formal and v.tone_formal > 60 else "décontracté"
            playful = "joueur" if v.tone_playful and v.tone_playful > 60 else "sérieux"
            bold = "audacieux" if v.tone_bold and v.tone_bold > 60 else "subtil"
            voice_lines.append(f"Ton : {formality}, {playful}, {bold}")

            if v.words_to_avoid:
                voice_lines.append(f"Mots INTERDITS : {', '.join(v.words_to_avoid)}")
            if v.words_to_prefer:
                voice_lines.append(f"Mots à PRIVILÉGIER : {', '.join(v.words_to_prefer)}")
            if v.example_phrases:
                voice_lines.append(f"Exemples de ton : {' | '.join(v.example_phrases[:3])}")
            if v.emojis_allowed:
                voice_lines.append(f"Emojis autorisés (max {v.max_emojis_per_post or 2} par réponse)")
            else:
                voice_lines.append("Pas d'emojis dans les réponses")
            if v.custom_instructions:
                voice_lines.append(f"Instructions spéciales : {v.custom_instructions}")

            sections.append("VOIX DE LA MARQUE :\n" + "\n".join(voice_lines))

        # Knowledge base (services, FAQ, hours, etc.)
        knowledge_items = self._get_brand_knowledge()
        if knowledge_items:
            sections.append("INFORMATIONS DU BUSINESS :\n" + "\n".join(knowledge_items))

        # Locations
        if brand.locations:
            sections.append(f"Localisations : {', '.join(brand.locations)}")

        # Constraints
        if brand.constraints:
            constraints_str = json.dumps(brand.constraints, ensure_ascii=False)
            sections.append(f"Contraintes business : {constraints_str}")

        # Rules
        sections.append(
            "RÈGLES ABSOLUES :\n"
            "1. Ne JAMAIS mentionner que tu es une IA ou un robot.\n"
            "2. Maximum 3 phrases par réponse. Court, humain, efficace.\n"
            "3. Toujours personnaliser la réponse au contenu spécifique de l'avis.\n"
            "4. Pour les avis positifs : remercier chaleureusement + inviter à revenir.\n"
            "5. Pour les avis négatifs : empathie sincère + proposer contact direct.\n"
            "6. Pour les questions : répondre précisément avec les infos du business.\n"
            f"7. Pour les crises : réponse empathique uniquement, pas de justification.\n"
            f"8. Seuil de confiance auto-publish : {settings.cm_auto_publish_threshold}.\n"
            "9. Ne jamais offrir de compensation ou remise sans autorisation humaine.\n"
            "10. Répondre UNIQUEMENT en JSON valide."
        )

        return "\n\n".join(sections)

    def _get_brand_knowledge(self) -> list[str]:
        """Extract knowledge items from the brand for the system prompt."""
        items = []
        # The brand may have knowledge items loaded via relationship
        knowledge_list = getattr(self.brand, "knowledge_items", None) or []
        for ki in knowledge_list:
            if not ki.is_active:
                continue
            prefix = ki.knowledge_type.value.upper() if hasattr(ki, "knowledge_type") else "INFO"
            items.append(f"[{prefix}] {ki.title}: {ki.content}")
        return items

    # ── Classification ───────────────────────────────────────────────────────

    async def classify_interaction(
        self, content: str, rating: int | None = None,
    ) -> dict[str, Any]:
        """Classify an interaction using Claude Haiku (fast, cheap).

        Returns:
            {
                "classification": "positive|negative|neutral|question|crisis",
                "sentiment_score": 0.0-1.0,
                "confidence": 0.0-1.0,
                "should_escalate": bool,
            }
        """
        # Quick crisis keyword scan (before even calling the LLM)
        content_lower = content.lower()
        has_crisis_keyword = _has_crisis_keyword(content)

        # Rating-based pre-classification hints
        rating_hint = ""
        if rating is not None:
            if rating <= 2:
                rating_hint = f"Note : {rating}/5 étoiles (mauvaise)."
            elif rating == 3:
                rating_hint = f"Note : {rating}/5 étoiles (moyenne)."
            else:
                rating_hint = f"Note : {rating}/5 étoiles (bonne)."

        prompt = f"""Analyse cette interaction client et classifie-la.

INTERACTION :
{content}
{rating_hint}

Réponds en JSON strict :
{{
  "classification": "positive|negative|neutral|question|crisis",
  "sentiment_score": <float entre 0.0 et 1.0, où 1.0 = très positif>,
  "confidence": <float entre 0.0 et 1.0>,
  "reasoning": "<1 phrase expliquant ta classification>"
}}

Règles :
- "crisis" si mots dangereux (intoxication, allergie, avocat, plainte, menace...) OU accusations graves
- "negative" si insatisfaction claire mais pas de crise
- "question" si le client pose une question (horaires, menu, prix, réservation...)
- "neutral" si neutre ou mitigé
- "positive" si satisfaction explicite"""

        client = self._get_client()
        try:
            response = await client.messages.create(
                model=self.HAIKU_MODEL,
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
            )
            result = json.loads(response.content[0].text)
        except Exception as exc:
            logger.error("Classification failed", error=str(exc))
            # Fallback: rule-based classification
            result = self._fallback_classify(content, rating)

        # Force escalation on crisis keywords or very low ratings
        should_escalate = False
        if has_crisis_keyword:
            result["classification"] = "crisis"
            should_escalate = True
        if rating is not None and rating <= 2 and result["classification"] == "crisis":
            should_escalate = True
        if result["classification"] == "crisis":
            should_escalate = True

        return {
            "classification": result.get("classification", "neutral"),
            "sentiment_score": float(result.get("sentiment_score", 0.5)),
            "confidence": float(result.get("confidence", 0.5)),
            "should_escalate": should_escalate,
        }

    def _fallback_classify(
        self, content: str, rating: int | None,
    ) -> dict[str, Any]:
        """Rule-based fallback when the LLM is unavailable."""
        content_lower = content.lower()

        if _has_crisis_keyword(content_lower):
            return {"classification": "crisis", "sentiment_score": 0.1, "confidence": 0.7}

        if rating is not None:
            if rating >= 4:
                return {"classification": "positive", "sentiment_score": 0.85, "confidence": 0.7}
            elif rating <= 2:
                return {"classification": "negative", "sentiment_score": 0.2, "confidence": 0.7}

        if "?" in content:
            return {"classification": "question", "sentiment_score": 0.5, "confidence": 0.5}

        return {"classification": "neutral", "sentiment_score": 0.5, "confidence": 0.4}

    # ── Response Generation ──────────────────────────────────────────────────

    async def generate_response(self, interaction: CMInteraction) -> dict[str, Any]:
        """Generate an AI response for an interaction.

        Uses Haiku for simple positive/neutral cases, Sonnet for negative/crisis.

        Returns:
            {
                "response": str,
                "confidence": float,
                "should_auto_publish": bool,
                "reasoning": str,
            }
        """
        system_prompt = self.build_system_prompt()
        classification = interaction.classification
        rating = interaction.rating

        # Choose model based on complexity
        is_complex = classification in ("negative", "crisis") or (rating is not None and rating <= 2)
        model = self.SONNET_MODEL if is_complex else self.HAIKU_MODEL

        niche_key = self.brand.brand_type.value if self.brand.brand_type else "service"
        tone_guide = NICHE_TONE_GUIDE.get(niche_key, DEFAULT_NICHE_TONE)

        prompt = f"""Tu dois répondre à cette interaction client sur {interaction.platform}.

TYPE : {interaction.interaction_type}
CLASSIFICATION : {classification}
{"NOTE : " + str(rating) + "/5 étoiles" if rating else ""}
AUTEUR : {interaction.commenter_name}

CONTENU ORIGINAL :
\"{interaction.content}\"

CONSIGNES :
- Réponse en maximum 3 phrases, naturelle et humaine.
- {"Ton empathique : " + tone_guide['negative_empathy'] if classification in ('negative', 'crisis') else "Ton chaleureux : " + tone_guide['greeting']}
- Personnalise la réponse au contenu SPÉCIFIQUE de cet avis (ne pas être générique).
- {"IMPORTANT : Propose de contacter le business directement pour résoudre le problème." if classification in ('negative', 'crisis') else ""}
- {"NE PAS offrir de compensation. NE PAS se justifier." if classification == 'crisis' else ""}

Réponds en JSON strict :
{{
  "response": "<la réponse à publier, max 3 phrases>",
  "confidence": <float 0.0-1.0>,
  "reasoning": "<1 phrase expliquant ton choix de réponse>"
}}"""

        client = self._get_client()
        try:
            response = await client.messages.create(
                model=model,
                max_tokens=512,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
            )
            result = json.loads(response.content[0].text)
        except Exception as exc:
            logger.error("Response generation failed", error=str(exc), model=model)
            raise

        confidence = float(result.get("confidence", 0.0))
        threshold = settings.cm_auto_publish_threshold

        # Auto-publish only if: high confidence AND not critical AND rating >= 3
        should_auto_publish = (
            confidence >= threshold
            and classification not in ("negative", "crisis")
            and (rating is None or rating >= 3)
        )

        return {
            "response": result.get("response", ""),
            "confidence": confidence,
            "should_auto_publish": should_auto_publish,
            "reasoning": result.get("reasoning", ""),
        }

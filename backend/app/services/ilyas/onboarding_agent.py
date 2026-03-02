"""
PresenceOS — Ilyas Onboarding Agent (Sprint 4)

Conversational onboarding that builds a BusinessDNA profile
through 8 sequential questions. Uses Claude Haiku for fast extraction.
"""

import json
import logging
from typing import Any

from app.core.config import get_settings
from app.models.business_dna import BusinessDNA
from app.services.firebase_firestore import FirestoreService

logger = logging.getLogger(__name__)

# ── Onboarding questions (8 steps) ──

ONBOARDING_QUESTIONS: list[dict[str, str]] = [
    {
        "id": "business_name",
        "question": (
            "Salut ! Je suis Ilyas, ton Community Manager IA. 🎉\n\n"
            "Pour bien te conseiller, j'ai besoin d'apprendre à connaître "
            "ton commerce. On commence ?\n\n"
            "**Comment s'appelle ton commerce ?**"
        ),
        "extract_prompt": (
            "Extract the business/restaurant name from the user's answer. "
            "Return JSON: {\"business_name\": \"...\"}"
        ),
    },
    {
        "id": "business_type_and_cuisine",
        "question": (
            "Super ! Et c'est quel type d'établissement ? "
            "(restaurant, boulangerie, bar, café, food truck…)\n\n"
            "Si c'est un restaurant, quel style de cuisine ? "
            "(italien, libanais, burger, bistronomique…)"
        ),
        "extract_prompt": (
            "Extract the business type and cuisine style from the user's answer. "
            "Return JSON: {\"business_type\": \"...\", \"cuisine_style\": \"...\"}"
        ),
    },
    {
        "id": "location",
        "question": (
            "Top ! Tu es situé où exactement ? "
            "(ville et quartier si possible)"
        ),
        "extract_prompt": (
            "Extract city and neighborhood from the user's answer. "
            "Return JSON: {\"city\": \"...\", \"neighborhood\": \"...\"}"
        ),
    },
    {
        "id": "ambiance",
        "question": (
            "Comment tu décrirais l'ambiance de ton établissement ?\n\n"
            "Par exemple : cosy et familial, branché et moderne, "
            "traditionnel et authentique…"
        ),
        "extract_prompt": (
            "Extract the ambiance description from the user's answer. "
            "Return JSON: {\"ambiance\": \"...\"}"
        ),
    },
    {
        "id": "unique_selling_point",
        "question": (
            "Qu'est-ce qui te différencie de tes concurrents ? "
            "Ton petit truc en plus, ta spécialité…"
        ),
        "extract_prompt": (
            "Extract the unique selling point from the user's answer. "
            "Return JSON: {\"unique_selling_point\": \"...\"}"
        ),
    },
    {
        "id": "target_and_tone",
        "question": (
            "C'est qui ta clientèle idéale ? "
            "(familles, jeunes actifs, touristes, étudiants…)\n\n"
            "Et tu préfères qu'on communique comment ? "
            "Plutôt chaleureux et gourmand, ou pro et élégant ?"
        ),
        "extract_prompt": (
            "Extract target audience and preferred tone of voice. "
            "Return JSON: {\"target_audience\": \"...\", \"tone_of_voice\": \"...\"}"
        ),
    },
    {
        "id": "platforms_and_frequency",
        "question": (
            "Sur quels réseaux sociaux tu es présent ? "
            "(Instagram, Facebook, TikTok, LinkedIn…)\n\n"
            "Et tu voudrais poster combien de fois par semaine ?"
        ),
        "extract_prompt": (
            "Extract social platforms as a list and posting frequency. "
            "Return JSON: {\"favorite_platforms\": [\"...\"], \"posting_frequency\": \"...\"}"
        ),
    },
    {
        "id": "signature_dishes",
        "question": (
            "Dernière question ! Quels sont tes plats ou produits signatures ? "
            "(Les 3-5 trucs qui te représentent le mieux)\n\n"
            "Et il y a des sujets qu'on devrait éviter dans ta communication ?"
        ),
        "extract_prompt": (
            "Extract signature dishes as a list and no-go topics as a list. "
            "Return JSON: {\"signature_dishes\": [\"...\"], \"no_go_topics\": [\"...\"]}"
        ),
    },
]

TOTAL_STEPS = len(ONBOARDING_QUESTIONS)


class OnboardingAgent:
    """Manages the conversational onboarding flow that builds BusinessDNA."""

    def __init__(self) -> None:
        self._firestore = FirestoreService()
        self._client = None

    def _get_client(self):
        """Lazy Anthropic client (sync — Haiku calls are fast)."""
        if self._client is None:
            settings = get_settings()
            if not settings.anthropic_api_key:
                raise RuntimeError("Anthropic API key not configured")
            import anthropic
            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self._client

    async def get_dna(self, business_id: str) -> BusinessDNA | None:
        """Load existing DNA from Firestore."""
        data = await self._firestore.get_subcollection_doc(
            "businesses", business_id, "dna", "profile",
        )
        if data is None:
            return None
        return BusinessDNA.from_dict(data)

    async def save_dna(self, business_id: str, dna: BusinessDNA) -> bool:
        """Save DNA to Firestore."""
        return await self._firestore.set_subcollection_doc(
            "businesses", business_id, "dna", "profile",
            dna.to_dict(),
        )

    def get_question(self, step: int) -> dict[str, str] | None:
        """Get question for a given step (0-indexed)."""
        if 0 <= step < TOTAL_STEPS:
            return ONBOARDING_QUESTIONS[step]
        return None

    def extract_answer(self, step: int, user_answer: str) -> dict[str, Any]:
        """Use Claude Haiku to extract structured data from user's free-text answer."""
        question_def = self.get_question(step)
        if question_def is None:
            return {}

        try:
            client = self._get_client()
            settings = get_settings()
            model = getattr(settings, "ilyas_onboarding_model", "claude-haiku-4-5-20241022")

            response = client.messages.create(
                model=model,
                max_tokens=256,
                temperature=0,
                system=(
                    "Tu es un extracteur de données. Extrais les informations demandées "
                    "de la réponse de l'utilisateur. Réponds UNIQUEMENT en JSON valide, "
                    "sans texte autour. Si une information n'est pas mentionnée, "
                    "mets une chaîne vide ou une liste vide."
                ),
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Question posée : {question_def['question']}\n\n"
                            f"Réponse de l'utilisateur : {user_answer}\n\n"
                            f"{question_def['extract_prompt']}"
                        ),
                    },
                ],
            )

            raw_text = response.content[0].text.strip()
            # Handle potential markdown code blocks
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            extracted = json.loads(raw_text)
            logger.info(
                "Onboarding extraction step=%d result=%s",
                step, json.dumps(extracted, ensure_ascii=False),
            )
            return extracted

        except Exception as exc:
            logger.warning("Onboarding extraction failed step=%d: %s", step, exc)
            return {}

    async def process_answer(
        self,
        business_id: str,
        step: int,
        user_answer: str,
    ) -> dict[str, Any]:
        """Process a user answer: extract data, update DNA, return next question.

        Returns:
            {
                "step": current step,
                "extracted": {...},
                "next_step": next step or None if complete,
                "next_question": question text or None,
                "dna": current DNA dict,
                "complete": bool,
            }
        """
        # Load or create DNA
        dna = await self.get_dna(business_id) or BusinessDNA()

        # Extract structured data from answer
        extracted = self.extract_answer(step, user_answer)

        # Store raw answer
        question_def = self.get_question(step)
        if question_def:
            dna.raw_answers[question_def["id"]] = user_answer

        # Merge extracted fields into DNA
        for key, value in extracted.items():
            if hasattr(dna, key) and value:
                setattr(dna, key, value)

        # Check if complete
        next_step = step + 1
        complete = next_step >= TOTAL_STEPS

        if complete:
            dna.onboarding_complete = True

        # Save DNA
        await self.save_dna(business_id, dna)

        # Build response
        result: dict[str, Any] = {
            "step": step,
            "extracted": extracted,
            "next_step": next_step if not complete else None,
            "next_question": None,
            "dna": dna.to_dict(),
            "complete": complete,
        }

        if not complete:
            next_q = self.get_question(next_step)
            if next_q:
                result["next_question"] = next_q["question"]

        return result

    async def start_onboarding(self, business_id: str) -> dict[str, Any]:
        """Start or resume onboarding — returns current step and question."""
        dna = await self.get_dna(business_id)

        if dna and dna.onboarding_complete:
            return {
                "step": TOTAL_STEPS,
                "question": None,
                "complete": True,
                "dna": dna.to_dict(),
            }

        # Determine current step from raw_answers
        current_step = 0
        if dna:
            for i, q in enumerate(ONBOARDING_QUESTIONS):
                if q["id"] in dna.raw_answers:
                    current_step = i + 1

        question = self.get_question(current_step)
        return {
            "step": current_step,
            "question": question["question"] if question else None,
            "complete": False,
            "dna": dna.to_dict() if dna else BusinessDNA().to_dict(),
        }

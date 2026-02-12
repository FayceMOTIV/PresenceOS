"""
PresenceOS — Reputation Manager (Feature 3)

Manages Google/Facebook/TripAdvisor reviews with:
- Unified review feed across platforms
- Sentiment analysis (positive/negative/neutral)
- AI-generated response suggestions in brand voice
- Review stats and trends

In dev mode, returns realistic mock restaurant review data.
"""
import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

import structlog

logger = structlog.get_logger()

# Mock review data for restaurant context
_MOCK_REVIEWS = [
    {"author": "Marie L.", "platform": "google", "rating": 5, "text": "Excellent restaurant ! Le burger signature est incroyable. Service rapide et equipe tres agreable.", "sentiment": "positive"},
    {"author": "Pierre D.", "platform": "google", "rating": 4, "text": "Tres bonne cuisine, les portions sont genereuses. Seul bemol, l'attente un peu longue le samedi.", "sentiment": "positive"},
    {"author": "Sophie M.", "platform": "tripadvisor", "rating": 3, "text": "Cuisine correcte mais rien d'exceptionnel. Le cadre est sympa par contre.", "sentiment": "neutral"},
    {"author": "Lucas R.", "platform": "facebook", "rating": 5, "text": "Mon restaurant prefere du quartier ! Les tacos sont a tomber. Je recommande a 100%.", "sentiment": "positive"},
    {"author": "Emma B.", "platform": "google", "rating": 2, "text": "Decu par ma derniere visite. Le plat etait froid et le serveur peu aimable.", "sentiment": "negative"},
    {"author": "Thomas K.", "platform": "tripadvisor", "rating": 4, "text": "Super brunch du dimanche. Les pancakes sont delicieux et le cafe excellent.", "sentiment": "positive"},
    {"author": "Julie F.", "platform": "facebook", "rating": 5, "text": "Anniversaire reussi grace a vous ! Merci pour le gateau surprise. Toute l'equipe etait top.", "sentiment": "positive"},
    {"author": "Antoine V.", "platform": "google", "rating": 1, "text": "Reservation non honoree malgre confirmation. Tres decu, je ne reviendrai pas.", "sentiment": "negative"},
]

_AI_RESPONSES = {
    "positive": [
        "Merci beaucoup {author} pour ce magnifique retour ! Nous sommes ravis que vous ayez apprecie votre experience. Au plaisir de vous revoir tres bientot !",
        "Wow, merci {author} ! Votre avis nous fait chaud au coeur. Toute l'equipe est motivee a vous offrir la meilleure experience possible. A bientot !",
    ],
    "neutral": [
        "Merci {author} pour votre retour honnete. Nous prenons vos remarques en compte pour nous ameliorer. N'hesitez pas a nous donner une seconde chance !",
    ],
    "negative": [
        "Nous sommes sincèrement desoles {author} pour cette experience decevante. Ce n'est pas le niveau de service que nous souhaitons offrir. Pourriez-vous nous contacter en MP pour que nous puissions en discuter ? Merci.",
        "{author}, merci de nous avoir fait part de votre insatisfaction. Nous prenons cela très au serieux et allons immediatement rectifier cela. Nous aimerions vous offrir une nouvelle experience. Contactez-nous !",
    ],
}

# In-memory stores
_reviews: dict[str, list[dict]] = {}
_responses: dict[str, dict] = {}


class ReputationManagerService:
    """Manage reviews and reputation across platforms."""

    def _ensure_reviews(self, brand_id: str) -> list[dict]:
        """Ensure mock reviews exist for a brand."""
        if brand_id not in _reviews:
            reviews = []
            now = datetime.now(timezone.utc)
            for i, mock in enumerate(_MOCK_REVIEWS):
                reviews.append({
                    "id": str(uuid.uuid4()),
                    "brand_id": brand_id,
                    "platform": mock["platform"],
                    "author": mock["author"],
                    "rating": mock["rating"],
                    "text": mock["text"],
                    "sentiment": mock["sentiment"],
                    "responded": False,
                    "response": None,
                    "created_at": (now - timedelta(days=random.randint(1, 30))).isoformat(),
                })
            reviews.sort(key=lambda r: r["created_at"], reverse=True)
            _reviews[brand_id] = reviews
        return _reviews[brand_id]

    def get_reviews(
        self,
        brand_id: str,
        platform: str | None = None,
        sentiment: str | None = None,
        responded: bool | None = None,
    ) -> list[dict[str, Any]]:
        """Get reviews with optional filters."""
        reviews = self._ensure_reviews(brand_id)
        if platform:
            reviews = [r for r in reviews if r["platform"] == platform]
        if sentiment:
            reviews = [r for r in reviews if r["sentiment"] == sentiment]
        if responded is not None:
            reviews = [r for r in reviews if r["responded"] == responded]
        return reviews

    def get_review(self, review_id: str) -> dict[str, Any] | None:
        """Get a single review."""
        for reviews in _reviews.values():
            for r in reviews:
                if r["id"] == review_id:
                    return r
        return None

    def suggest_response(self, review_id: str) -> dict[str, Any] | None:
        """Generate an AI response suggestion for a review."""
        review = self.get_review(review_id)
        if not review:
            return None

        sentiment = review["sentiment"]
        templates = _AI_RESPONSES.get(sentiment, _AI_RESPONSES["neutral"])
        response_text = random.choice(templates).format(author=review["author"])

        return {
            "review_id": review_id,
            "suggested_response": response_text,
            "sentiment": sentiment,
            "tone": "empathique" if sentiment == "negative" else "chaleureux",
        }

    def respond_to_review(self, review_id: str, response_text: str) -> dict[str, Any] | None:
        """Mark a review as responded with the given text."""
        review = self.get_review(review_id)
        if not review:
            return None

        review["responded"] = True
        review["response"] = response_text
        review["responded_at"] = datetime.now(timezone.utc).isoformat()
        logger.info("review_responded", review_id=review_id)
        return review

    def get_stats(self, brand_id: str) -> dict[str, Any]:
        """Get reputation statistics."""
        reviews = self._ensure_reviews(brand_id)
        total = len(reviews)
        if total == 0:
            return {"brand_id": brand_id, "total": 0, "avg_rating": 0}

        return {
            "brand_id": brand_id,
            "total": total,
            "avg_rating": round(sum(r["rating"] for r in reviews) / total, 1),
            "by_sentiment": {
                "positive": sum(1 for r in reviews if r["sentiment"] == "positive"),
                "neutral": sum(1 for r in reviews if r["sentiment"] == "neutral"),
                "negative": sum(1 for r in reviews if r["sentiment"] == "negative"),
            },
            "by_platform": {
                "google": sum(1 for r in reviews if r["platform"] == "google"),
                "facebook": sum(1 for r in reviews if r["platform"] == "facebook"),
                "tripadvisor": sum(1 for r in reviews if r["platform"] == "tripadvisor"),
            },
            "response_rate": round(sum(1 for r in reviews if r["responded"]) / total * 100, 1),
            "pending_responses": sum(1 for r in reviews if not r["responded"]),
        }

"""
PresenceOS — Business DNA Model (Sprint 4)

Dataclass representing the editorial genome of a business,
built through Ilyas conversational onboarding.
Stored in Firestore at businesses/{id}/dna/profile.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class BusinessDNA:
    """Editorial genome of a business — built by Ilyas during onboarding."""

    # Identity
    business_name: str = ""
    business_type: str = ""        # ex: "restaurant", "boulangerie", "bar"
    cuisine_style: str = ""        # ex: "cuisine libanaise", "pizza napolitaine"
    city: str = ""
    neighborhood: str = ""         # quartier

    # Personality
    ambiance: str = ""             # ex: "cosy et familial", "branché et moderne"
    unique_selling_point: str = ""  # ce qui les différencie
    target_audience: str = ""      # ex: "familles avec enfants", "jeunes actifs 25-35"
    tone_of_voice: str = ""        # ex: "chaleureux et gourmand", "pro et élégant"

    # Content preferences
    favorite_platforms: list[str] = field(default_factory=list)
    posting_frequency: str = ""    # ex: "3 fois par semaine", "tous les jours"
    content_themes: list[str] = field(default_factory=list)
    no_go_topics: list[str] = field(default_factory=list)

    # Operational
    opening_hours: str = ""
    signature_dishes: list[str] = field(default_factory=list)
    price_range: str = ""          # ex: "€€", "€€€"

    # Meta
    onboarding_complete: bool = False
    raw_answers: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for Firestore storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BusinessDNA:
        """Deserialize from Firestore document."""
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)

    def to_system_prompt_section(self) -> str:
        """Format DNA as a section for Ilyas system prompt injection."""
        lines: list[str] = ["ADN DU COMMERCE (appris pendant l'onboarding) :"]

        if self.business_name:
            lines.append(f"- Nom : {self.business_name}")
        if self.business_type:
            lines.append(f"- Type : {self.business_type}")
        if self.cuisine_style:
            lines.append(f"- Cuisine : {self.cuisine_style}")
        if self.city:
            loc = self.city
            if self.neighborhood:
                loc += f" ({self.neighborhood})"
            lines.append(f"- Localisation : {loc}")
        if self.ambiance:
            lines.append(f"- Ambiance : {self.ambiance}")
        if self.unique_selling_point:
            lines.append(f"- Point fort : {self.unique_selling_point}")
        if self.target_audience:
            lines.append(f"- Cible : {self.target_audience}")
        if self.tone_of_voice:
            lines.append(f"- Ton : {self.tone_of_voice}")
        if self.favorite_platforms:
            lines.append(f"- Réseaux préférés : {', '.join(self.favorite_platforms)}")
        if self.posting_frequency:
            lines.append(f"- Fréquence : {self.posting_frequency}")
        if self.content_themes:
            lines.append(f"- Thèmes favoris : {', '.join(self.content_themes)}")
        if self.no_go_topics:
            lines.append(f"- Sujets interdits : {', '.join(self.no_go_topics)}")
        if self.signature_dishes:
            lines.append(f"- Plats signatures : {', '.join(self.signature_dishes)}")
        if self.price_range:
            lines.append(f"- Gamme de prix : {self.price_range}")

        return "\n".join(lines) if len(lines) > 1 else ""

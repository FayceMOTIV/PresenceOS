"""
PresenceOS - Content Calendar Service
Seasonal events + optimal posting slots.
"""
from datetime import datetime, timezone, timedelta

SEASONAL_EVENTS = [
    {"month": 1, "day": 1, "name": "Nouvel An", "theme": "voeux, nouveau départ"},
    {"month": 1, "day": 6, "name": "Épiphanie", "theme": "galette des rois"},
    {"month": 2, "day": 2, "name": "Chandeleur", "theme": "crêpes"},
    {"month": 2, "day": 14, "name": "Saint-Valentin", "theme": "dîner romantique, menu couple"},
    {"month": 3, "day": 8, "name": "Journée de la femme", "theme": "offre spéciale"},
    {"month": 3, "day": 20, "name": "Printemps", "theme": "nouveaux plats, fraîcheur, terrasse"},
    {"month": 4, "day": 1, "name": "Poisson d'avril", "theme": "humour, plat surprise"},
    {"month": 5, "day": 1, "name": "Fête du travail", "theme": "repos, brunch"},
    {"month": 5, "day": 25, "name": "Fête des mères", "theme": "menu familial, brunch"},
    {"month": 6, "day": 15, "name": "Fête des pères", "theme": "bbq, viande, bière"},
    {"month": 6, "day": 21, "name": "Fête de la musique", "theme": "soirée spéciale"},
    {"month": 7, "day": 14, "name": "14 Juillet", "theme": "menu tricolore, terrasse"},
    {"month": 9, "day": 1, "name": "Rentrée", "theme": "nouveau menu, formule midi"},
    {"month": 10, "day": 31, "name": "Halloween", "theme": "décoration, plat effrayant"},
    {"month": 11, "day": 20, "name": "Beaujolais Nouveau", "theme": "vin, dégustation"},
    {"month": 12, "day": 25, "name": "Noël", "theme": "menu fêtes, réservation"},
    {"month": 12, "day": 31, "name": "Saint-Sylvestre", "theme": "soirée, menu réveillon"},
]

# Ramadan (approximate for 2026 — adjust yearly)
RAMADAN_2026 = {"start": "2026-02-17", "end": "2026-03-19", "theme": "iftar, ftour, menu ramadan"}


def get_upcoming_events(days_ahead: int = 14) -> list[dict]:
    """Get seasonal events within the next N days."""
    now = datetime.now(timezone.utc)
    events = []

    for event in SEASONAL_EVENTS:
        try:
            event_date = datetime(now.year, event["month"], event["day"], tzinfo=timezone.utc)
            if event_date < now:
                event_date = event_date.replace(year=now.year + 1)
            delta = (event_date - now).days
            if 0 <= delta <= days_ahead:
                events.append({
                    **event,
                    "date": event_date.isoformat(),
                    "days_until": delta,
                })
        except ValueError:
            continue

    # Check Ramadan
    try:
        ram_start = datetime.fromisoformat(RAMADAN_2026["start"]).replace(tzinfo=timezone.utc)
        ram_end = datetime.fromisoformat(RAMADAN_2026["end"]).replace(tzinfo=timezone.utc)
        if ram_start <= now <= ram_end:
            events.append({
                "name": "Ramadan",
                "theme": RAMADAN_2026["theme"],
                "date": now.isoformat(),
                "days_until": 0,
            })
    except Exception:
        pass

    return sorted(events, key=lambda e: e.get("days_until", 999))


# Optimal posting times per platform (Europe/Paris)
OPTIMAL_SLOTS = {
    "instagram": [
        {"day": "monday", "hour": 12, "minute": 0},
        {"day": "tuesday", "hour": 11, "minute": 30},
        {"day": "wednesday", "hour": 12, "minute": 0},
        {"day": "thursday", "hour": 18, "minute": 30},
        {"day": "friday", "hour": 12, "minute": 0},
        {"day": "saturday", "hour": 11, "minute": 0},
        {"day": "sunday", "hour": 10, "minute": 30},
    ],
    "tiktok": [
        {"day": "tuesday", "hour": 19, "minute": 0},
        {"day": "thursday", "hour": 12, "minute": 0},
        {"day": "friday", "hour": 17, "minute": 0},
        {"day": "saturday", "hour": 20, "minute": 0},
    ],
    "facebook": [
        {"day": "wednesday", "hour": 11, "minute": 0},
        {"day": "friday", "hour": 13, "minute": 0},
        {"day": "saturday", "hour": 12, "minute": 0},
    ],
}

DAY_MAP = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}


def get_next_optimal_slot(platform: str = "instagram", from_date: datetime | None = None) -> datetime:
    """Get the next optimal posting time for a platform."""
    now = from_date or datetime.now(timezone.utc)
    slots = OPTIMAL_SLOTS.get(platform, OPTIMAL_SLOTS["instagram"])

    candidates = []
    for slot in slots:
        target_day = DAY_MAP[slot["day"]]
        current_day = now.weekday()
        days_ahead = (target_day - current_day) % 7
        if days_ahead == 0 and (now.hour > slot["hour"] or (now.hour == slot["hour"] and now.minute >= slot["minute"])):
            days_ahead = 7
        candidate = now.replace(hour=slot["hour"], minute=slot["minute"], second=0, microsecond=0) + timedelta(days=days_ahead)
        candidates.append(candidate)

    return min(candidates) if candidates else now + timedelta(days=1)

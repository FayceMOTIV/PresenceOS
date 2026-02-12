"""
PresenceOS - Engagement Score Predictor

Heuristic-based engagement prediction (0-100).
No AI calls — pure rules engine, instant response.
"""
import re


PLATFORM_CHAR_LIMITS = {
    "instagram_post": 2200,
    "instagram_story": 2200,
    "instagram_reel": 2200,
    "facebook": 63206,
    "linkedin": 3000,
    "tiktok": 150,
}

OPTIMAL_HASHTAG_RANGES = {
    "instagram_post": (8, 15),
    "instagram_story": (3, 8),
    "instagram_reel": (5, 10),
    "facebook": (3, 5),
    "linkedin": (3, 5),
    "tiktok": (3, 5),
}

OPTIMAL_LENGTH_RANGES = {
    "instagram_post": (100, 300),
    "instagram_story": (20, 100),
    "instagram_reel": (50, 200),
    "facebook": (100, 500),
    "linkedin": (150, 600),
    "tiktok": (30, 120),
}

# Regex for detecting emojis (broad Unicode ranges)
_EMOJI_PATTERN = re.compile(
    "[\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA00-\U0001FA6F"  # chess symbols
    "\U0001FA70-\U0001FAFF"  # symbols extended-A
    "]+",
    flags=re.UNICODE,
)

# CTA patterns (French)
_CTA_PATTERNS = [
    r"\?$",
    r"commentez?|commente",
    r"partage[rz]?",
    r"tag[gue]*[ez]",
    r"lien en bio",
    r"clique[rz]?",
    r"commande[rz]?",
    r"reserve[rz]?",
    r"decouvr[eiz]",
    r"profite[rz]?",
    r"rejoign",
    r"abonne[rz]?-?(toi|vous)",
    r"DM|MP",
    r"swipe",
    r"enregistre",
    r"like[rz]?",
]


def compute_engagement_score(
    caption: str,
    hashtags: list[str],
    platform: str = "instagram_post",
) -> dict:
    """Compute heuristic engagement score (0-100).

    Returns dict with total and breakdown per criterion.
    """
    scores: dict[str, int] = {}

    # 1. Hook detection (+20): first line has question, bold statement, or emoji
    first_line = caption.split("\n")[0].strip() if caption else ""
    has_hook = bool(
        re.search(r"\?", first_line)
        or re.match(r"^[A-Z\u00C0-\u00FF]{3,}", first_line)
        or _EMOJI_PATTERN.match(first_line)
        or (len(first_line) > 5 and first_line.endswith("!"))
    )
    scores["has_hook"] = 20 if has_hook else 0

    # 2. CTA detection (+15)
    has_cta = any(
        re.search(p, caption, re.IGNORECASE | re.MULTILINE)
        for p in _CTA_PATTERNS
    )
    scores["has_cta"] = 15 if has_cta else 0

    # 3. Hashtag count (+15)
    min_h, max_h = OPTIMAL_HASHTAG_RANGES.get(platform, (5, 10))
    h_count = len(hashtags)
    if min_h <= h_count <= max_h:
        scores["hashtag_score"] = 15
    elif h_count > 0:
        scores["hashtag_score"] = 8
    else:
        scores["hashtag_score"] = 0

    # 4. Emoji usage (+10): 1-3 emojis is ideal
    emoji_count = len(_EMOJI_PATTERN.findall(caption))
    if 1 <= emoji_count <= 3:
        scores["emoji_score"] = 10
    elif emoji_count > 3:
        scores["emoji_score"] = 5
    else:
        scores["emoji_score"] = 0

    # 5. Length optimization (+15)
    char_count = len(caption)
    opt_min, opt_max = OPTIMAL_LENGTH_RANGES.get(platform, (100, 300))
    if opt_min <= char_count <= opt_max:
        scores["length_score"] = 15
    elif char_count > 0:
        scores["length_score"] = 7
    else:
        scores["length_score"] = 0

    # 6. Line breaks for readability (+10)
    line_count = caption.count("\n")
    if line_count >= 2:
        scores["readability_score"] = 10
    elif line_count >= 1:
        scores["readability_score"] = 5
    else:
        scores["readability_score"] = 0

    # 7. Hashtag mix — short + long tags (+15)
    short_tags = [h for h in hashtags if len(h) <= 12]
    long_tags = [h for h in hashtags if len(h) > 12]
    if short_tags and long_tags:
        scores["trending_score"] = 15
    elif hashtags:
        scores["trending_score"] = 8
    else:
        scores["trending_score"] = 0

    scores["total"] = sum(scores.values())
    return scores

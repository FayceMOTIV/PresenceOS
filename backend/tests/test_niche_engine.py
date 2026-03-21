"""
Tests for the Niche Engine — detect_niche, get_niche_system_prompt, NICHES data.
"""
import pytest

from app.data.niches import detect_niche, get_niche_system_prompt, NICHES, NICHE_ALIASES


# ── detect_niche exact match ──

def test_detect_exact_niche():
    niche = detect_niche("restaurant")
    assert niche["label"] == "🍕 Restaurant / Café"


def test_detect_medecin_exact():
    niche = detect_niche("medecin")
    assert "Médecin" in niche["label"]


# ── detect_niche alias match ──

def test_detect_alias_medecin():
    niche = detect_niche("médecin")
    assert "Médecin" in niche["label"]


def test_detect_alias_coiffeur():
    niche = detect_niche("coiffeuse")
    assert "Coiffeur" in niche["label"]


# ── detect_niche partial match ──

def test_detect_partial_match():
    niche = detect_niche("coiffeur homme paris")
    assert "Coiffeur" in niche["label"]


# ── detect_niche fallback ──

def test_detect_unknown_defaults_restaurant():
    niche = detect_niche("xyz_unknown_123")
    assert niche["label"] == "🍕 Restaurant / Café"


def test_detect_empty_defaults_restaurant():
    niche = detect_niche("")
    assert niche["label"] == "🍕 Restaurant / Café"


# ── NICHES data integrity ──

def test_all_niches_have_required_fields():
    required = [
        "tone", "audience", "platforms_priority", "content_pillars",
        "viral_hooks", "cta", "legal_constraints", "best_formats",
        "taboo_subjects", "video_style", "content_ratio",
    ]
    for key, niche in NICHES.items():
        for field in required:
            assert field in niche, f"Niche '{key}' missing field '{field}'"


def test_all_niches_have_posting_times():
    for key, niche in NICHES.items():
        assert "posting_times" in niche, f"Niche '{key}' missing posting_times"


def test_15_niches_available():
    assert len(NICHES) >= 15


def test_all_aliases_point_to_valid_niches():
    for alias, niche_key in NICHE_ALIASES.items():
        assert niche_key in NICHES, f"Alias '{alias}' points to unknown niche '{niche_key}'"


# ── get_niche_system_prompt ──

def test_niche_system_prompt_not_empty():
    niche = detect_niche("medecin")
    brand_dna = {"name": "Cabinet Dr Dupont", "description": "Médecin généraliste"}
    prompt = get_niche_system_prompt(niche, brand_dna)
    assert len(prompt) > 500
    assert "SNIPER" in prompt
    assert "Dr Dupont" in prompt


def test_niche_system_prompt_restaurant():
    niche = detect_niche("restaurant")
    brand_dna = {"name": "Le Family's", "description": "Restaurant familial"}
    prompt = get_niche_system_prompt(niche, brand_dna)
    assert "Family's" in prompt
    assert "niche_expertise" in prompt


# ── Legal constraints ──

def test_legal_constraints_for_medecin():
    niche = detect_niche("medecin")
    assert len(niche["legal_constraints"]) > 0
    assert any("CNOM" in c for c in niche["legal_constraints"])


def test_no_legal_constraints_for_restaurant():
    niche = detect_niche("restaurant")
    assert len(niche["legal_constraints"]) == 0


def test_taboo_subjects_for_avocat():
    niche = detect_niche("avocat")
    assert len(niche["taboo_subjects"]) > 0


# ── Tone computation ──

def test_tone_expert_high_for_avocat():
    niche = detect_niche("avocat")
    assert niche["tone"]["expert"] > 0.9


def test_tone_warmth_high_for_coiffeur():
    niche = detect_niche("coiffeur")
    assert niche["tone"]["warmth"] > 0.8


# ── Content ratio sums approximately to 1.0 ──

def test_content_ratio_sums():
    for key, niche in NICHES.items():
        total = sum(niche["content_ratio"].values())
        assert 0.95 <= total <= 1.05, f"Niche '{key}' content_ratio sums to {total}"

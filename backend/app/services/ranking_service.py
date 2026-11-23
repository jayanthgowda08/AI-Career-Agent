"""
services/ranking_service.py — Multi-Factor Ranking & Skill Gap Engine

Implements an interpretable weighted recommendation scoring model:
- Skill Similarity (weight: 0.35)
- Semantic Vector Similarity (weight: 0.25)
- Role Relevance (weight: 0.15)
- Location Compatibility (weight: 0.15)
- Experience Compatibility (weight: 0.10)
"""

import re
from typing import List, Tuple, Set
from app.models.job import Job
from app.models.profile import CandidateProfile
from app.schemas.recommendation import ScoreBreakdown


def normalize_token(token: str) -> str:
    """Normalizes a skill/role string for case-insensitive robust comparison."""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", token).lower().strip()
    # Normalize common abbreviations
    synonyms = {
        "reactjs": "react",
        "react js": "react",
        "nodejs": "node",
        "node js": "node",
        "postgres": "postgresql",
        "fast api": "fastapi",
        "py torch": "pytorch",
        "tf": "tensorflow",
    }
    return synonyms.get(cleaned, cleaned)


def is_skill_match(skill_a: str, skill_b: str) -> bool:
    """
    High-precision skill comparison:
    - Normalizes common abbreviations and synonyms.
    - Prevents false-positive substring matches (e.g. 'C' in 'CSS', 'Java' in 'JavaScript', 'R' in 'React').
    - Requires exact token equality for short identifiers (<= 3 chars).
    """
    a = normalize_token(skill_a)
    b = normalize_token(skill_b)
    if a == b:
        return True
    if len(a) <= 3 or len(b) <= 3:
        return a == b
    pattern_a = r"(?:\b|_)" + re.escape(a) + r"(?:\b|_)"
    if re.search(pattern_a, b):
        return True
    pattern_b = r"(?:\b|_)" + re.escape(b) + r"(?:\b|_)"
    return bool(re.search(pattern_b, a))


def analyze_skill_overlap(
    candidate_skills: List[str],
    job_required_skills: List[str],
    job_preferred_skills: List[str] = None,
) -> Tuple[List[str], List[str], List[str], float]:
    """
    Compares candidate skills with job required and preferred skills.
    Accurately handles:
    - Full match: all required skills matched (score ~1.0)
    - Partial match: fraction of skills matched (score proportional to overlap)
    - No match: 0 skills matched (score = 0.0)
    """
    if not candidate_skills:
        return [], list(job_required_skills or []), list(job_preferred_skills or []), 0.0

    if not job_required_skills and not job_preferred_skills:
        return [], [], [], 0.0

    job_pref = job_preferred_skills or []
    matching = []
    missing_req = []
    missing_pref = []

    # Check required skills (highest weight)
    for req in job_required_skills:
        matched = False
        for cand in candidate_skills:
            if is_skill_match(req, cand):
                matching.append(req)
                matched = True
                break
        if not matched:
            missing_req.append(req)

    # Check preferred skills
    for pref in job_pref:
        matched = False
        for cand in candidate_skills:
            if is_skill_match(pref, cand):
                if pref not in matching:
                    matching.append(pref)
                matched = True
                break
        if not matched:
            missing_pref.append(pref)

    # Accurate proportional scoring: 75% required, 25% preferred
    req_ratio = len([m for m in matching if m in job_required_skills]) / len(job_required_skills) if job_required_skills else 1.0
    pref_ratio = len([m for m in matching if m in job_pref]) / len(job_pref) if job_pref else 0.0
    skill_score = (0.75 * req_ratio) + (0.25 * pref_ratio)

    return matching, missing_req, missing_pref, round(skill_score, 4)


def compute_role_score(job_title: str, preferred_roles: List[str]) -> float:
    """Calculates relevance score between job title and preferred roles."""
    if not preferred_roles:
        return 0.5  # Neutral if no preference specified

    job_title_norm = normalize_token(job_title)
    max_score = 0.0

    for role in preferred_roles:
        role_norm = normalize_token(role)
        if role_norm == job_title_norm:
            return 1.0  # Exact match
        elif role_norm in job_title_norm or job_title_norm in role_norm:
            max_score = max(max_score, 0.85)
        else:
            # Word overlap ratio
            r_words = set(role_norm.split())
            j_words = set(job_title_norm.split())
            common = r_words.intersection(j_words)
            if common:
                overlap = len(common) / max(len(r_words), len(j_words))
                max_score = max(max_score, overlap * 0.75)

    return round(max_score, 4)


def compute_location_score(
    job_location: str,
    preferred_locations: List[str],
    candidate_location: str = None,
) -> float:
    """Calculates location score considering preferences and Remote flexibility."""
    job_loc_lower = job_location.lower()

    # Remote jobs are universally accessible
    if "remote" in job_loc_lower:
        return 0.95

    # Check candidate preferences
    all_prefs = [p.lower() for p in (preferred_locations or [])]
    if candidate_location:
        all_prefs.append(candidate_location.lower())

    if not all_prefs:
        return 0.6  # Neutral

    for pref in all_prefs:
        if pref in job_loc_lower or job_loc_lower in pref:
            return 1.0

    return 0.2  # Different location and not remote


def compute_experience_score(job: Job, candidate_exp_years: int = 2) -> float:
    """Calculates compatibility based on years of experience required."""
    req_years = job.min_years_experience
    if candidate_exp_years >= req_years:
        return 1.0  # Fully qualified
    elif req_years - candidate_exp_years <= 1:
        return 0.8  # Slight stretch (1 year gap is normal)
    elif req_years - candidate_exp_years <= 2:
        return 0.5  # Moderate stretch
    else:
        return 0.2  # Significant stretch


def calculate_match_score(
    job: Job,
    profile: CandidateProfile,
    semantic_similarity: float,
    weights: dict = None,
) -> Tuple[int, ScoreBreakdown, List[str], List[str], List[str]]:
    """
    Computes composite match score (0-100) and compiles reasons and skill breakdowns.
    """
    w = weights or {
        "skill": 0.35,
        "semantic": 0.25,
        "role": 0.15,
        "location": 0.15,
        "experience": 0.10,
    }

    # 1. Component scores
    matching, missing_req, missing_pref, skill_score = analyze_skill_overlap(
        profile.skills, job.required_skills, job.preferred_skills
    )
    role_score = compute_role_score(job.title, profile.preferred_roles)
    location_score = compute_location_score(
        job.location, profile.preferred_locations, profile.location
    )
    # Estimate candidate years: length of experience list or default to 2
    cand_years = len(profile.experience) if profile.experience else 2
    exp_score = compute_experience_score(job, cand_years)

    # 2. Weighted total (0.0 to 1.0)
    composite = (
        (w["skill"] * skill_score)
        + (w["semantic"] * semantic_similarity)
        + (w["role"] * role_score)
        + (w["location"] * location_score)
        + (w["experience"] * exp_score)
    )

    # Strict accuracy penalty: if candidate has ZERO matching skills and no role match,
    # prevent false positive inflation from location/experience
    if len(matching) == 0 and role_score < 0.3:
        composite *= 0.3  # Drastically reduces score to <= 8%

    match_percentage = int(round(max(0.0, min(1.0, composite)) * 100))

    # 3. Generate human-readable reasons
    reasons = []
    if matching:
        reasons.append(f"Matched {len(matching)} key skill(s): {', '.join(matching[:4])}")
    if role_score >= 0.8:
        reasons.append(f"Title closely matches preferred role")
    if location_score >= 0.9:
        if "remote" in job.location.lower():
            reasons.append("Remote friendly opportunity")
        else:
            reasons.append(f"Matches location preference ({job.location})")
    if semantic_similarity >= 0.5:
        reasons.append(f"High conceptual match based on resume profile")

    breakdown = ScoreBreakdown(
        skill_score=skill_score,
        semantic_score=round(semantic_similarity, 4),
        role_score=role_score,
        location_score=location_score,
        experience_score=exp_score,
    )

    return match_percentage, breakdown, matching, missing_req, reasons

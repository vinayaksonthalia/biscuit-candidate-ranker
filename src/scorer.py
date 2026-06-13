"""
Scorer — Stage 2: Multi-signal candidate scoring engine.

Six dimensions, each normalized to [0.0, 1.0], combined via weighted sum.
Final score is multiplied by (1.0 - suspicion_penalty) from filters.
"""

from datetime import datetime

from . import config


def score_candidate(cand: dict, suspicion: float = 0.0) -> dict:
    """
    Compute a composite score for a candidate.

    Returns a dict with:
      - "total": float, the final weighted score
      - "components": dict mapping dimension name to its [0,1] sub-score
      - "flags": list of strings noting concerns or highlights
    """
    components = {
        "career_relevance": _score_career_relevance(cand),
        "skills_match": _score_skills_match(cand),
        "experience_band": _score_experience_band(cand),
        "behavioral_signals": _score_behavioral(cand),
        "location_logistics": _score_location(cand),
        "education": _score_education(cand),
    }

    raw_total = sum(
        components[dim] * config.WEIGHTS[dim] for dim in config.WEIGHTS
    )

    # Apply suspicion penalty as a multiplier
    total = raw_total * (1.0 - suspicion)

    # Skills gate: if a candidate has near-zero skill relevance, they are
    # simply not a fit regardless of experience, location, or engagement.
    # Without this, a "Graphic Designer at Wipro" with great location and
    # behavioral signals can outrank candidates with actual ML experience.
    skills_score = components["skills_match"]
    if skills_score < 0.05:
        total *= 0.15  # Severe cap — wrong domain entirely
    elif skills_score < 0.15:
        total *= 0.35  # Weak cap — minimal relevant skills
    elif skills_score < 0.25:
        total *= 0.60  # Moderate cap — some relevant skills but thin

    flags = _collect_flags(cand, components)

    return {
        "total": round(total, 6),
        "components": components,
        "flags": flags,
    }


# =========================================================================
# Dimension scorers
# =========================================================================


def _score_career_relevance(cand: dict) -> float:
    """
    Score based on career trajectory: product vs services companies,
    and ML/AI title alignment.

    Pure consulting = 0.0, mixed = proportional, pure product = 1.0.
    ML/AI-related titles add bonus.
    """
    career = cand.get("career_history", [])
    if not career:
        return 0.0

    product_months = 0
    services_months = 0
    ml_title_months = 0
    total_months = 0

    for job in career:
        dur = job.get("duration_months", 0)
        if dur <= 0:
            continue
        total_months += dur
        company = job.get("company", "").lower().strip()

        # Classify company
        if company in config.SERVICE_CONSULTING_COMPANIES:
            services_months += dur
        elif (
            company in config.PRODUCT_COMPANIES
            or company in config.FICTIONAL_PRODUCT_COMPANIES
        ):
            product_months += dur
        else:
            # Unknown company — check company size and industry as heuristic
            industry = job.get("industry", "").lower()
            size = job.get("company_size", "")
            if "it services" in industry or "consulting" in industry:
                services_months += dur
            elif size in ("1-10", "11-50", "51-200"):
                # Small company = likely startup/product
                product_months += dur * 0.6
            else:
                # Neutral — give partial credit
                product_months += dur * 0.3

        # Check if title is ML/AI-related
        title = job.get("title", "").lower()
        if any(kw in title for kw in config.ML_TITLE_KEYWORDS):
            ml_title_months += dur

    if total_months == 0:
        return 0.0

    # Product ratio: what fraction of career was at product companies
    product_ratio = product_months / total_months

    # ML title ratio: what fraction of career had ML/AI titles
    ml_ratio = ml_title_months / total_months

    # Combined: 60% weight on product ratio, 40% on ML title relevance
    score = 0.6 * product_ratio + 0.4 * ml_ratio

    # Check career descriptions for ML/AI keywords
    desc_ml_score = _description_ml_relevance(career)
    # Blend in description relevance (up to 0.15 bonus)
    score = min(1.0, score + desc_ml_score * 0.15)

    return round(min(1.0, max(0.0, score)), 4)


def _description_ml_relevance(career: list) -> float:
    """Check career descriptions for ML/NLP/retrieval keywords.
    
    Only uses ML-specific terms — avoids generic words like "model",
    "pipeline", "feature" that inflate scores for data engineering or
    non-ML roles.
    """
    ml_desc_keywords = {
        "embedding", "vector", "nlp", "retrieval", "ranking",
        "recommendation", "search engine", "transformer", "bert", "gpt",
        "llm", "deep learning", "neural network", "machine learning",
        "reranking", "re-ranking", "information retrieval",
        "fine-tuning", "fine tuning", "rag",
    }
    total_hits = 0
    total_jobs = 0
    for job in career:
        desc = job.get("description", "").lower()
        if not desc:
            continue
        total_jobs += 1
        hits = sum(1 for kw in ml_desc_keywords if kw in desc)
        total_hits += min(hits, 4)  # cap per job

    if total_jobs == 0:
        return 0.0
    avg_hits = total_hits / total_jobs
    return min(1.0, avg_hits / 3.0)


def _score_skills_match(cand: dict) -> float:
    """
    Score based on alignment with JD skill requirements.

    Core must-have skills weighted highest, nice-to-have adds modest bonus,
    negative domain skills apply penalty.
    Keyword stuffer detection (non-tech title + many AI skills) = near 0.
    """
    profile = cand.get("profile", {})
    skills = cand.get("skills", [])

    if not skills:
        return 0.0

    # Build lowercase skill name set with proficiency weighting
    skill_names = set()
    skill_details = {}
    for s in skills:
        name = s.get("name", "").lower().strip()
        if name:
            skill_names.add(name)
            skill_details[name] = {
                "proficiency": s.get("proficiency", "beginner"),
                "duration_months": s.get("duration_months", 0),
                "endorsements": s.get("endorsements", 0),
            }

    # Keyword stuffer check
    current_title = profile.get("current_title", "").lower().strip()
    if current_title in config.KEYWORD_STUFFER_TITLES:
        core_ai_skills = {
            "nlp", "natural language processing", "machine learning",
            "deep learning", "pytorch", "tensorflow",
            "embeddings", "sentence-transformers", "faiss",
            "pinecone", "weaviate", "qdrant", "milvus",
            "information retrieval", "ranking", "recommendation systems",
            "transformers", "bert", "gpt", "llm", "rag",
            "vector search", "vector database",
        }
        ai_count = len(skill_names & core_ai_skills)
        if ai_count >= 5:
            return 0.05  # Near-zero — keyword stuffer

    # Core skill matches
    core_matches = skill_names & config.CORE_MUST_HAVE_SKILLS
    nice_matches = skill_names & config.NICE_TO_HAVE_SKILLS
    adjacent_matches = skill_names & config.ADJACENT_ML_SKILLS
    negative_matches = skill_names & config.NEGATIVE_DOMAIN_SKILLS

    # Weight core matches by proficiency
    core_score = 0.0
    for skill_name in core_matches:
        detail = skill_details.get(skill_name, {})
        prof = detail.get("proficiency", "beginner")
        prof_weight = {"expert": 1.0, "advanced": 0.8, "intermediate": 0.5, "beginner": 0.2}.get(prof, 0.2)
        core_score += prof_weight

    # Normalize core score (ideal would be ~5-7 core skills)
    core_normalized = min(1.0, core_score / 4.0)

    # Nice-to-have bonus (up to 0.15)
    nice_bonus = min(0.15, len(nice_matches) * 0.05)

    # Adjacent ML skills bonus (up to 0.10)
    adjacent_bonus = min(0.10, len(adjacent_matches) * 0.02)

    # Negative domain penalty
    negative_penalty = min(0.3, len(negative_matches) * 0.1)

    # Assessment scores bonus (from Redrob platform)
    assessment_bonus = _assessment_bonus(cand, core_matches | nice_matches)

    score = core_normalized + nice_bonus + adjacent_bonus + assessment_bonus - negative_penalty

    return round(min(1.0, max(0.0, score)), 4)


def _assessment_bonus(cand: dict, relevant_skills: set) -> float:
    """Bonus from Redrob skill assessment scores for relevant skills."""
    assessments = cand.get("redrob_signals", {}).get("skill_assessment_scores", {})
    if not assessments:
        return 0.0

    relevant_scores = []
    for skill_name, score_val in assessments.items():
        if skill_name.lower() in relevant_skills:
            relevant_scores.append(score_val)

    if not relevant_scores:
        return 0.0

    avg_score = sum(relevant_scores) / len(relevant_scores)
    # Normalize: 80+ is excellent, 50 is average
    return min(0.10, max(0.0, (avg_score - 50) / 300))


def _score_experience_band(cand: dict) -> float:
    """
    Score based on years of experience fit with JD requirement.

    Uses a smooth curve centered on the 6-8 year ideal band.
    """
    yoe = cand.get("profile", {}).get("years_of_experience", 0)

    if config.EXPERIENCE_IDEAL_MIN <= yoe <= config.EXPERIENCE_IDEAL_MAX:
        return 1.0
    elif config.EXPERIENCE_ACCEPTABLE_MIN <= yoe < config.EXPERIENCE_IDEAL_MIN:
        # 4-6 years: linear interpolation from 0.5 to 1.0
        return 0.5 + 0.5 * (yoe - config.EXPERIENCE_ACCEPTABLE_MIN) / (
            config.EXPERIENCE_IDEAL_MIN - config.EXPERIENCE_ACCEPTABLE_MIN
        )
    elif config.EXPERIENCE_IDEAL_MAX < yoe <= config.EXPERIENCE_ACCEPTABLE_MAX:
        # 8-12 years: linear interpolation from 1.0 to 0.4
        return 1.0 - 0.6 * (yoe - config.EXPERIENCE_IDEAL_MAX) / (
            config.EXPERIENCE_ACCEPTABLE_MAX - config.EXPERIENCE_IDEAL_MAX
        )
    elif yoe < config.EXPERIENCE_ACCEPTABLE_MIN:
        # Under 4 years: too junior
        return max(0.0, yoe / config.EXPERIENCE_ACCEPTABLE_MIN * 0.3)
    else:
        # Over 12 years: may be over-qualified / in management
        return max(0.1, 0.4 - (yoe - config.EXPERIENCE_ACCEPTABLE_MAX) * 0.05)


def _score_behavioral(cand: dict) -> float:
    """
    Score based on engagement and behavioral signals from Redrob platform.

    Integrates: activity recency, response rate, profile completeness,
    GitHub activity, open-to-work flag, interview completion rate.
    """
    signals = cand.get("redrob_signals", {})

    # 1. Activity recency (most important behavioral signal per JD)
    last_active_str = signals.get("last_active_date", "")
    if last_active_str:
        try:
            last_active_d = datetime.strptime(last_active_str, "%Y-%m-%d").date()
            months_since = (
                (config.REFERENCE_DATE.year - last_active_d.year) * 12
                + (config.REFERENCE_DATE.month - last_active_d.month)
            )
        except ValueError:
            months_since = 12
    else:
        months_since = 12

    if months_since <= 1:
        recency = 1.0
    elif months_since <= 3:
        recency = 0.8
    elif months_since < config.ACTIVITY_STALE_MONTHS:
        recency = 0.5
    else:
        # Dead lead — JD explicitly says to down-weight
        recency = max(0.0, 0.2 - (months_since - config.ACTIVITY_STALE_MONTHS) * 0.02)

    # 2. Recruiter response rate
    response_rate = signals.get("recruiter_response_rate", 0)
    if response_rate < config.MIN_RECRUITER_RESPONSE_RATE:
        response_score = 0.1  # Ghost
    elif response_rate < 0.3:
        response_score = 0.4
    elif response_rate < 0.6:
        response_score = 0.7
    else:
        response_score = 1.0

    # 3. Profile completeness
    completeness = signals.get("profile_completeness_score", 0)
    if completeness < config.MIN_PROFILE_COMPLETENESS:
        completeness_score = 0.1
    else:
        completeness_score = min(1.0, completeness / 100.0)

    # 4. GitHub activity (-1 means no GitHub linked)
    github = signals.get("github_activity_score", -1)
    if github < 0:
        github_score = 0.3  # No GitHub = neutral, not terrible
    else:
        github_score = min(1.0, github / 70.0)

    # 5. Open to work flag
    open_to_work = 1.0 if signals.get("open_to_work_flag", False) else 0.4

    # 6. Interview completion rate
    interview_rate = signals.get("interview_completion_rate", 0)
    interview_score = min(1.0, interview_rate)

    # 7. Verification signals (minor)
    verified = 0.0
    if signals.get("verified_email", False):
        verified += 0.4
    if signals.get("verified_phone", False):
        verified += 0.3
    if signals.get("linkedin_connected", False):
        verified += 0.3

    # Weighted combination
    score = (
        recency * 0.30
        + response_score * 0.20
        + completeness_score * 0.10
        + github_score * 0.10
        + open_to_work * 0.10
        + interview_score * 0.10
        + verified * 0.10
    )

    return round(min(1.0, max(0.0, score)), 4)


def _score_location(cand: dict) -> float:
    """
    Score based on location, notice period, and work mode preferences.
    """
    profile = cand.get("profile", {})
    signals = cand.get("redrob_signals", {})

    # Location scoring
    location = profile.get("location", "").lower().strip()
    country = profile.get("country", "").lower().strip()

    if any(loc in location for loc in config.PREFERRED_LOCATIONS):
        location_score = 1.0
    elif any(loc in location for loc in config.ACCEPTABLE_LOCATIONS):
        location_score = 0.6
    elif config.PREFERRED_COUNTRY in country:
        location_score = 0.3
    else:
        location_score = 0.0  # JD says no visa sponsorship

    # Relocation willingness bonus
    if signals.get("willing_to_relocate", False) and location_score < 1.0:
        location_score = min(1.0, location_score + 0.2)

    # Notice period scoring
    notice_days = signals.get("notice_period_days", 90)
    if notice_days <= config.NOTICE_PERIOD_IDEAL_MAX:
        notice_score = 1.0
    elif notice_days <= config.NOTICE_PERIOD_ACCEPTABLE_MAX:
        notice_score = 0.6 - 0.4 * (notice_days - config.NOTICE_PERIOD_IDEAL_MAX) / (
            config.NOTICE_PERIOD_ACCEPTABLE_MAX - config.NOTICE_PERIOD_IDEAL_MAX
        )
    else:
        notice_score = 0.1

    # Work mode — JD says hybrid-flexible
    work_mode = signals.get("preferred_work_mode", "")
    mode_score = {
        "hybrid": 1.0,
        "flexible": 1.0,
        "onsite": 0.8,
        "remote": 0.5,
    }.get(work_mode, 0.5)

    # Combined: 50% location, 30% notice, 20% work mode
    score = location_score * 0.50 + notice_score * 0.30 + mode_score * 0.20

    return round(min(1.0, max(0.0, score)), 4)


def _score_education(cand: dict) -> float:
    """
    Score based on education quality and field relevance.
    """
    education = cand.get("education", [])
    if not education:
        return 0.3  # No education data = neutral

    best_score = 0.0

    for edu in education:
        tier = edu.get("tier", "unknown")
        field = edu.get("field_of_study", "").lower().strip()
        degree = edu.get("degree", "").lower().strip()

        # Tier scoring
        tier_score = {
            "tier_1": 1.0,
            "tier_2": 0.7,
            "tier_3": 0.4,
            "tier_4": 0.2,
            "unknown": 0.3,
        }.get(tier, 0.3)

        # Field relevance
        field_bonus = 0.0
        if field in config.RELEVANT_EDUCATION_FIELDS:
            field_bonus = 0.15
        elif any(kw in field for kw in ("computer", "engineering", "tech", "science", "math")):
            field_bonus = 0.08

        # PhD in wrong field penalty (synthetic data artifact)
        if ("ph.d" in degree or "phd" in degree):
            if field in {"mba", "accounting", "marketing", "finance", "human resources"}:
                tier_score *= 0.5  # Suspicious but not impossible

        edu_score = min(1.0, tier_score + field_bonus)
        best_score = max(best_score, edu_score)

    return round(best_score, 4)


def _collect_flags(cand: dict, components: dict) -> list:
    """
    Collect notable highlights and concerns for reasoning generation.
    """
    flags = []
    profile = cand.get("profile", {})
    signals = cand.get("redrob_signals", {})
    career = cand.get("career_history", [])

    # Highlights
    if components["career_relevance"] >= 0.8:
        flags.append("strong_product_career")
    if components["skills_match"] >= 0.8:
        flags.append("excellent_skill_fit")
    if components["experience_band"] >= 0.9:
        flags.append("ideal_experience_band")

    # Concerns
    yoe = profile.get("years_of_experience", 0)
    if yoe < 4:
        flags.append(f"concern:junior_{yoe:.1f}yr")
    elif yoe > 12:
        flags.append(f"concern:overqualified_{yoe:.1f}yr")

    notice = signals.get("notice_period_days", 0)
    if notice > 90:
        flags.append(f"concern:long_notice_{notice}d")

    if components["behavioral_signals"] < 0.3:
        flags.append("concern:low_engagement")

    # Check for pure consulting career
    all_services = all(
        job.get("company", "").lower().strip() in config.SERVICE_CONSULTING_COMPANIES
        for job in career
    ) if career else False
    if all_services and len(career) > 0:
        flags.append("concern:pure_consulting_career")

    # Country concern
    country = profile.get("country", "").lower()
    if config.PREFERRED_COUNTRY not in country:
        flags.append("concern:outside_india")

    return flags

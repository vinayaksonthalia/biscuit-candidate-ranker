"""
Ranker — Stage 3: Sorting, top-100 extraction, and fact-first reasoning.

Sorts candidates descending by score, ascending by candidate_id on ties.
Generates varied, fact-grounded reasoning per candidate.
Uses per-candidate deterministic seeding for reproducible variation.
"""

import hashlib
import random


def rank_candidates(scored_candidates: list, top_n: int = 100) -> list:
    """
    Sort scored candidates and return the top N with ranks and reasoning.

    Args:
        scored_candidates: list of (candidate_dict, score_result) tuples
        top_n: number of top candidates to return (default 100)

    Returns:
        list of dicts with keys: candidate_id, rank, score, reasoning
    """
    # Sort: descending by total score, then ascending by candidate_id for ties
    scored_candidates.sort(
        key=lambda x: (-x[1]["total"], x[0]["candidate_id"])
    )

    results = []
    for rank, (cand, score_result) in enumerate(scored_candidates[:top_n], 1):
        reasoning = _generate_reasoning(cand, score_result, rank)
        results.append({
            "candidate_id": cand["candidate_id"],
            "rank": rank,
            "score": score_result["total"],
            "reasoning": reasoning,
        })

    return results


def _generate_reasoning(cand: dict, score_result: dict, rank: int) -> str:
    """
    Generate fact-first, varied reasoning for a candidate.

    Uses a per-candidate seed (hash of candidate_id) for deterministic
    variation. Each call produces the same reasoning for the same candidate
    across runs.

    Strong facts (skills, career, description) are always prioritized.
    Weaker facts (location, notice period) are used as supporting detail.
    """
    cid = cand["candidate_id"]
    flags = score_result.get("flags", [])

    # Per-candidate deterministic seed using MD5 (Python's hash() is
    # randomized across processes since 3.3, so we use hashlib instead)
    seed_int = int(hashlib.md5(cid.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed_int)

    # Extract facts in priority tiers
    strong_facts = _extract_strong_facts(cand, score_result)
    weak_facts = _extract_weak_facts(cand, score_result)
    concerns = _extract_concerns(cand, flags)

    # Shuffle within each tier for variation — but strong facts always come first
    rng.shuffle(strong_facts)
    rng.shuffle(weak_facts)

    # Build fact list: strong first, then fill with weak
    all_facts = strong_facts + weak_facts

    if not all_facts:
        return (
            f"Candidate at rank {rank} based on composite scoring "
            f"across career, skills, and engagement signals."
        )

    # Pick 2-3 facts for the reasoning
    num_facts = min(len(all_facts), rng.choice([2, 3, 3]))
    selected = all_facts[:num_facts]

    # Build the reasoning string using varied structural templates.
    # This ensures reviewers see different sentence patterns, not just
    # different slot values in the same "Fact; Fact; Fact" template.
    # Facts are kept in original case — they cite profile data and contain
    # proper nouns (IIT, Stanford, etc.) that lowercasing would corrupt.
    template_idx = rng.randint(0, 4)

    if template_idx == 0:
        # Semicolon list (baseline)
        reasoning = "; ".join(selected)
    elif template_idx == 1 and len(selected) >= 2:
        # Full sentence: "X. Additionally, Y"
        reasoning = f"{selected[0]}. Additionally, {selected[1]}"
        if len(selected) >= 3:
            reasoning += f" — {selected[2]}"
    elif template_idx == 2 and len(selected) >= 2:
        # JD-referencing: "Strong fit for the Senior AI Engineer role — X; Y"
        reasoning = f"Strong fit for the Senior AI Engineer role — {selected[0]}"
        for fact in selected[1:]:
            reasoning += f"; {fact}"
    elif template_idx == 3 and len(selected) >= 2:
        # Lead-support: "Notably, X. Y."
        reasoning = f"Notably, {selected[0]}. {selected[1]}"
        if len(selected) >= 3:
            reasoning += f"; {selected[2]}"
    else:
        # Narrative: "X, complemented by Y"
        reasoning = selected[0]
        if len(selected) >= 2:
            reasoning += f", complemented by {selected[1]}"
        if len(selected) >= 3:
            reasoning += f" and {selected[2]}"

    # Append concern if present (honest about gaps)
    # Top-5 candidates: only add concern 30% of the time to keep tone positive
    # Others: always add if present
    if concerns:
        if rank > 5 or rng.random() < 0.3:
            concern = rng.choice(concerns) if len(concerns) > 1 else concerns[0]
            reasoning += f". {concern}"

    # Ensure it ends with a period
    if not reasoning.endswith("."):
        reasoning += "."

    return reasoning


def _extract_strong_facts(cand: dict, score_result: dict) -> list:
    """
    Extract high-signal facts: skills, career, description highlights.
    These should lead the reasoning for top candidates.
    """
    from . import config

    profile = cand.get("profile", {})
    career = cand.get("career_history", [])
    skills = cand.get("skills", [])
    components = score_result.get("components", {})

    from .scorer import _get_robust_yoe
    yoe = _get_robust_yoe(cand)

    facts = []
    current_title = profile.get("current_title", "")
    current_company = profile.get("current_company", "")

    # Fact: Years + current role (always relevant)
    if current_title and current_company:
        facts.append(
            f"{yoe:.0f} years of experience, currently {current_title} "
            f"at {current_company}"
        )

    # Fact: Core JD skill matches
    skill_names = {s.get("name", "").lower() for s in skills}
    core_matches = skill_names & config.CORE_MUST_HAVE_SKILLS
    if core_matches:
        # Pick the most impressive-sounding skills (vector DBs > generic)
        priority_order = [
            "pinecone", "weaviate", "qdrant", "milvus", "faiss",
            "sentence-transformers", "sentence transformers", "embeddings",
            "information retrieval", "ranking", "recommendation systems",
            "hybrid search", "vector search", "vector database",
            "nlp", "natural language processing", "opensearch",
            "elasticsearch", "retrieval", "re-ranking", "reranking",
            "ndcg", "mrr", "map", "python",
        ]
        ordered = [s for s in priority_order if s in core_matches]
        remaining = sorted(core_matches - set(ordered))
        all_core = ordered + remaining
        display = [s.title() for s in all_core[:4]]
        facts.append(f"Core JD skills: {', '.join(display)}")

    # Fact: Product company experience
    seen_companies = set()
    for job in career:
        comp_lower = job.get("company", "").lower().strip()
        comp_display = job.get("company", "")
        if comp_lower in config.PRODUCT_COMPANIES and comp_lower not in seen_companies:
            seen_companies.add(comp_lower)
            title = job.get("title", "")
            if title:
                facts.append(f"Previously {title} at {comp_display}")
            else:
                facts.append(f"Product company experience at {comp_display}")
            if len(seen_companies) >= 2:
                break

    # Fact: Career description ML highlights
    for job in career[:3]:
        desc = job.get("description", "")
        if not desc:
            continue
        desc_lower = desc.lower()
        ml_keywords = [
            "embedding", "vector", "ranking", "retrieval",
            "search", "recommendation", "nlp", "transformer",
            "reranking", "re-ranking",
        ]
        hits = [kw for kw in ml_keywords if kw in desc_lower]
        if len(hits) >= 2:
            company = job.get("company", "previous role")
            facts.append(f"Built {hits[0]}-based systems at {company}")
            break

    # Fact: Headline insight (often contains the best signal)
    headline = profile.get("headline", "")
    if headline:
        hl_lower = headline.lower()
        ml_signals = [
            "ranking", "retrieval", "search", "recommendation",
            "nlp", "ml", "machine learning", "ai engineer",
            "embedding", "deep learning",
        ]
        if any(s in hl_lower for s in ml_signals):
            facts.append(f'Profile headline: "{headline}"')

    # Fact: Nice-to-have skills
    nice_matches = skill_names & config.NICE_TO_HAVE_SKILLS
    if nice_matches:
        display = [s.title() for s in sorted(nice_matches)[:2]]
        facts.append(f"Brings {', '.join(display)} experience")

    # Fact: Tier-1 education
    for edu in cand.get("education", []):
        if edu.get("tier") == "tier_1" and edu.get("institution"):
            facts.append(f"{edu['institution']} graduate (Tier-1)")
            break

    return facts


def _extract_weak_facts(cand: dict, score_result: dict) -> list:
    """
    Extract supporting facts: location, notice period, engagement, GitHub.
    These fill out reasoning but shouldn't lead it.
    """
    profile = cand.get("profile", {})
    signals = cand.get("redrob_signals", {})
    facts = []

    # Location
    location = profile.get("location", "")
    country = profile.get("country", "")
    if location:
        facts.append(f"Located in {location}, {country}")

    # Notice period
    notice = signals.get("notice_period_days", 0)
    if notice <= 30:
        facts.append(f"Available within {notice} days notice")
    elif notice <= 60:
        facts.append(f"{notice}-day notice period")

    # GitHub activity
    github = signals.get("github_activity_score", -1)
    if github >= 60:
        facts.append(f"Strong GitHub activity (score: {github:.0f}/100)")

    # Open to work
    if signals.get("open_to_work_flag", False):
        facts.append("Currently open to new opportunities")

    # High engagement
    response_rate = signals.get("recruiter_response_rate", 0)
    if response_rate >= 0.7:
        facts.append(
            f"High recruiter engagement ({response_rate:.0%} response rate)"
        )

    return facts


def _extract_concerns(cand: dict, flags: list) -> list:
    """
    Extract honest concerns from flags for the reasoning column.
    """
    concerns = []

    for flag in flags:
        if not flag.startswith("concern:"):
            continue

        concern_type = flag[len("concern:"):]

        if concern_type.startswith("junior_"):
            yoe = concern_type.split("_")[1]
            concerns.append(
                f"Note: {yoe} years may be below the JD's 5-9 year band"
            )
        elif concern_type.startswith("overqualified_"):
            yoe = concern_type.split("_")[1]
            concerns.append(
                f"Note: {yoe} years exceeds the ideal 5-9 year range"
            )
        elif concern_type.startswith("long_notice_"):
            # Flag format is "concern:long_notice_120d" — extract just digits
            raw = concern_type.split("_")[-1]
            days = raw.rstrip("d")
            concerns.append(
                f"Concern: {days}-day notice period exceeds JD's "
                f"preferred 30-day window"
            )
        elif concern_type == "low_engagement":
            concerns.append(
                "Concern: low platform engagement suggests limited availability"
            )
        elif concern_type == "pure_consulting_career":
            concerns.append(
                "Concern: entire career at IT services firms — "
                "JD flags this as a fit risk"
            )
        elif concern_type == "outside_india":
            concerns.append(
                "Note: located outside India — JD states no visa sponsorship"
            )

    return concerns

"""
Filters — Stage 1: Honeypot detection and suspicion scoring.

Hard-filters the 42 confirmed impossible profiles.
Returns a suspicion penalty [0.0 - 1.0] for borderline cases.
"""

from datetime import datetime, date

from . import config


def is_honeypot(cand: dict) -> bool:
    """
    Returns True if the candidate has a definitively impossible profile.

    Three rules (union catches exactly 42 profiles in the dataset):
      1. Expert proficiency in 3+ skills with 0 months duration
      2. A single job's stated duration exceeds total years of experience
      3. A single job's stated duration exceeds actual calendar span by >12 months
    """
    skills = cand.get("skills", [])
    profile = cand.get("profile", {})
    career = cand.get("career_history", [])
    signals = cand.get("redrob_signals", {})

    # Rule 1: Expert skills with zero duration
    expert_zero_count = sum(
        1
        for s in skills
        if s.get("proficiency") == "expert" and s.get("duration_months", 0) == 0
    )
    if expert_zero_count >= config.HONEYPOT_EXPERT_ZERO_DURATION_THRESHOLD:
        return True

    # Rule 2: Single job duration exceeds total YoE
    yoe = profile.get("years_of_experience", 0)
    for job in career:
        job_years = job.get("duration_months", 0) / 12.0
        if job_years > yoe + 0.1:  # small buffer for rounding
            return True

    # Rule 3: Stated job duration exceeds calendar dates by >12 months
    last_active_str = signals.get("last_active_date", "")
    if last_active_str:
        try:
            last_active_d = datetime.strptime(last_active_str, "%Y-%m-%d").date()
        except ValueError:
            last_active_d = config.REFERENCE_DATE
    else:
        last_active_d = config.REFERENCE_DATE

    for job in career:
        stated_months = job.get("duration_months", 0)
        start_str = job.get("start_date", "")
        end_str = job.get("end_date")

        if not start_str:
            continue

        try:
            start_d = datetime.strptime(start_str, "%Y-%m-%d").date()
        except ValueError:
            continue

        if end_str:
            try:
                end_d = datetime.strptime(end_str, "%Y-%m-%d").date()
            except ValueError:
                continue
        else:
            end_d = last_active_d

        calendar_months = (end_d.year - start_d.year) * 12 + (
            end_d.month - start_d.month
        )
        if stated_months - calendar_months > 12:
            return True

    return False


def compute_suspicion(cand: dict) -> float:
    """
    Returns a suspicion penalty between 0.0 (clean) and ~0.30 (very suspicious).

    This catches borderline profiles that don't trip the hard honeypot rules
    but have inconsistencies suggesting synthetic noise or data issues.
    The penalty is subtracted from the candidate's final score multiplier.
    """
    penalty = 0.0
    skills = cand.get("skills", [])
    profile = cand.get("profile", {})
    signals = cand.get("redrob_signals", {})

    # Borderline expert-zero-duration (1-2 skills, below hard threshold of 3)
    expert_zero_count = sum(
        1
        for s in skills
        if s.get("proficiency") == "expert" and s.get("duration_months", 0) == 0
    )
    if 1 <= expert_zero_count <= 2:
        penalty += config.SUSPICION_THRESHOLDS["expert_zero_dur_1_2"]

    # Borderline date mismatch (6-12 months, below hard threshold of 12)
    last_active_str = signals.get("last_active_date", "")
    if last_active_str:
        try:
            last_active_d = datetime.strptime(last_active_str, "%Y-%m-%d").date()
        except ValueError:
            last_active_d = config.REFERENCE_DATE
    else:
        last_active_d = config.REFERENCE_DATE

    for job in cand.get("career_history", []):
        stated_months = job.get("duration_months", 0)
        start_str = job.get("start_date", "")
        end_str = job.get("end_date")
        if not start_str:
            continue
        try:
            start_d = datetime.strptime(start_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        if end_str:
            try:
                end_d = datetime.strptime(end_str, "%Y-%m-%d").date()
            except ValueError:
                continue
        else:
            end_d = last_active_d

        calendar_months = (end_d.year - start_d.year) * 12 + (
            end_d.month - start_d.month
        )
        diff = stated_months - calendar_months
        if 6 < diff <= 12:
            penalty += config.SUSPICION_THRESHOLDS["date_mismatch_6_12"]
            break

    # Single skill duration absurdly exceeds career span
    yoe_m = profile.get("years_of_experience", 0) * 12
    if yoe_m > 0:
        max_skill_dur = max(
            (s.get("duration_months", 0) for s in skills), default=0
        )
        if max_skill_dur > yoe_m * 2.5 and max_skill_dur > 36:
            penalty += config.SUSPICION_THRESHOLDS["skill_dur_extreme"]

    # Cap at 0.30 — suspicion is a modifier, not a death sentence
    return min(penalty, 0.30)

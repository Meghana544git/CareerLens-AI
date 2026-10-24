"""
CareerLens AI — Career Tools
Orchestrates all AI-powered career features using watsonx.ai.
"""

import re
import sys
import os
import logging
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from agent_instructions import (
    get_ats_analysis_prompt, get_cover_letter_prompt,
    get_interview_questions_prompt, get_skill_gap_prompt,
    get_career_roadmap_prompt, get_chat_prompt,
    LANGUAGE_CONFIG, INTERNSHIP_FIT_CONFIG,
)
from backend.watsonx_client import get_watsonx_client
from backend.ats_analyzer import calculate_ats_score
from backend.local_generator import (
    analyze_skill_gaps as local_analyze_skill_gaps,
    chat_with_agent as local_chat_with_agent,
    enrich_ats_result,
    generate_career_roadmap as local_generate_career_roadmap,
    generate_cover_letter as local_generate_cover_letter,
    generate_interview_questions as local_generate_interview_questions,
    improve_resume_bullets as local_improve_resume_bullets,
)

logger = logging.getLogger(__name__)


def detect_language(text: str) -> str:
    """
    Detect if text is primarily Hindi or English.
    Returns 'hi' or 'en'.
    """
    if not LANGUAGE_CONFIG.get("auto_detect", True):
        return LANGUAGE_CONFIG.get("default_language", "en")
    # Hindi Unicode range: \u0900-\u097F
    hindi_chars = sum(1 for c in text if "\u0900" <= c <= "\u097F")
    total_chars = len([c for c in text if c.strip()])
    if total_chars > 0 and (hindi_chars / total_chars) > 0.15:
        return "hi"
    return "en"


def analyze_resume_vs_jd(
    resume_text: str, job_description: str, user_name: str = "Applicant"
) -> Dict[str, Any]:
    """Run a deterministic, local ATS comparison without an AI/API call."""
    if not str(resume_text or "").strip():
        return {"ats_score": 0, "error": "Please upload or paste your resume first."}
    if not str(job_description or "").strip():
        return {"ats_score": 0, "error": "Job description is required."}
    result = calculate_ats_score(resume_text, job_description)
    return enrich_ats_result(resume_text, job_description, result)

def generate_cover_letter(
    resume_text: str, job_description: str, user_name: str = "Applicant"
) -> Dict[str, Any]:
    """Create a cover letter using local templates and supplied text only."""
    return local_generate_cover_letter(resume_text, job_description, user_name)

def generate_interview_questions(
    job_description: str, resume_text: str = ""
) -> Dict[str, Any]:
    """Create role-specific interview practice questions without AI."""
    return local_generate_interview_questions(job_description, resume_text)

def analyze_skill_gaps(resume_text: str, job_description: str) -> Dict[str, Any]:
    """Compare detected resume skills to job requirements using local rules."""
    return local_analyze_skill_gaps(resume_text, job_description)

def generate_career_roadmap(resume_text: str, target_role: str) -> Dict[str, Any]:
    """Create an editable 12-week roadmap using role-specific skill profiles."""
    return local_generate_career_roadmap(resume_text, target_role)

def analyze_internship_fit(resume_text: str, internship_description: str) -> Dict[str, Any]:
    """
    Specialized internship fit analysis for students/freshers.
    Applies the fresher-friendly scoring from agent_instructions.
    """
    cfg = INTERNSHIP_FIT_CONFIG

    from backend.ats_analyzer import _extract_tech_skills, _extract_keywords
    from backend.resume_parser import extract_skills_from_text

    resume_lower = resume_text.lower()
    jd_lower = internship_description.lower()

    # Compute sub-scores weighted for freshers
    jd_skills = _extract_tech_skills(jd_lower)
    resume_skills = _extract_tech_skills(resume_lower)
    jd_keywords = _extract_keywords(internship_description)

    skill_match_pct = len(jd_skills & resume_skills) / max(len(jd_skills), 1)
    keyword_match_pct = sum(1 for k in jd_keywords if k in resume_lower) / max(len(jd_keywords), 1)

    has_projects = bool(re.search(r"\b(project|built|developed|created)\b", resume_lower))
    has_prior_intern = bool(re.search(r"\bintern(ship)?\b", resume_lower))
    has_certs = bool(re.search(r"\b(certificate|certification|certified|course)\b", resume_lower))

    score = round(
        skill_match_pct * 100 * cfg["skills_weight"] +
        keyword_match_pct * 100 * 0.30 +
        (30 if has_projects else 0) * cfg["projects_weight"] +
        (30 if has_prior_intern else 0) * cfg["experience_weight"] +
        (20 if has_certs else 0) * cfg["certifications_weight"]
    )

    # Fresher bonus
    if "fresher" in resume_lower or "final year" in resume_lower or "student" in resume_lower:
        score += cfg.get("fresher_bonus", 5)

    score = min(100, score)
    should_apply = score >= cfg["min_score_to_apply"]

    matched_skills = list(jd_skills & resume_skills)
    missing_skills = list(jd_skills - resume_skills)

    return {
        "internship_fit_score": score,
        "should_apply": should_apply,
        "matched_skills": matched_skills[:10],
        "missing_skills": missing_skills[:10],
        "has_projects": has_projects,
        "has_prior_internship": has_prior_intern,
        "has_certifications": has_certs,
        "recommendation": (
            "Great fit! Polish your resume and apply now." if score >= 70
            else "Good base — add 1-2 quick projects and apply." if score >= cfg["min_score_to_apply"]
            else "Build 1-2 projects for this stack before applying."
        ),
        "platforms": cfg["top_internship_platforms"],
    }


def chat_with_agent(
    user_message: str, session_context: str = "", resume_text: str = ""
) -> Dict[str, Any]:
    """Return practical career guidance locally, without a model/API call."""
    return local_chat_with_agent(user_message, session_context, resume_text)

def improve_resume_bullets(resume_text: str, job_description: str = "") -> Dict[str, Any]:
    """Improve wording while preserving supplied facts and avoiding invented metrics."""
    return local_improve_resume_bullets(resume_text, job_description)


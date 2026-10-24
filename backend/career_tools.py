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
    """Use watsonx when configured; otherwise return reliable local analysis."""
    if not str(resume_text or "").strip():
        return {"ats_score": 0, "error": "Please upload or paste your resume first."}
    if not str(job_description or "").strip():
        return {"ats_score": 0, "error": "Job description is required."}
    client = get_watsonx_client()
    language = detect_language(resume_text + job_description)
    if client.is_configured():
        try:
            prompt = get_ats_analysis_prompt(resume_text, job_description, language)
            ai_result = client.generate_json(prompt, max_new_tokens=2048)
            result = calculate_ats_score(resume_text, job_description, ai_result)
            result["language"] = language
            return enrich_ats_result(resume_text, job_description, result)
        except Exception:
            logger.exception("watsonx ATS analysis failed; using local fallback")
    result = calculate_ats_score(resume_text, job_description)
    return enrich_ats_result(resume_text, job_description, result)

def generate_cover_letter(
    resume_text: str, job_description: str, user_name: str = "Applicant"
) -> Dict[str, Any]:
    """Generate a tailored letter with Granite, falling back to local templates."""
    client = get_watsonx_client()
    language = detect_language(resume_text + " " + job_description)
    if client.is_configured():
        try:
            prompt = get_cover_letter_prompt(resume_text, job_description, user_name, language)
            letter = client.generate(prompt, max_new_tokens=800, temperature=0.5)
            if letter.strip():
                return {"cover_letter": letter, "word_count": len(letter.split()), "language": language}
        except Exception:
            logger.exception("watsonx cover-letter generation failed; using local fallback")
    return local_generate_cover_letter(resume_text, job_description, user_name)

def generate_interview_questions(
    job_description: str, resume_text: str = ""
) -> Dict[str, Any]:
    """Create interview preparation with Granite when configured."""
    client = get_watsonx_client()
    language = detect_language(job_description + " " + resume_text)
    if client.is_configured():
        try:
            prompt = get_interview_questions_prompt(job_description, resume_text, language)
            result = client.generate_json(prompt, max_new_tokens=2048)
            return {
                "behavioral_questions": result.get("behavioral_questions", []),
                "technical_questions": result.get("technical_questions", []),
                "situational_questions": result.get("situational_questions", []),
                "questions_to_ask_interviewer": result.get("questions_to_ask_interviewer", []),
                "preparation_checklist": result.get("preparation_checklist", []),
                "language": language,
            }
        except Exception:
            logger.exception("watsonx interview generation failed; using local fallback")
    return local_generate_interview_questions(job_description, resume_text)

def analyze_skill_gaps(resume_text: str, job_description: str) -> Dict[str, Any]:
    """Use Granite for skill-gap analysis when credentials are configured."""
    client = get_watsonx_client()
    language = detect_language(resume_text + " " + job_description)
    if client.is_configured():
        try:
            prompt = get_skill_gap_prompt(resume_text, job_description, language)
            result = client.generate_json(prompt, max_new_tokens=2048)
            local = local_analyze_skill_gaps(resume_text, job_description)
            for key in ("critical_gaps", "nice_to_have_gaps", "learning_roadmap", "quick_wins", "career_advice"):
                if key in result and result[key]:
                    local[key] = result[key]
            local["language"] = language
            local["generation_mode"] = "ibm_watsonx"
            return local
        except Exception:
            logger.exception("watsonx skill-gap analysis failed; using local fallback")
    return local_analyze_skill_gaps(resume_text, job_description)

def generate_career_roadmap(resume_text: str, target_role: str) -> Dict[str, Any]:
    """Generate a personalized roadmap with Granite when credentials are configured."""
    client = get_watsonx_client()
    language = detect_language(resume_text)
    if client.is_configured():
        try:
            prompt = get_career_roadmap_prompt(resume_text, target_role, language)
            result = client.generate_json(prompt, max_new_tokens=2048)
            fallback = local_generate_career_roadmap(resume_text, target_role)
            for key in ("current_level", "target_level", "estimated_timeline", "roadmap_phases",
                        "internship_opportunities", "networking_strategy", "salary_range", "motivational_note"):
                if key in result and result[key]:
                    fallback[key] = result[key]
            fallback["language"] = language
            fallback["generation_mode"] = "ibm_watsonx"
            return fallback
        except Exception:
            logger.exception("watsonx roadmap generation failed; using local fallback")
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
    """Use Granite for chat when configured; otherwise provide local guidance."""
    client = get_watsonx_client()
    language = detect_language(user_message)
    if client.is_configured():
        try:
            context_parts = []
            if session_context:
                context_parts.append(session_context)
            if resume_text:
                context_parts.append("User resume summary (first 500 chars): " + resume_text[:500])
            prompt = get_chat_prompt(user_message, " | ".join(context_parts), language)
            return {"response": client.generate(prompt, max_new_tokens=1024, temperature=0.4), "language": language, "generation_mode": "ibm_watsonx"}
        except Exception:
            logger.exception("watsonx chat failed; using local fallback")
    return local_chat_with_agent(user_message, session_context, resume_text)

def improve_resume_bullets(resume_text: str, job_description: str = "") -> Dict[str, Any]:
    """Improve bullets with Granite when configured, preserving a local fallback."""
    client = get_watsonx_client()
    if client.is_configured():
        try:
            prompt = f"""You are CareerLens AI, an expert resume coach.
Rewrite the supplied resume bullets using strong action verbs. Preserve facts and do not invent metrics.
Resume:
{resume_text}
Job description context:
{job_description[:500] if job_description else "Not supplied"}
Return only valid JSON with improved_bullets (original, improved, improvement_reason), general_tips, and professional_english_phrases.
"""
            result = client.generate_json(prompt, max_new_tokens=1500)
            if result.get("improved_bullets"):
                return {
                    "improved_bullets": result.get("improved_bullets", []),
                    "general_tips": result.get("general_tips", []),
                    "professional_english_phrases": result.get("professional_english_phrases", {}),
                    "generation_mode": "ibm_watsonx",
                }
        except Exception:
            logger.exception("watsonx resume rewrite failed; using local fallback")
    return local_improve_resume_bullets(resume_text, job_description)


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
    """
    Full ATS analysis: AI analysis + rule-based scoring blended together.
    Returns comprehensive match report.
    """
    client = get_watsonx_client()
    language = detect_language(resume_text + job_description)

    prompt = get_ats_analysis_prompt(resume_text, job_description, language)
    ai_result = client.generate_json(prompt, max_new_tokens=2048)

    # Blend AI result with rule-based scoring
    final = calculate_ats_score(resume_text, job_description, ai_result)
    final["language"] = language
    return final


def generate_cover_letter(
    resume_text: str, job_description: str, user_name: str = "Applicant"
) -> Dict[str, Any]:
    """Generate a tailored cover letter."""
    client = get_watsonx_client()
    language = detect_language(resume_text)

    prompt = get_cover_letter_prompt(resume_text, job_description, user_name, language)
    cover_letter = client.generate(prompt, max_new_tokens=800, temperature=0.5)

    return {
        "cover_letter": cover_letter,
        "word_count": len(cover_letter.split()),
        "language": language,
    }


def generate_interview_questions(
    job_description: str, resume_text: str = ""
) -> Dict[str, Any]:
    """Generate predicted interview questions with preparation guidance."""
    client = get_watsonx_client()
    language = detect_language(job_description)

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


def analyze_skill_gaps(resume_text: str, job_description: str) -> Dict[str, Any]:
    """Identify skill gaps and generate a learning roadmap with resources."""
    client = get_watsonx_client()
    language = detect_language(resume_text)

    prompt = get_skill_gap_prompt(resume_text, job_description, language)
    result = client.generate_json(prompt, max_new_tokens=2048)

    return {
        "critical_gaps": result.get("critical_gaps", []),
        "nice_to_have_gaps": result.get("nice_to_have_gaps", []),
        "learning_roadmap": result.get("learning_roadmap", []),
        "quick_wins": result.get("quick_wins", []),
        "career_advice": result.get("career_advice", ""),
        "language": language,
    }


def generate_career_roadmap(resume_text: str, target_role: str) -> Dict[str, Any]:
    """Generate a personalized career roadmap toward a target role."""
    client = get_watsonx_client()
    language = detect_language(resume_text)

    prompt = get_career_roadmap_prompt(resume_text, target_role, language)
    result = client.generate_json(prompt, max_new_tokens=2048)

    return {
        "current_level": result.get("current_level", ""),
        "target_level": result.get("target_level", ""),
        "estimated_timeline": result.get("estimated_timeline", ""),
        "roadmap_phases": result.get("roadmap_phases", []),
        "internship_opportunities": result.get("internship_opportunities", []),
        "networking_strategy": result.get("networking_strategy", []),
        "salary_range": result.get("salary_range", {}),
        "motivational_note": result.get("motivational_note", ""),
        "language": language,
    }


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
    """
    Main conversational AI endpoint.
    Handles open-ended career coaching questions.
    """
    client = get_watsonx_client()
    language = detect_language(user_message)

    context_parts = []
    if session_context:
        context_parts.append(session_context)
    if resume_text:
        # Include a brief resume summary for context
        context_parts.append(f"User resume summary (first 500 chars): {resume_text[:500]}")

    context = " | ".join(context_parts)

    prompt = get_chat_prompt(user_message, context, language)
    response = client.generate(prompt, max_new_tokens=1024, temperature=0.4)

    return {
        "response": response,
        "language": language,
    }


def improve_resume_bullets(resume_text: str, job_description: str = "") -> Dict[str, Any]:
    """
    Specifically generate improved bullet point rewrites for the resume.
    """
    client = get_watsonx_client()

    prompt = f"""You are CareerLens AI, an expert resume coach.

Analyze this resume and rewrite weak bullet points using the STAR method and strong action verbs.
Focus on quantification, impact, and relevance.

RESUME:
{resume_text}

{"JOB DESCRIPTION CONTEXT: " + job_description[:500] if job_description else ""}

Return JSON:
{{
  "improved_bullets": [
    {{
      "original": "<original bullet or phrase>",
      "improved": "<rewritten bullet with metrics and action verb>",
      "improvement_reason": "<why this is better>"
    }}
  ],
  "general_tips": ["<tip 1>", "<tip 2>", "<tip 3>"],
  "professional_english_phrases": {{
    "instead_of": "<weak phrase>",
    "use": "<strong professional phrase>"
  }}
}}
Return ONLY valid JSON."""

    result = client.generate_json(prompt, max_new_tokens=1500)

    return {
        "improved_bullets": result.get("improved_bullets", []),
        "general_tips": result.get("general_tips", []),
        "professional_english_phrases": result.get("professional_english_phrases", {}),
    }



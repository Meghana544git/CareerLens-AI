"""
CareerLens AI — ATS Scoring & Analysis Engine
Computes multi-dimensional ATS scores using keyword matching + AI analysis.
"""

import re
import sys
import os
import logging
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from agent_instructions import (
    ATS_SCORING_WEIGHTS, ATS_SCORE_THRESHOLDS, ATS_BONUS_RULES
)

logger = logging.getLogger(__name__)

# Strong action verbs that improve resume quality score
ACTION_VERBS = {
    "developed", "built", "designed", "led", "managed", "created", "implemented",
    "optimized", "improved", "reduced", "increased", "launched", "delivered",
    "architected", "engineered", "deployed", "automated", "scaled", "trained",
    "mentored", "collaborated", "analyzed", "researched", "published", "presented",
    "achieved", "awarded", "established", "transformed", "streamlined", "accelerated",
}


def calculate_ats_score(
    resume_text: str,
    job_description: str,
    ai_result: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Calculate a comprehensive ATS score using both rule-based and AI analysis.
    If ai_result is provided, blends AI scores with rule-based scores.
    """
    if not resume_text or not job_description:
        return {"ats_score": 0, "error": "Missing resume or job description"}

    # Rule-based sub-scores
    rule_scores = _calculate_rule_based_scores(resume_text, job_description)

    # If we have AI analysis, blend it (AI scores carry 60%, rules 40%)
    if ai_result and isinstance(ai_result, dict) and "score_breakdown" in ai_result:
        ai_breakdown = ai_result.get("score_breakdown", {})
        blended = {}
        for key in ["keyword_match", "skills_coverage", "experience_relevance",
                    "education_match", "resume_quality"]:
            ai_val = ai_breakdown.get(key, rule_scores.get(key, 50))
            rule_val = rule_scores.get(key, 50)
            blended[key] = round(ai_val * 0.6 + rule_val * 0.4)

        final_score = _compute_weighted_score(blended)
        # Apply bonus points
        bonus = _calculate_bonus(resume_text, job_description)
        final_score = min(100, final_score + bonus)

        return {
            "ats_score": final_score,
            "score_breakdown": blended,
            "bonus_points": bonus,
            "matched_skills": ai_result.get("matched_skills", []),
            "missing_keywords": ai_result.get("missing_keywords", []),
            "weak_skills": ai_result.get("weak_skills", []),
            "role_fit_summary": ai_result.get("role_fit_summary", ""),
            "top_strengths": ai_result.get("top_strengths", []),
            "improvement_actions": ai_result.get("improvement_actions", []),
            "resume_bullet_rewrites": ai_result.get("resume_bullet_rewrites", []),
            "overall_verdict": _get_verdict(final_score),
            "score_label": _get_score_label(final_score),
            "score_color": _get_score_color(final_score),
        }

    # Pure rule-based fallback
    rule_score = _compute_weighted_score(rule_scores)
    bonus = _calculate_bonus(resume_text, job_description)
    final_score = min(100, rule_score + bonus)

    keywords_from_jd = _extract_keywords(job_description)
    resume_lower = resume_text.lower()
    matched = [kw for kw in keywords_from_jd if kw.lower() in resume_lower]
    missing = [kw for kw in keywords_from_jd if kw.lower() not in resume_lower]

    return {
        "ats_score": final_score,
        "score_breakdown": rule_scores,
        "bonus_points": bonus,
        "matched_skills": matched[:15],
        "missing_keywords": missing[:15],
        "weak_skills": [],
        "role_fit_summary": f"Rule-based analysis complete. {len(matched)} of {len(keywords_from_jd)} keywords matched.",
        "top_strengths": [],
        "improvement_actions": [],
        "resume_bullet_rewrites": [],
        "overall_verdict": _get_verdict(final_score),
        "score_label": _get_score_label(final_score),
        "score_color": _get_score_color(final_score),
    }


def _calculate_rule_based_scores(resume: str, jd: str) -> Dict[str, int]:
    """Compute sub-scores purely from text analysis."""
    resume_lower = resume.lower()
    jd_lower = jd.lower()

    # 1. Keyword Match Score
    jd_keywords = _extract_keywords(jd)
    if jd_keywords:
        matches = sum(1 for kw in jd_keywords if kw.lower() in resume_lower)
        keyword_score = round((matches / len(jd_keywords)) * 100)
    else:
        keyword_score = 50

    # 2. Skills Coverage
    tech_skills_in_jd = _extract_tech_skills(jd_lower)
    tech_skills_in_resume = _extract_tech_skills(resume_lower)
    if tech_skills_in_jd:
        skill_overlap = len(tech_skills_in_jd & tech_skills_in_resume)
        skills_score = round((skill_overlap / len(tech_skills_in_jd)) * 100)
    else:
        skills_score = 60

    # 3. Experience Relevance (heuristic — count years, domain terms)
    exp_score = _score_experience(resume_lower, jd_lower)

    # 4. Education Match
    edu_score = _score_education(resume_lower, jd_lower)

    # 5. Resume Quality
    quality_score = _score_resume_quality(resume)

    return {
        "keyword_match": min(100, keyword_score),
        "skills_coverage": min(100, skills_score),
        "experience_relevance": exp_score,
        "education_match": edu_score,
        "resume_quality": quality_score,
    }


def _compute_weighted_score(breakdown: Dict[str, int]) -> int:
    """Apply weights from agent_instructions to compute final score."""
    weights = ATS_SCORING_WEIGHTS
    total = (
        breakdown.get("keyword_match", 50) * weights["keyword_match"] +
        breakdown.get("skills_coverage", 50) * weights["skills_coverage"] +
        breakdown.get("experience_relevance", 50) * weights["experience_relevance"] +
        breakdown.get("education_match", 50) * weights["education_match"] +
        breakdown.get("resume_quality", 50) * weights["resume_quality"]
    )
    return round(total)


def _calculate_bonus(resume: str, jd: str) -> int:
    """Calculate bonus points based on strong signals."""
    bonus = 0
    resume_lower = resume.lower()

    # Quantified achievements (numbers in context of impact)
    if re.search(r"\b\d+[\.\d]*\s*%", resume):
        bonus += ATS_BONUS_RULES["quantified_achievements"]

    # Action verbs
    words = set(resume_lower.split())
    if len(words & ACTION_VERBS) >= 5:
        bonus += ATS_BONUS_RULES["action_verbs_used"]

    # GitHub/LinkedIn
    if "github.com" in resume_lower or "linkedin.com" in resume_lower:
        bonus += ATS_BONUS_RULES["github_linkedin_present"]

    return bonus


def _extract_keywords(text: str) -> List[str]:
    """Extract important keywords from text (removes stopwords)."""
    STOPWORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
        "for", "of", "with", "by", "from", "is", "are", "was", "were",
        "be", "been", "being", "have", "has", "had", "do", "does", "did",
        "will", "would", "could", "should", "may", "might", "must", "can",
        "we", "you", "our", "your", "their", "this", "that", "these", "those",
        "not", "no", "so", "as", "if", "then", "than", "into", "about",
        "up", "out", "it", "its", "also", "more", "very", "just", "well",
        "team", "work", "role", "position", "job", "company", "candidates",
        "experience", "ability", "strong", "good", "great", "excellent",
        "required", "preferred", "bonus", "plus", "including", "such",
    }
    # Tokenize and filter
    words = re.findall(r"\b[a-zA-Z][a-zA-Z+#./]{2,}\b", text.lower())
    keywords = [w for w in words if w not in STOPWORDS]
    # Count frequency and return top keywords
    freq = {}
    for w in keywords:
        freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: -x[1])[:50]]


def _extract_tech_skills(text: str) -> set:
    """Extract technology/skill terms from text."""
    TECH_TERMS = {
        "python", "java", "javascript", "typescript", "c++", "c#", "golang",
        "react", "angular", "vue", "node", "django", "flask", "fastapi",
        "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "git", "github", "ci/cd", "jenkins", "linux",
        "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
        "spark", "hadoop", "kafka", "airflow",
        "tableau", "power bi", "excel",
        "agile", "scrum", "jira", "figma",
        "machine learning", "deep learning", "nlp", "api", "rest",
        "html", "css", "bootstrap", "tailwind",
    }
    found = set()
    for term in TECH_TERMS:
        if re.search(r"\b" + re.escape(term) + r"\b", text):
            found.add(term)
    return found


def _score_experience(resume: str, jd: str) -> int:
    """Score experience relevance heuristically."""
    score = 50  # Default

    # Check if JD requires years and resume has years
    jd_years_match = re.search(r"(\d+)\+?\s*years?", jd)
    resume_years_mentions = re.findall(r"\b(20\d{2})\b", resume)

    if jd_years_match and resume_years_mentions:
        required_years = int(jd_years_match.group(1))
        # Approximate years from dates in resume
        years = [int(y) for y in resume_years_mentions]
        if years:
            span = max(years) - min(years)
            if span >= required_years:
                score = 80
            elif span >= required_years * 0.7:
                score = 65
            else:
                score = 40

    # Boost if "intern" or "fresher" appears
    if "intern" in resume or "fresher" in resume or "student" in jd:
        score = max(score, 60)  # Freshers should still get decent score

    return min(100, score)


def _score_education(resume: str, jd: str) -> int:
    """Score education alignment."""
    score = 60  # Default

    # Degree levels
    phd_keywords = ["phd", "ph.d", "doctorate", "doctoral"]
    masters_keywords = ["master", "m.s.", "m.e.", "m.tech", "mba", "m.sc"]
    bachelors_keywords = ["bachelor", "b.s.", "b.e.", "b.tech", "b.sc", "b.com", "undergraduate", "ug"]

    jd_wants_phd = any(k in jd for k in phd_keywords)
    jd_wants_masters = any(k in jd for k in masters_keywords)
    jd_wants_bachelors = any(k in jd for k in bachelors_keywords)

    has_phd = any(k in resume for k in phd_keywords)
    has_masters = any(k in resume for k in masters_keywords)
    has_bachelors = any(k in resume for k in bachelors_keywords)

    if jd_wants_phd:
        score = 90 if has_phd else (70 if has_masters else 50)
    elif jd_wants_masters:
        score = 90 if (has_phd or has_masters) else (75 if has_bachelors else 50)
    elif jd_wants_bachelors:
        score = 90 if (has_phd or has_masters or has_bachelors) else 55

    # Relevant field bonus
    cs_fields = ["computer science", "software", "data science", "information technology",
                 "electronics", "electrical", "statistics", "mathematics"]
    if any(f in resume for f in cs_fields) and any(f in jd for f in cs_fields):
        score = min(100, score + 10)

    return score


def _score_resume_quality(resume: str) -> int:
    """Score the structural quality of the resume."""
    score = 40
    resume_lower = resume.lower()
    word_count = len(resume.split())

    # Appropriate length
    if 300 <= word_count <= 900:
        score += 15
    elif 200 <= word_count < 300 or 900 < word_count <= 1200:
        score += 8

    # Has standard sections
    sections_found = 0
    for section in ["experience", "education", "skills", "projects", "summary"]:
        if section in resume_lower:
            sections_found += 1
    score += sections_found * 5

    # Action verbs
    words = set(resume_lower.split())
    action_verb_count = len(words & ACTION_VERBS)
    if action_verb_count >= 8:
        score += 10
    elif action_verb_count >= 4:
        score += 5

    # Quantified achievements
    if re.search(r"\b\d+[\.\d]*\s*%", resume):
        score += 10
    if re.search(r"\$[\d,]+|\d+\s*(million|thousand|users|clients)", resume, re.IGNORECASE):
        score += 5

    # Professional links
    if "linkedin" in resume_lower or "github" in resume_lower:
        score += 5

    return min(100, score)


def _get_verdict(score: int) -> str:
    for label, (low, high, verdict) in ATS_SCORE_THRESHOLDS.items():
        if low <= score <= high:
            return verdict
    return "Analysis Complete"


def _get_score_label(score: int) -> str:
    for label, (low, high, verdict) in ATS_SCORE_THRESHOLDS.items():
        if low <= score <= high:
            return label.capitalize()
    return "Unknown"


def _get_score_color(score: int) -> str:
    if score >= 85: return "#22c55e"   # green
    if score >= 70: return "#3b82f6"   # blue
    if score >= 50: return "#eab308"   # yellow
    if score >= 30: return "#f97316"   # orange
    return "#ef4444"                    # red


def compare_jobs(resume_text: str, job_list: List[Dict]) -> List[Dict]:
    """
    Compare a resume against multiple job descriptions.
    Returns sorted list with scores.
    """
    results = []
    for job in job_list:
        jd = job.get("description", "")
        if not jd:
            continue
        score_data = calculate_ats_score(resume_text, jd)
        results.append({
            "job_title": job.get("title", "Unknown Role"),
            "company": job.get("company", ""),
            "ats_score": score_data["ats_score"],
            "score_label": score_data["score_label"],
            "score_color": score_data["score_color"],
            "matched_skills": score_data["matched_skills"][:5],
            "missing_keywords": score_data["missing_keywords"][:5],
            "verdict": score_data["overall_verdict"],
        })
    # Sort by score descending
    return sorted(results, key=lambda x: x["ats_score"], reverse=True)

#!/usr/bin/env python3
"""Deterministic no-AI generator regression tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.local_generator import (
    analyze_skill_gaps,
    enrich_ats_result,
    extract_skills,
    generate_career_roadmap,
    generate_cover_letter,
    generate_interview_questions,
    improve_resume_bullets,
    chat_with_agent,
)
from backend.ats_analyzer import calculate_ats_score

RESUME = """Student developer
B.Tech Artificial Intelligence and Machine Learning
Skills: Python, Java, SQL, Git, Pandas
Projects: Built a Python text classification project and a small REST API.
"""
JOB = """Software Engineering Intern
Required skills: Python, Java, SQL, REST APIs, Git, testing and problem solving.
Build maintainable features and collaborate with engineers.
"""

def main():
    letter = generate_cover_letter(RESUME, JOB, "Meghana")
    assert "Meghana" in letter["cover_letter"]
    assert "Software Engineer" in letter["cover_letter"]
    assert letter["word_count"] > 50
    assert "94%" not in letter["cover_letter"], "must not invent achievements"

    gaps = analyze_skill_gaps("", "Machine Learning Engineer role: Python, SQL, PyTorch and Git.")
    assert gaps["critical_gaps"], "must produce gaps without a resume"
    assert gaps["learning_roadmap"], "must produce a roadmap"
    gap_names = [item["skill"] for item in gaps["critical_gaps"]]
    assert "Python" in gap_names and "PyTorch" in gap_names

    roadmap = generate_career_roadmap(RESUME, "Machine Learning Engineer")
    assert "Machine Learning Engineer" in roadmap["target_level"]
    assert roadmap["roadmap_phases"] and len(roadmap["roadmap_phases"]) == 3
    assert roadmap["estimated_timeline"]

    interview = generate_interview_questions(JOB, RESUME)
    assert interview["technical_questions"]
    assert any("Python" in item["question"] for item in interview["technical_questions"])
    assert interview["behavioral_questions"]

    improved = improve_resume_bullets("Worked on a Python project.\nHelped test a REST API.")
    assert improved["improved_bullets"]
    assert all(item["improved"] for item in improved["improved_bullets"])

    ats = enrich_ats_result(RESUME, JOB, calculate_ats_score(RESUME, JOB))
    assert isinstance(ats["ats_score"], int)
    assert "Python" in ats["matched_skills"]

    chat = chat_with_agent("How should I prepare for an interview?", resume_text=RESUME)
    assert len(chat["response"]) > 30
    assert "Python" in chat["response"]

    assert "Python" in extract_skills(RESUME)
    print("PASS deterministic cover letter, skill gaps, roadmap, interview, resume rewrite, ATS and chat")

if __name__ == "__main__":
    main()

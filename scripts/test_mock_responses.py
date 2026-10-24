#!/usr/bin/env python3
"""Unit checks for CareerLens mock-mode AI responses."""

import json
import sys
from pathlib import Path

# Make the repository root importable when this script is invoked by file path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.watsonx_client import WatsonxClient


def check_json(prompt: str, expected_key: str) -> None:
    raw = WatsonxClient._mock_response(prompt, expect_json=True)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Mock response was not JSON for {expected_key}") from exc
    assert data.get(expected_key), f"Mock response missing {expected_key}"


def main() -> None:
    check_json("score_breakdown ATS resume analysis", "ats_score")
    cover = WatsonxClient._mock_response("Generate a cover letter", expect_json=False)
    assert "Dear Hiring Manager" in cover

    check_json("interview behavioral_questions technical questions", "behavioral_questions")
    check_json("skill_gap learning_roadmap", "critical_gaps")
    check_json("career roadmap roadmap_phases", "roadmap_phases")
    check_json("rewrite weak bullet points improved_bullets", "improved_bullets")

    chat = WatsonxClient._mock_response("career coach general question", expect_json=False)
    assert "CareerLens AI" in chat
    print("PASS mock responses for ATS, cover letter, interview, skill gaps, roadmap, resume rewriting, and chat")


if __name__ == "__main__":
    main()

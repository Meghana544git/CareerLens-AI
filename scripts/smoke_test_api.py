#!/usr/bin/env python3
"""Live smoke tests for the deployed CareerLens Flask API.

These tests run before a new Flutter web bundle is published. They use a
temporary HTTP session, test representative features, and clean up their own
saved job/chat records when the API supports it.
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

BASE_URL = os.environ.get(
    "CAREERLENS_API_BASE_URL",
    "https://career-lens-ai-gilt.vercel.app",
).rstrip("/")
TIMEOUT_SECONDS = 75
ORIGIN = "https://careerlens-ai-flutter-web.vercel.app"

cookies = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))


def request(path: str, method: str = "GET", payload=None, headers=None, data=None):
    request_headers = {"Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    body = data
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        BASE_URL + path,
        data=body,
        headers=request_headers,
        method=method,
    )
    try:
        with opener.open(req, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read()
            decoded = raw.decode("utf-8", errors="replace")
            return response.status, response.headers, decoded
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise AssertionError(
            f"{method} {path} returned HTTP {exc.code}: {details[:500]}"
        ) from exc
    except Exception as exc:
        raise AssertionError(
            f"{method} {path} failed to respond within {TIMEOUT_SECONDS}s: {exc}"
        ) from exc


def json_request(path: str, method: str = "GET", payload=None):
    status, headers, raw = request(path, method, payload=payload)
    assert status == 200, f"{method} {path}: expected HTTP 200, got {status}"
    try:
        body = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"{method} {path}: response wasn't JSON") from exc
    assert isinstance(body, dict), f"{method} {path}: response should be an object"
    assert body.get("success") is True, (
        f"{method} {path}: API did not report success: {str(body)[:400]}"
    )
    assert "data" in body, f"{method} {path}: response is missing data"
    return body["data"]


def check(name, fn):
    started = time.monotonic()
    fn()
    elapsed = time.monotonic() - started
    print(f"PASS {name} ({elapsed:.1f}s)", flush=True)


RESUME = """Meghana Yara
Computer Science undergraduate specialising in AI and Machine Learning.
Skills: Python, Java, SQL, machine learning, data analysis, Git and REST APIs.
Projects: Built a text classification model, developed a resume analysis tool,
and created a small Python web application. Education: B.Tech Artificial
Intelligence and Machine Learning. Experience: Student developer.
"""

JOB = """Software Engineering Intern. Work with Python, Java, SQL, APIs,
Git, testing, problem solving and machine learning. Build maintainable software,
collaborate with engineering teams, write automated tests, review code and
document technical decisions. Applicants should be students who are eager
to learn, communicate clearly and deliver reliable software features."""


def test_health():
    status, headers, raw = request("/health")
    assert status == 200, f"GET /health returned HTTP {status}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssertionError("GET /health did not return JSON") from exc
    assert data.get("status") == "healthy", f"service health isn't healthy: {data}"


def test_cors():
    status, headers, raw = request(
        "/api/roadmap/generate",
        method="OPTIONS",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert status in (200, 204), f"CORS preflight returned HTTP {status}"
    allowed_origin = headers.get("Access-Control-Allow-Origin", "")
    assert allowed_origin in (ORIGIN, "*"), (
        f"CORS did not allow the Flutter web origin ({allowed_origin!r})"
    )
    allowed_methods = headers.get("Access-Control-Allow-Methods", "")
    assert "POST" in allowed_methods.upper(), (
        f"CORS does not allow POST ({allowed_methods!r})"
    )


def test_cover_letter():
    data = json_request(
        "/api/cover-letter/generate",
        "POST",
        {"user_name": "CareerLens Smoke Test", "resume_text": RESUME, "job_description": JOB},
    )
    assert isinstance(data, dict) and len(data.get("cover_letter", "").strip()) > 80, (
        "cover-letter endpoint returned no readable letter"
    )


def test_interview():
    data = json_request(
        "/api/interview/questions",
        "POST",
        {"resume_text": RESUME, "job_description": JOB},
    )
    assert isinstance(data, dict) and (
        data.get("behavioral_questions") or data.get("technical_questions")
    ), "interview endpoint returned no questions"


def test_skill_gaps():
    data = json_request(
        "/api/skills/gap",
        "POST",
        {"resume_text": RESUME, "job_description": JOB},
    )
    assert isinstance(data, dict) and (
        "critical_gaps" in data or "learning_roadmap" in data
    ), "skill-gap endpoint returned an unexpected result"


def test_roadmap():
    data = json_request(
        "/api/roadmap/generate",
        "POST",
        {"target_role": "Machine Learning Engineer", "resume_text": RESUME},
    )
    assert isinstance(data, dict) and (
        data.get("roadmap_phases") or data.get("estimated_timeline")
    ), "roadmap endpoint returned no roadmap"


def test_internship_fit():
    data = json_request(
        "/api/internship/fit",
        "POST",
        {"resume_text": RESUME, "internship_description": JOB},
    )
    assert isinstance(data, dict) and "internship_fit_score" in data, (
        "internship-fit endpoint returned no fit score"
    )


def test_resume_improvement():
    data = json_request(
        "/api/resume/improve",
        "POST",
        {"resume_text": RESUME, "job_description": JOB},
    )
    assert isinstance(data, dict) and (
        data.get("improved_bullets") or data.get("general_tips")
    ), "resume-improvement endpoint returned no improvements"


def test_ats():
    data = json_request(
        "/api/ats/analyze",
        "POST",
        {
            "user_name": "CareerLens Smoke Test",
            "job_title": "Software Engineering Intern",
            "company_name": "Example Company",
            "resume_text": RESUME,
            "job_description": JOB,
        },
    )
    assert isinstance(data, dict) and isinstance(data.get("ats_score"), (int, float)), (
        "ATS endpoint returned no numeric score"
    )


def test_job_comparison():
    data = json_request(
        "/api/jobs/compare",
        "POST",
        {
            "resume_text": RESUME,
            "jobs": [
                {"title": "Software Intern", "company": "Example A", "description": JOB},
                {"title": "ML Intern", "company": "Example B", "description": JOB + " Focus on Python and machine learning."},
            ],
        },
    )
    assert isinstance(data, list) and len(data) >= 1, (
        "job comparison endpoint returned no scored jobs"
    )
    assert all(isinstance(item.get("ats_score"), (int, float)) for item in data), (
        "job comparison response is missing scores"
    )


def test_chat():
    data = json_request(
        "/api/chat",
        "POST",
        {"message": "Give me one short interview preparation tip.", "resume_text": RESUME},
    )
    assert isinstance(data, dict) and len(str(data.get("response", "")).strip()) > 10, (
        "career-coach endpoint returned no response"
    )
    # Clean up the smoke-test conversation.
    json_request("/api/chat/clear", "POST", {})


def test_dashboard_and_saved_jobs():
    stats = json_request("/api/session/stats")
    assert isinstance(stats, dict) and "saved_jobs" in stats, (
        "dashboard stats endpoint returned an unexpected result"
    )
    jobs = json_request("/api/jobs/saved")
    assert isinstance(jobs, list), "saved-jobs endpoint did not return a list"


def test_resume_upload():
    boundary = "----CareerLensSmoke" + uuid.uuid4().hex
    file_bytes = (
        b"MEGHANA YARA\nEDUCATION\nB.Tech Computer Science\nSKILLS\nPython SQL Java\n"
        b"PROJECTS\nBuilt a Python application.\n"
    )
    payload = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="careerlens-smoke.txt"\r\n'
        "Content-Type: text/plain\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
    data = json_request_with_multipart(
        "/api/resume/upload",
        payload,
        {"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    assert isinstance(data, dict) and data.get("filename") == "careerlens-smoke.txt", (
        "resume upload endpoint did not return the uploaded file"
    )
    assert data.get("preview"), "resume parser returned an empty preview"


def json_request_with_multipart(path, body_bytes, headers):
    status, response_headers, raw = request(path, "POST", headers=headers, data=body_bytes)
    assert status == 200, f"POST {path}: expected HTTP 200, got {status}"
    body = json.loads(raw)
    assert body.get("success") is True, (
        f"POST {path}: API did not report success: {str(body)[:400]}"
    )
    return body.get("data")


def main():
    checks = [
        ("backend health", test_health),
        ("browser CORS preflight", test_cors),
        ("resume upload and parsing", test_resume_upload),
        ("ATS analysis", test_ats),
        ("cover letter generation", test_cover_letter),
        ("interview question generation", test_interview),
        ("skill-gap analysis", test_skill_gaps),
        ("career roadmap", test_roadmap),
        ("internship-fit analysis", test_internship_fit),
        ("resume bullet rewriting", test_resume_improvement),
        ("job comparison", test_job_comparison),
        ("career coach chat", test_chat),
        ("dashboard and saved jobs", test_dashboard_and_saved_jobs),
    ]
    for name, fn in checks:
        check(name, fn)
    print(f"ALL {len(checks)} LIVE API CHECKS PASSED", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)

"""
CareerLens AI — Flask Application
Main entry point with all API routes.
"""

import os
import sys
import json
import uuid
import logging
from pathlib import Path
from datetime import datetime
from functools import wraps

from flask import (
    Flask, request, jsonify, render_template,
    session, send_from_directory, abort
)
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# ─── Setup ────────────────────────────────────────────────────────────────────
load_dotenv()
BASE_DIR = Path(__file__).parent   # project root (where app.py lives)
sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("careerlens")

# ─── App Factory ──────────────────────────────────────────────────────────────
def create_app():
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "frontend" / "templates"),
        static_folder=str(BASE_DIR / "frontend" / "static"),
    )

    # Configuration
    app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(32).hex())
    app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_UPLOAD_MB", 10)) * 1024 * 1024
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///careerlens.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    UPLOAD_FOLDER = BASE_DIR / "uploads"
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)

    CORS(app, supports_credentials=True)

    # Init database
    from backend.models import init_db, db
    init_db(app)

    # ── Helpers ────────────────────────────────────────────────────────────────
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

    def allowed_file(filename):
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

    def get_or_create_session():
        if "session_id" not in session:
            session["session_id"] = str(uuid.uuid4())
        return session["session_id"]

    def ensure_user_session(session_id):
        from backend.models import UserSession
        user_sess = UserSession.query.filter_by(session_id=session_id).first()
        if not user_sess:
            user_sess = UserSession(session_id=session_id)
            db.session.add(user_sess)
            db.session.commit()
        return user_sess

    def api_response(data=None, error=None, status=200):
        if error:
            return jsonify({"success": False, "error": error}), status
        return jsonify({"success": True, "data": data}), status

    # ─── Routes ────────────────────────────────────────────────────────────────

    @app.route("/")
    def index():
        """Serve the main dashboard."""
        return render_template("index.html")

    @app.route("/health")
    def health():
        from backend.watsonx_client import get_watsonx_client
        client = get_watsonx_client()
        return jsonify({
            "status": "healthy",
            "app": "CareerLens AI",
            "version": "1.0.0",
            "watsonx_initialized": client._initialized,
            "timestamp": datetime.utcnow().isoformat(),
        })

    # ── Resume Upload ──────────────────────────────────────────────────────────
    @app.route("/api/resume/upload", methods=["POST"])
    def upload_resume():
        session_id = get_or_create_session()
        ensure_user_session(session_id)

        if "file" not in request.files:
            return api_response(error="No file provided", status=400)

        file = request.files["file"]
        if not file or file.filename == "":
            return api_response(error="Empty filename", status=400)

        if not allowed_file(file.filename):
            return api_response(error="Only PDF, DOCX, and TXT files are supported", status=400)

        filename = secure_filename(file.filename)
        unique_name = f"{session_id}_{filename}"
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
        file.save(file_path)

        from backend.resume_parser import parse_resume, extract_skills_from_text
        from backend.models import UserSession

        parsed = parse_resume(file_path)
        if parsed.get("error") and not parsed.get("text"):
            return api_response(error=f"Could not parse file: {parsed['error']}", status=422)

        # Update user session with resume info
        user_sess = UserSession.query.filter_by(session_id=session_id).first()
        if user_sess:
            user_sess.resume_filename = filename
            user_sess.resume_text_snippet = parsed["text"][:500]
            db.session.commit()

        # Store full resume text in server session
        session["resume_text"] = parsed["text"]
        session["resume_filename"] = filename

        skills = extract_skills_from_text(parsed["text"])

        return api_response({
            "filename": filename,
            "format": parsed.get("format", ""),
            "word_count": parsed.get("word_count", 0),
            "sections_detected": list(parsed.get("sections", {}).keys()),
            "contact": parsed.get("contact", {}),
            "skills_detected": skills[:20],
            "preview": parsed["text"][:400] + "..." if len(parsed["text"]) > 400 else parsed["text"],
        })

    # ── ATS Analysis ──────────────────────────────────────────────────────────
    @app.route("/api/ats/analyze", methods=["POST"])
    def analyze_ats():
        session_id = get_or_create_session()
        data = request.get_json(force=True) or {}

        job_description = data.get("job_description", "").strip()
        resume_text = data.get("resume_text") or session.get("resume_text", "")
        user_name = data.get("user_name", "Applicant")
        job_title = data.get("job_title", "")
        company_name = data.get("company_name", "")

        if not job_description:
            return api_response(error="Job description is required", status=400)
        if not resume_text:
            return api_response(error="Please upload your resume first", status=400)
        if len(job_description) < 50:
            return api_response(error="Job description is too short (min 50 chars)", status=400)

        from backend.career_tools import analyze_resume_vs_jd
        from backend.models import ATSAnalysis

        logger.info(f"[{session_id}] Running ATS analysis — JD: {len(job_description)} chars")
        result = analyze_resume_vs_jd(resume_text, job_description, user_name)

        # Save to DB
        ensure_user_session(session_id)
        analysis = ATSAnalysis(
            session_id=session_id,
            job_title=job_title or "Unknown Role",
            company_name=company_name,
            job_description_snippet=job_description[:300],
            ats_score=result.get("ats_score", 0),
            score_breakdown_json=json.dumps(result.get("score_breakdown", {})),
            matched_skills_json=json.dumps(result.get("matched_skills", [])),
            missing_keywords_json=json.dumps(result.get("missing_keywords", [])),
            overall_verdict=result.get("overall_verdict", ""),
        )
        db.session.add(analysis)
        db.session.commit()

        result["analysis_id"] = analysis.id
        return api_response(result)

    # ── Cover Letter ──────────────────────────────────────────────────────────
    @app.route("/api/cover-letter/generate", methods=["POST"])
    def generate_cover_letter():
        data = request.get_json(force=True) or {}
        job_description = data.get("job_description", "").strip()
        resume_text = data.get("resume_text") or session.get("resume_text", "")
        user_name = data.get("user_name", "Applicant")

        if not job_description:
            return api_response(error="Job description is required", status=400)
        # Allow cover letter generation without resume — use a generic placeholder
        if not resume_text:
            resume_text = (
                "Motivated professional with a strong academic background and relevant skills. "
                "Eager to contribute to the team and grow in the role."
            )

        from backend.career_tools import generate_cover_letter
        logger.info("Generating cover letter")
        result = generate_cover_letter(resume_text, job_description, user_name)
        return api_response(result)

    # ── Interview Questions ────────────────────────────────────────────────────
    @app.route("/api/interview/questions", methods=["POST"])
    def get_interview_questions():
        data = request.get_json(force=True) or {}
        job_description = data.get("job_description", "").strip()
        resume_text = data.get("resume_text") or session.get("resume_text", "")

        if not job_description:
            return api_response(error="Job description is required", status=400)

        from backend.career_tools import generate_interview_questions
        result = generate_interview_questions(job_description, resume_text)
        return api_response(result)

    # ── Skill Gap Analysis ────────────────────────────────────────────────────
    @app.route("/api/skills/gap", methods=["POST"])
    def skill_gap_analysis():
        data = request.get_json(force=True) or {}
        job_description = data.get("job_description", "").strip()
        resume_text = data.get("resume_text") or session.get("resume_text", "")

        if not job_description or not resume_text:
            return api_response(error="Both resume and job description are required", status=400)

        from backend.career_tools import analyze_skill_gaps
        result = analyze_skill_gaps(resume_text, job_description)
        return api_response(result)

    # ── Career Roadmap ────────────────────────────────────────────────────────
    @app.route("/api/roadmap/generate", methods=["POST"])
    def generate_roadmap():
        data = request.get_json(force=True) or {}
        target_role = data.get("target_role", "").strip()
        resume_text = data.get("resume_text") or session.get("resume_text", "")

        if not target_role:
            return api_response(error="Target role is required", status=400)

        from backend.career_tools import generate_career_roadmap
        result = generate_career_roadmap(resume_text or "Student/fresher looking to start career", target_role)
        return api_response(result)

    # ── Internship Fit ────────────────────────────────────────────────────────
    @app.route("/api/internship/fit", methods=["POST"])
    def internship_fit():
        data = request.get_json(force=True) or {}
        internship_description = data.get("internship_description", "").strip()
        resume_text = data.get("resume_text") or session.get("resume_text", "")

        if not internship_description:
            return api_response(error="Internship description is required", status=400)

        from backend.career_tools import analyze_internship_fit
        result = analyze_internship_fit(resume_text or "", internship_description)
        return api_response(result)

    # ── Resume Bullets Improvement ────────────────────────────────────────────
    @app.route("/api/resume/improve", methods=["POST"])
    def improve_resume():
        data = request.get_json(force=True) or {}
        resume_text = data.get("resume_text") or session.get("resume_text", "")
        job_description = data.get("job_description", "")

        if not resume_text:
            return api_response(error="Please upload your resume first", status=400)

        from backend.career_tools import improve_resume_bullets
        result = improve_resume_bullets(resume_text, job_description)
        return api_response(result)

    # ── Job Comparison ────────────────────────────────────────────────────────
    @app.route("/api/jobs/compare", methods=["POST"])
    def compare_jobs_endpoint():
        data = request.get_json(force=True) or {}
        jobs = data.get("jobs", [])
        resume_text = data.get("resume_text") or session.get("resume_text", "")

        if not jobs:
            return api_response(error="No jobs provided to compare", status=400)
        if not resume_text:
            return api_response(error="Please upload your resume first", status=400)
        if len(jobs) > 5:
            return api_response(error="Maximum 5 jobs can be compared at once", status=400)

        from backend.ats_analyzer import compare_jobs
        result = compare_jobs(resume_text, jobs)
        return api_response(result)

    # ── Save Job ──────────────────────────────────────────────────────────────
    @app.route("/api/jobs/save", methods=["POST"])
    def save_job():
        session_id = get_or_create_session()
        ensure_user_session(session_id)
        data = request.get_json(force=True) or {}

        from backend.models import SavedJob
        job = SavedJob(
            session_id=session_id,
            job_title=data.get("job_title", "Unknown Role"),
            company_name=data.get("company_name", ""),
            job_description=data.get("job_description", ""),
            job_url=data.get("job_url", ""),
            ats_score=data.get("ats_score"),
            notes=data.get("notes", ""),
        )
        db.session.add(job)
        db.session.commit()
        return api_response(job.to_dict())

    @app.route("/api/jobs/saved", methods=["GET"])
    def get_saved_jobs():
        session_id = get_or_create_session()
        from backend.models import SavedJob
        jobs = SavedJob.query.filter_by(session_id=session_id).order_by(SavedJob.created_at.desc()).all()
        return api_response([j.to_dict() for j in jobs])

    @app.route("/api/jobs/<int:job_id>", methods=["DELETE"])
    def delete_job(job_id):
        session_id = get_or_create_session()
        from backend.models import SavedJob
        job = SavedJob.query.filter_by(id=job_id, session_id=session_id).first()
        if not job:
            return api_response(error="Job not found", status=404)
        db.session.delete(job)
        db.session.commit()
        return api_response({"deleted": True})

    # ── Chat ──────────────────────────────────────────────────────────────────
    @app.route("/api/chat", methods=["POST"])
    def chat():
        session_id = get_or_create_session()
        ensure_user_session(session_id)
        data = request.get_json(force=True) or {}
        message = data.get("message", "").strip()

        if not message:
            return api_response(error="Message cannot be empty", status=400)
        if len(message) > 2000:
            return api_response(error="Message too long (max 2000 chars)", status=400)

        from backend.career_tools import chat_with_agent
        from backend.models import ChatMessage

        resume_text = session.get("resume_text", "")

        # Get recent chat context (last 3 exchanges)
        recent_msgs = ChatMessage.query.filter_by(session_id=session_id)\
            .order_by(ChatMessage.created_at.desc()).limit(6).all()
        recent_msgs.reverse()
        context = " | ".join([f"{m.role}: {m.content[:100]}" for m in recent_msgs])

        result = chat_with_agent(message, context, resume_text)

        # Save messages
        user_msg = ChatMessage(session_id=session_id, role="user", content=message,
                               language=result.get("language", "en"))
        ai_msg = ChatMessage(session_id=session_id, role="assistant",
                             content=result["response"], language=result.get("language", "en"))
        db.session.add(user_msg)
        db.session.add(ai_msg)
        db.session.commit()

        return api_response(result)

    @app.route("/api/chat/history", methods=["GET"])
    def chat_history():
        session_id = get_or_create_session()
        from backend.models import ChatMessage
        messages = ChatMessage.query.filter_by(session_id=session_id)\
            .order_by(ChatMessage.created_at.asc()).limit(50).all()
        return api_response([m.to_dict() for m in messages])

    @app.route("/api/chat/clear", methods=["POST"])
    def clear_chat():
        session_id = get_or_create_session()
        from backend.models import ChatMessage
        ChatMessage.query.filter_by(session_id=session_id).delete()
        db.session.commit()
        return api_response({"cleared": True})

    # ── Session / Dashboard Stats ─────────────────────────────────────────────
    @app.route("/api/session/stats", methods=["GET"])
    def session_stats():
        session_id = get_or_create_session()
        ensure_user_session(session_id)
        from backend.models import ATSAnalysis, SavedJob, ChatMessage, UserSession

        user_sess = UserSession.query.filter_by(session_id=session_id).first()
        analyses = ATSAnalysis.query.filter_by(session_id=session_id).order_by(ATSAnalysis.created_at.desc()).limit(5).all()
        saved_count = SavedJob.query.filter_by(session_id=session_id).count()
        chat_count = ChatMessage.query.filter_by(session_id=session_id, role="user").count()

        avg_score = 0
        if analyses:
            avg_score = round(sum(a.ats_score for a in analyses) / len(analyses))

        return api_response({
            "session_id": session_id,
            "user_name": user_sess.user_name if user_sess else "User",
            "resume_uploaded": bool(session.get("resume_text")),
            "resume_filename": session.get("resume_filename", ""),
            "total_analyses": len(analyses),
            "avg_ats_score": avg_score,
            "saved_jobs": saved_count,
            "chat_messages": chat_count,
            "recent_analyses": [a.to_dict() for a in analyses[:3]],
        })

    @app.route("/api/session/name", methods=["POST"])
    def set_user_name():
        session_id = get_or_create_session()
        data = request.get_json(force=True) or {}
        name = data.get("name", "").strip()[:100]
        if not name:
            return api_response(error="Name cannot be empty", status=400)

        from backend.models import UserSession
        ensure_user_session(session_id)
        user_sess = UserSession.query.filter_by(session_id=session_id).first()
        if user_sess:
            user_sess.user_name = name
            db.session.commit()
        session["user_name"] = name
        return api_response({"name": name})

    # ── Error Handlers ────────────────────────────────────────────────────────
    @app.errorhandler(413)
    def file_too_large(e):
        max_mb = int(os.getenv("MAX_UPLOAD_MB", 10))
        return api_response(error=f"File too large. Maximum size is {max_mb}MB.", status=413)

    @app.errorhandler(404)
    def not_found(e):
        return api_response(error="Endpoint not found", status=404)

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"Internal error: {e}")
        return api_response(error="Internal server error. Please try again.", status=500)

    return app


# ─── Entry Point ──────────────────────────────────────────────────────────────
app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    logger.info(f"🚀 CareerLens AI starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)

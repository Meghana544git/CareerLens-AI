"""
CareerLens AI — Database Models
SQLAlchemy models for storing sessions, analyses, and saved jobs.
"""

import os
import sys
import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class UserSession(db.Model):
    """Tracks user sessions and their resume + analysis state."""
    __tablename__ = "user_sessions"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(128), unique=True, nullable=False, index=True)
    user_name = db.Column(db.String(200), default="User")
    resume_filename = db.Column(db.String(300))
    resume_text_snippet = db.Column(db.Text)  # First 500 chars
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    language = db.Column(db.String(5), default="en")

    analyses = db.relationship("ATSAnalysis", backref="session", lazy=True, cascade="all, delete-orphan")
    saved_jobs = db.relationship("SavedJob", backref="session", lazy=True, cascade="all, delete-orphan")
    chat_messages = db.relationship("ChatMessage", backref="session", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_name": self.user_name,
            "resume_filename": self.resume_filename,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "language": self.language,
        }


class ATSAnalysis(db.Model):
    """Stores ATS analysis results for a session."""
    __tablename__ = "ats_analyses"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(128), db.ForeignKey("user_sessions.session_id"), nullable=False)
    job_title = db.Column(db.String(200))
    company_name = db.Column(db.String(200))
    job_description_snippet = db.Column(db.Text)  # First 300 chars
    ats_score = db.Column(db.Integer, default=0)
    score_breakdown_json = db.Column(db.Text)   # JSON string
    matched_skills_json = db.Column(db.Text)    # JSON string
    missing_keywords_json = db.Column(db.Text)  # JSON string
    overall_verdict = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "job_title": self.job_title,
            "company_name": self.company_name,
            "ats_score": self.ats_score,
            "score_breakdown": json.loads(self.score_breakdown_json or "{}"),
            "matched_skills": json.loads(self.matched_skills_json or "[]"),
            "missing_keywords": json.loads(self.missing_keywords_json or "[]"),
            "overall_verdict": self.overall_verdict,
            "created_at": self.created_at.isoformat(),
        }


class SavedJob(db.Model):
    """Saved target jobs for comparison."""
    __tablename__ = "saved_jobs"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(128), db.ForeignKey("user_sessions.session_id"), nullable=False)
    job_title = db.Column(db.String(200), nullable=False)
    company_name = db.Column(db.String(200))
    job_description = db.Column(db.Text)
    job_url = db.Column(db.String(500))
    ats_score = db.Column(db.Integer)
    status = db.Column(db.String(50), default="saved")  # saved, applied, interview, offer
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "job_title": self.job_title,
            "company_name": self.company_name,
            "ats_score": self.ats_score,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "job_url": self.job_url,
        }


class ChatMessage(db.Model):
    """Stores chat history for a session."""
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(128), db.ForeignKey("user_sessions.session_id"), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(5), default="en")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "language": self.language,
            "created_at": self.created_at.isoformat(),
        }


def init_db(app):
    """Initialize the database with the Flask app."""
    db.init_app(app)
    with app.app_context():
        db.create_all()

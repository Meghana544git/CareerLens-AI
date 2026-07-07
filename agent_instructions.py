"""
╔══════════════════════════════════════════════════════════════════════════════╗
║               CareerLens AI — AGENT INSTRUCTIONS & CONFIG                   ║
║   Edit this file to customize ALL aspects of the AI career coach behavior.  ║
╚══════════════════════════════════════════════════════════════════════════════╝

This is the single source of truth for:
  • Agent personality, tone, and behavior
  • Scoring logic weights for ATS analysis
  • Safety rules and output constraints
  • Language support configuration
  • Career specialization domains
  • Prompt templates for every feature
  • Resource recommendation sources
"""

# ─────────────────────────────────────────────────────────────────────────────
# 1. AGENT PERSONALITY & TONE
# ─────────────────────────────────────────────────────────────────────────────
AGENT_PERSONA = {
    "name": "CareerLens AI",
    "role": "Expert Career Coach, ATS Analyst, and Internship Advisor",
    "tone": "professional yet warm, encouraging, practical, direct",
    "style": (
        "Speak like a senior mentor who genuinely cares about the user's success. "
        "Be specific — give concrete, actionable advice, never generic platitudes. "
        "Use bullet points for clarity. Celebrate wins. Be honest about gaps. "
        "Never be condescending. Match user's energy and language."
    ),
    "max_response_length": "detailed but concise — aim for 300-600 words unless asked for more",
    "emoji_usage": "minimal — only for section headers or emphasis, never overdo it",
}

# ─────────────────────────────────────────────────────────────────────────────
# 2. LANGUAGE SUPPORT
# ─────────────────────────────────────────────────────────────────────────────
LANGUAGE_CONFIG = {
    "default_language": "en",
    "supported_languages": {
        "en": "English",
        "hi": "Hindi",
    },
    "auto_detect": True,          # Detect user's language and respond in kind
    "hindi_instruction": (
        "यदि उपयोगकर्ता हिंदी में बात करे तो हिंदी में उत्तर दें। "
        "Professional terms (like 'ATS score', 'resume', 'skill gap') को English में रखें। "
        "Simple, clear Hindi use करें — not overly formal."
    ),
    "bilingual_tips": True,       # Show resume/interview terms in both EN + HI
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. ATS SCORING LOGIC — Adjust weights to tune scoring behavior
# ─────────────────────────────────────────────────────────────────────────────
ATS_SCORING_WEIGHTS = {
    # Keyword match: percentage of JD keywords found in resume
    "keyword_match":        0.35,   # 35% weight
    # Skills coverage: hard skills / tech stack alignment
    "skills_coverage":      0.25,   # 25% weight
    # Experience relevance: years and domain match signals
    "experience_relevance": 0.15,   # 15% weight
    # Education match: degree / certification alignment
    "education_match":      0.10,   # 10% weight
    # Resume structure quality: sections, action verbs, quantification
    "resume_quality":       0.10,   # 10% weight
    # Job title alignment: target role vs resume roles
    "title_alignment":      0.05,   # 5% weight
}

ATS_SCORE_THRESHOLDS = {
    "excellent":  (85, 100, "🟢 Excellent Match — Apply with confidence!"),
    "good":       (70, 84,  "🔵 Good Match — Minor tweaks recommended."),
    "fair":       (50, 69,  "🟡 Fair Match — Several gaps to address."),
    "weak":       (30, 49,  "🟠 Weak Match — Significant gaps exist."),
    "poor":       (0,  29,  "🔴 Poor Match — Major alignment work needed."),
}

# Bonus points for strong signals
ATS_BONUS_RULES = {
    "quantified_achievements": 3,   # +3 if resume has numbers/metrics
    "action_verbs_used": 2,         # +2 for strong action verbs
    "matching_job_title": 4,        # +4 if current/previous title matches
    "certifications_match": 3,      # +3 if certs mentioned in JD are present
    "github_linkedin_present": 2,   # +2 for professional links
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. CAREER SPECIALIZATION DOMAINS
# ─────────────────────────────────────────────────────────────────────────────
CAREER_DOMAINS = {
    "software_engineering": {
        "keywords": ["python", "java", "javascript", "react", "node", "sql", "git", "api", "docker", "kubernetes"],
        "core_skills": ["algorithms", "data structures", "system design", "OOP", "REST APIs"],
        "certifications": ["AWS Certified", "Google Cloud", "Azure", "Oracle Java"],
    },
    "data_science": {
        "keywords": ["python", "machine learning", "pandas", "numpy", "tensorflow", "pytorch", "sql", "tableau", "power bi"],
        "core_skills": ["statistics", "data wrangling", "ML models", "visualization", "A/B testing"],
        "certifications": ["IBM Data Science", "Google Data Analytics", "AWS ML Specialty"],
    },
    "product_management": {
        "keywords": ["roadmap", "stakeholders", "agile", "scrum", "user stories", "KPIs", "PRD", "wireframes"],
        "core_skills": ["product strategy", "user research", "prioritization", "go-to-market"],
        "certifications": ["CSPO", "PMI-ACP", "Google PM Certificate"],
    },
    "marketing_digital": {
        "keywords": ["SEO", "SEM", "google analytics", "content", "social media", "email campaigns", "CRM", "conversion"],
        "core_skills": ["campaign management", "copywriting", "data analysis", "brand strategy"],
        "certifications": ["Google Analytics", "HubSpot", "Meta Blueprint"],
    },
    "finance_accounting": {
        "keywords": ["financial modeling", "excel", "valuation", "DCF", "GAAP", "budgeting", "forecasting", "bloomberg"],
        "core_skills": ["financial analysis", "reporting", "audit", "tax", "investment analysis"],
        "certifications": ["CFA", "CPA", "FRM", "Bloomberg Market Concepts"],
    },
    "design_ux": {
        "keywords": ["figma", "sketch", "adobe xd", "user research", "wireframes", "prototyping", "accessibility", "css"],
        "core_skills": ["UX research", "visual design", "design systems", "usability testing"],
        "certifications": ["Google UX Design", "Interaction Design Foundation", "Adobe Certified"],
    },
    "internship_general": {
        "keywords": ["communication", "teamwork", "problem-solving", "microsoft office", "excel", "presentation", "research"],
        "core_skills": ["time management", "adaptability", "critical thinking", "collaboration"],
        "certifications": ["Any relevant online course", "Coursera", "edX"],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# 5. PROMPT TEMPLATES — Edit these to fine-tune AI output for each feature
# ─────────────────────────────────────────────────────────────────────────────

def get_ats_analysis_prompt(resume_text: str, job_description: str, language: str = "en") -> str:
    lang_note = "Respond in Hindi if the language is 'hi', else English." if language == "hi" else ""
    return f"""You are CareerLens AI, an expert ATS analyst and career coach.
{lang_note}

Analyze this resume against the job description and provide a structured ATS analysis.

JOB DESCRIPTION:
{job_description}

RESUME:
{resume_text}

Provide your analysis in this EXACT JSON format:
{{
  "ats_score": <integer 0-100>,
  "score_breakdown": {{
    "keyword_match": <0-100>,
    "skills_coverage": <0-100>,
    "experience_relevance": <0-100>,
    "education_match": <0-100>,
    "resume_quality": <0-100>
  }},
  "matched_skills": [<list of skills found in both>],
  "missing_keywords": [<critical keywords from JD missing in resume>],
  "weak_skills": [<skills present but need strengthening>],
  "role_fit_summary": "<2-3 sentence honest assessment>",
  "top_strengths": [<3-5 bullet points>],
  "improvement_actions": [<3-5 specific, actionable bullet points>],
  "resume_bullet_rewrites": [
    {{"original": "<original bullet>", "improved": "<rewritten with metrics/action verbs>"}}
  ],
  "overall_verdict": "<Excellent/Good/Fair/Weak/Poor Match with brief reason>"
}}
Return ONLY valid JSON, no extra text."""


def get_cover_letter_prompt(resume_text: str, job_description: str, user_name: str = "Applicant", language: str = "en") -> str:
    lang_note = "Write the cover letter in Hindi if language is 'hi'." if language == "hi" else ""
    return f"""You are CareerLens AI, an expert career coach and professional writer.
{lang_note}

Write a compelling, personalized cover letter for this job application.

APPLICANT RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

APPLICANT NAME: {user_name}

Guidelines:
- 3-4 paragraphs, professional but warm tone
- Opening: Hook with genuine enthusiasm and key qualification
- Body 1: Match top 2-3 experiences/skills to the role's needs
- Body 2: Show cultural fit and specific value you bring
- Closing: Clear call to action, confident but not arrogant
- Use specific details from both the resume and JD — never generic
- Length: 250-350 words
- Do NOT use placeholder text like [Company Name] — extract from the JD or use "your team"

Return ONLY the cover letter text, ready to send."""


def get_interview_questions_prompt(job_description: str, resume_text: str, language: str = "en") -> str:
    lang_note = "Respond in Hindi if language is 'hi'." if language == "hi" else ""
    return f"""You are CareerLens AI, an expert interview coach with deep knowledge of hiring practices.
{lang_note}

Based on this job description and candidate resume, generate likely interview questions with preparation guidance.

JOB DESCRIPTION:
{job_description}

RESUME SUMMARY:
{resume_text[:1000]}

Return in this JSON format:
{{
  "behavioral_questions": [
    {{
      "question": "<STAR-method question>",
      "why_asked": "<what interviewer is assessing>",
      "sample_answer_framework": "<2-3 sentence guide>",
      "tip": "<preparation tip>"
    }}
  ],
  "technical_questions": [
    {{
      "question": "<technical question>",
      "expected_answer_points": ["<point 1>", "<point 2>"],
      "difficulty": "easy|medium|hard"
    }}
  ],
  "situational_questions": [
    {{
      "question": "<situation-based question>",
      "ideal_approach": "<how to structure the answer>"
    }}
  ],
  "questions_to_ask_interviewer": [
    "<smart question candidate should ask>"
  ],
  "preparation_checklist": ["<action item 1>", "<action item 2>"]
}}
Return ONLY valid JSON."""


def get_skill_gap_prompt(resume_text: str, job_description: str, language: str = "en") -> str:
    lang_note = "Respond in Hindi if language is 'hi'." if language == "hi" else ""
    return f"""You are CareerLens AI, an expert skill development advisor.
{lang_note}

Identify skill gaps and create a personalized learning roadmap.

JOB DESCRIPTION:
{job_description}

RESUME:
{resume_text}

Return in this JSON format:
{{
  "critical_gaps": [
    {{
      "skill": "<skill name>",
      "importance": "high|medium|low",
      "reason": "<why this skill matters for the role>",
      "learning_time": "<estimated weeks to learn>",
      "free_resources": [
        {{"name": "<resource name>", "url": "<url>", "type": "course|tutorial|docs|practice"}}
      ]
    }}
  ],
  "nice_to_have_gaps": [
    {{
      "skill": "<skill name>",
      "free_resources": [{{"name": "<name>", "url": "<url>", "type": "<type>"}}]
    }}
  ],
  "learning_roadmap": [
    {{"week": 1, "focus": "<what to learn>", "resources": ["<resource 1>", "<resource 2>"], "milestone": "<what you can do after>"}}
  ],
  "quick_wins": ["<skill you can add/improve this week>"],
  "career_advice": "<2-3 sentences of personalized career strategy>"
}}
Return ONLY valid JSON."""


def get_career_roadmap_prompt(resume_text: str, target_role: str, language: str = "en") -> str:
    lang_note = "Respond in Hindi if language is 'hi'." if language == "hi" else ""
    return f"""You are CareerLens AI, an expert career strategist.
{lang_note}

Create a detailed career roadmap from the candidate's current position to their target role.

TARGET ROLE: {target_role}

CURRENT PROFILE (from resume):
{resume_text[:1500]}

Return in this JSON format:
{{
  "current_level": "<entry/mid/senior level assessment>",
  "target_level": "<what level the target role is>",
  "estimated_timeline": "<realistic time estimate>",
  "roadmap_phases": [
    {{
      "phase": "<Phase 1: Foundation / Phase 2: Growth / etc>",
      "duration": "<e.g., 0-3 months>",
      "goals": ["<goal 1>", "<goal 2>"],
      "skills_to_build": ["<skill 1>", "<skill 2>"],
      "certifications": ["<cert 1>"],
      "projects_to_build": ["<project idea>"],
      "milestone": "<what success looks like>"
    }}
  ],
  "internship_opportunities": [
    {{"type": "<internship type>", "companies_to_target": ["<company 1>"], "how_to_apply": "<strategy>"}}
  ],
  "networking_strategy": ["<action 1>", "<action 2>"],
  "salary_range": {{"entry": "<INR/USD range>", "experienced": "<INR/USD range>"}},
  "motivational_note": "<personalized encouragement>"
}}
Return ONLY valid JSON."""


def get_chat_prompt(user_message: str, context: str = "", language: str = "en") -> str:
    lang_note = ""
    if language == "hi":
        lang_note = "उपयोगकर्ता हिंदी में बात कर रहे हैं। हिंदी में जवाब दें। Professional terms English में रखें।"
    
    return f"""You are CareerLens AI — an expert career coach, ATS analyst, and internship advisor.
{lang_note}

Your personality: Professional, warm, encouraging, specific, practical. Like a senior mentor.
Never give generic advice. Always be specific and actionable.
You help with: resume writing, ATS optimization, cover letters, interview prep, skill gaps, career planning, internship search, salary negotiation, LinkedIn optimization, and professional English.

{f"Context from session: {context}" if context else ""}

User: {user_message}

Respond helpfully as CareerLens AI. Be direct, specific, and encouraging."""


# ─────────────────────────────────────────────────────────────────────────────
# 6. SAFETY RULES
# ─────────────────────────────────────────────────────────────────────────────
SAFETY_RULES = {
    "refuse_topics": [
        "generating fake credentials or certifications",
        "plagiarism or copying others' work",
        "lying on resumes or applications",
        "discriminatory hiring advice",
        "salary information for illegal activities",
    ],
    "safe_refusal_message": (
        "I'm here to help you succeed honestly and ethically. "
        "I can't help with that, but I'd love to help you build genuine skills "
        "and a resume that truly represents your abilities!"
    ),
    "pii_warning": True,  # Warn users not to include SSN, bank details etc.
    "max_resume_size_mb": 10,
}

# ─────────────────────────────────────────────────────────────────────────────
# 7. RESOURCE RECOMMENDATIONS (Fallback if AI doesn't provide URLs)
# ─────────────────────────────────────────────────────────────────────────────
LEARNING_RESOURCES = {
    "python":           {"name": "Python for Everybody", "url": "https://www.coursera.org/specializations/python", "type": "course"},
    "machine_learning": {"name": "ML by Andrew Ng",      "url": "https://www.coursera.org/learn/machine-learning", "type": "course"},
    "sql":              {"name": "SQLZoo",                "url": "https://sqlzoo.net", "type": "practice"},
    "react":            {"name": "React Docs",            "url": "https://react.dev/learn", "type": "docs"},
    "system_design":    {"name": "System Design Primer",  "url": "https://github.com/donnemartin/system-design-primer", "type": "tutorial"},
    "dsa":              {"name": "LeetCode",              "url": "https://leetcode.com", "type": "practice"},
    "docker":           {"name": "Docker Get Started",    "url": "https://docs.docker.com/get-started/", "type": "docs"},
    "git":              {"name": "Git Tutorial",          "url": "https://learngitbranching.js.org", "type": "practice"},
    "communication":    {"name": "Toastmasters",          "url": "https://www.toastmasters.org", "type": "community"},
    "interview_prep":   {"name": "Glassdoor Interview Q", "url": "https://www.glassdoor.com/Interview/index.htm", "type": "practice"},
    "resume":           {"name": "Harvard Resume Guide",  "url": "https://ocs.fas.harvard.edu/resumes-cvs", "type": "docs"},
    "linkedin":         {"name": "LinkedIn Learning",     "url": "https://www.linkedin.com/learning/", "type": "course"},
}

# ─────────────────────────────────────────────────────────────────────────────
# 8. INTERNSHIP FIT CRITERIA
# ─────────────────────────────────────────────────────────────────────────────
INTERNSHIP_FIT_CONFIG = {
    "ideal_cgpa_mention": True,      # Check if CGPA is mentioned
    "projects_weight": 0.30,          # Projects matter most for freshers
    "skills_weight": 0.40,            # Skills / tech stack
    "experience_weight": 0.20,        # Any prior internship/part-time
    "certifications_weight": 0.10,    # Online certifications
    "min_score_to_apply": 45,         # Recommend applying if score >= 45
    "fresher_bonus": 5,               # Grace points for freshers / students
    "top_internship_platforms": [
        {"name": "Internshala",    "url": "https://internshala.com"},
        {"name": "LinkedIn Jobs",  "url": "https://www.linkedin.com/jobs/"},
        {"name": "Unstop",         "url": "https://unstop.com"},
        {"name": "AngelList",      "url": "https://wellfound.com/jobs"},
        {"name": "Indeed",         "url": "https://www.indeed.com"},
        {"name": "Glassdoor",      "url": "https://www.glassdoor.com"},
        {"name": "Naukri",         "url": "https://www.naukri.com"},
        {"name": "IBM SkillsBuild","url": "https://skillsbuild.org"},
    ],
}

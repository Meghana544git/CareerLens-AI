"""
Deterministic career-content generators for CareerLens AI.

These functions use the user's text, keyword matching and transparent templates.
They do not call a language model, external AI API, or paid generation service.
"""
import re
from typing import Any

SKILL_PATTERNS = [
    ("Python", r"\bpython\b"),
    ("Java", r"\bjava\b"),
    ("JavaScript", r"\bjavascript\b"),
    ("TypeScript", r"\btypescript\b"),
    ("C++", r"(?<![a-z0-9])c\+\+(?![a-z0-9])"),
    ("C#", r"(?<![a-z0-9])c#(?![a-z0-9])"),
    ("SQL", r"\bsql\b"),
    ("MySQL", r"\bmysql\b"),
    ("PostgreSQL", r"\bpostgres(?:ql)?\b"),
    ("HTML", r"\bhtml5?\b"),
    ("CSS", r"\bcss3?\b"),
    ("React", r"\breact(?:\.js)?\b"),
    ("Angular", r"\bangular\b"),
    ("Vue", r"\bvue(?:\.js)?\b"),
    ("Node.js", r"\bnode(?:\.js)?\b"),
    ("Flask", r"\bflask\b"),
    ("Django", r"\bdjango\b"),
    ("FastAPI", r"\bfastapi\b"),
    ("Flutter", r"\bflutter\b"),
    ("Dart", r"\bdart\b"),
    ("REST APIs", r"\brest(?:ful)?\s+api(?:s)?\b|\bapi development\b"),
    ("Git", r"\bgit\b"),
    ("GitHub", r"\bgithub\b"),
    ("Linux", r"\blinux\b"),
    ("AWS", r"\baws\b|amazon web services"),
    ("Azure", r"\bazure\b"),
    ("Google Cloud", r"\bgcp\b|google cloud"),
    ("Docker", r"\bdocker\b"),
    ("Kubernetes", r"\bkubernetes\b|\bk8s\b"),
    ("Terraform", r"\bterraform\b"),
    ("CI/CD", r"\bci\s*/\s*cd\b|\bcontinuous integration\b"),
    ("Machine Learning", r"\bmachine[\s-]+learning\b|\bml models?\b"),
    ("Deep Learning", r"\bdeep[\s-]+learning\b"),
    ("NLP", r"\bnatural language processing\b|\bnlp\b"),
    ("Computer Vision", r"\bcomputer vision\b"),
    ("TensorFlow", r"\btensorflow\b"),
    ("PyTorch", r"\bpytorch\b"),
    ("Pandas", r"\bpandas\b"),
    ("NumPy", r"\bnumpy\b"),
    ("Scikit-learn", r"\bscikit[\s-]?learn\b|\bsklearn\b"),
    ("Apache Spark", r"\bapache spark\b|\bspark\b"),
    ("Hadoop", r"\bhadoop\b"),
    ("Statistics", r"\bstatistics?\b"),
    ("Data Analysis", r"\bdata analysis\b|\banalytical skills\b"),
    ("Data Visualization", r"\bdata visuali[sz]ation\b"),
    ("Excel", r"\bexcel\b"),
    ("Power BI", r"\bpower\s*bi\b"),
    ("Tableau", r"\btableau\b"),
    ("Data Structures and Algorithms", r"\bdata structures\b|\balgorithms\b|\bdsa\b"),
    ("Object-Oriented Programming", r"\bobject[\s-]oriented programming\b|\boop\b"),
    ("System Design", r"\bsystem design\b"),
    ("Cybersecurity", r"\bcyber[\s-]?security\b"),
    ("Networking", r"\bnetworking\b|\btcp/ip\b|\bdns\b"),
    ("Android", r"\bandroid\b"),
    ("React Native", r"\breact native\b"),
    ("Figma", r"\bfigma\b"),
    ("Agile", r"\bagile\b"),
    ("Jira", r"\bjira\b"),
    ("Testing", r"\btesting\b|\bunit tests?\b|\bautomated tests?\b"),
    ("Communication", r"\bcommunication skills?\b|\bcommunicate clearly\b"),
    ("Problem Solving", r"\bproblem[\s-]solving\b"),
]

ROLE_PROFILES = [
    {
        "name": "Machine Learning Engineer",
        "terms": ["machine learning engineer", "ml engineer", "ai engineer", "artificial intelligence engineer"],
        "skills": ["Python", "SQL", "Statistics", "Pandas", "NumPy", "Machine Learning", "Scikit-learn", "PyTorch", "Git", "REST APIs"],
        "project": "Build and document an end-to-end machine-learning project, including data cleaning, a baseline model, evaluation and a simple demo.",
        "resource": "https://scikit-learn.org/stable/tutorial/",
    },
    {
        "name": "Data Scientist",
        "terms": ["data scientist", "data science"],
        "skills": ["Python", "SQL", "Statistics", "Pandas", "NumPy", "Data Visualization", "Machine Learning", "Scikit-learn"],
        "project": "Analyze a public dataset, explain the findings with charts, and document the limitations and conclusions.",
        "resource": "https://www.kaggle.com/learn",
    },
    {
        "name": "Data Analyst",
        "terms": ["data analyst", "business analyst", "analytics"],
        "skills": ["SQL", "Excel", "Statistics", "Data Analysis", "Data Visualization", "Power BI", "Tableau", "Python"],
        "project": "Create a small analytics dashboard from a public dataset and write five evidence-backed business insights.",
        "resource": "https://sqlbolt.com/",
    },
    {
        "name": "Frontend Developer",
        "terms": ["frontend", "front-end", "front end", "ui developer", "web designer"],
        "skills": ["HTML", "CSS", "JavaScript", "TypeScript", "React", "Git", "Testing"],
        "project": "Build a responsive multi-page web interface with accessible forms, validation and a clear README.",
        "resource": "https://developer.mozilla.org/en-US/docs/Learn",
    },
    {
        "name": "Backend Developer",
        "terms": ["backend", "back-end", "back end", "api developer"],
        "skills": ["Python", "Java", "SQL", "REST APIs", "Git", "Testing", "Docker", "Linux"],
        "project": "Build a documented REST API with input validation, database persistence and automated tests.",
        "resource": "https://fastapi.tiangolo.com/tutorial/",
    },
    {
        "name": "Full Stack Developer",
        "terms": ["full stack", "full-stack", "fullstack"],
        "skills": ["HTML", "CSS", "JavaScript", "React", "Node.js", "SQL", "REST APIs", "Git", "Testing"],
        "project": "Create a small full-stack application with authentication-ready structure, CRUD operations and deployment notes.",
        "resource": "https://developer.mozilla.org/en-US/docs/Learn",
    },
    {
        "name": "Cloud / DevOps Engineer",
        "terms": ["devops", "cloud engineer", "site reliability", "platform engineer"],
        "skills": ["Linux", "Networking", "Git", "AWS", "Docker", "Kubernetes", "CI/CD", "Terraform"],
        "project": "Containerize a small app and document a repeatable build-and-test pipeline.",
        "resource": "https://skillsbuild.org/",
    },
    {
        "name": "Cybersecurity Analyst",
        "terms": ["cybersecurity", "cyber security", "security analyst", "soc analyst"],
        "skills": ["Networking", "Linux", "Cybersecurity", "Testing", "Python"],
        "project": "Complete a legal beginner lab and write a defensive security report describing the findings and mitigations.",
        "resource": "https://tryhackme.com/",
    },
    {
        "name": "Mobile App Developer",
        "terms": ["mobile developer", "mobile app", "android developer", "flutter developer"],
        "skills": ["Flutter", "Dart", "Java", "REST APIs", "Git", "Testing", "SQL"],
        "project": "Build a small mobile app with form validation, local state, error handling and clear setup instructions.",
        "resource": "https://docs.flutter.dev/",
    },
    {
        "name": "Software Engineer",
        "terms": ["software engineer", "software developer", "software engineering", "programmer"],
        "skills": ["Data Structures and Algorithms", "Object-Oriented Programming", "Java", "Python", "SQL", "Git", "Testing", "REST APIs"],
        "project": "Build a complete, well-tested application and explain the design choices in a concise README.",
        "resource": "https://www.freecodecamp.org/learn/",
    },
]

RESOURCE_URLS = {
    "Python": ("Python Tutorial", "https://docs.python.org/3/tutorial/"),
    "Java": ("Dev.java Learning", "https://dev.java/learn/"),
    "JavaScript": ("MDN JavaScript Guide", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide"),
    "TypeScript": ("TypeScript Handbook", "https://www.typescriptlang.org/docs/"),
    "SQL": ("SQLBolt", "https://sqlbolt.com/"),
    "MySQL": ("MySQL Documentation", "https://dev.mysql.com/doc/"),
    "PostgreSQL": ("PostgreSQL Tutorial", "https://www.postgresql.org/docs/current/tutorial.html"),
    "HTML": ("MDN HTML", "https://developer.mozilla.org/en-US/docs/Learn/HTML"),
    "CSS": ("MDN CSS", "https://developer.mozilla.org/en-US/docs/Learn/CSS"),
    "React": ("React Documentation", "https://react.dev/learn"),
    "Node.js": ("Node.js Learn", "https://nodejs.org/en/learn"),
    "REST APIs": ("MDN HTTP", "https://developer.mozilla.org/en-US/docs/Web/HTTP"),
    "Git": ("Git Book", "https://git-scm.com/book/en/v2"),
    "AWS": ("AWS Skill Builder", "https://skillbuilder.aws/"),
    "Docker": ("Docker Get Started", "https://docs.docker.com/get-started/"),
    "Kubernetes": ("Kubernetes Basics", "https://kubernetes.io/docs/tutorials/kubernetes-basics/"),
    "Machine Learning": ("Google Machine Learning Crash Course", "https://developers.google.com/machine-learning/crash-course"),
    "Pandas": ("Pandas Getting Started", "https://pandas.pydata.org/docs/getting_started/"),
    "NumPy": ("NumPy Learn", "https://numpy.org/learn/"),
    "Scikit-learn": ("Scikit-learn Tutorials", "https://scikit-learn.org/stable/tutorial/"),
    "PyTorch": ("PyTorch Tutorials", "https://pytorch.org/tutorials/"),
    "Statistics": ("Khan Academy Statistics", "https://www.khanacademy.org/math/statistics-probability"),
    "Data Structures and Algorithms": ("VisuAlgo", "https://visualgo.net/en"),
    "Flutter": ("Flutter Documentation", "https://docs.flutter.dev/"),
    "Dart": ("Dart Language Tour", "https://dart.dev/language"),
    "Cybersecurity": ("TryHackMe", "https://tryhackme.com/"),
    "Networking": ("Cisco Skills for All", "https://skillsforall.com/"),
    "Excel": ("Microsoft Excel Help", "https://support.microsoft.com/excel"),
    "Power BI": ("Microsoft Learn Power BI", "https://learn.microsoft.com/en-us/training/powerplatform/power-bi"),
    "Tableau": ("Tableau Free Training", "https://www.tableau.com/learn/training"),
}
STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "are", "will",
    "you", "your", "our", "their", "into", "have", "has", "who", "what",
    "when", "where", "work", "working", "role", "team", "company", "job",
    "position", "candidate", "candidates", "required", "preferred", "ability",
    "experience", "skills", "skill", "build", "building", "using", "including",
}


def detect_language(text: str) -> str:
    text = str(text or "")
    visible = [char for char in text if char.strip()]
    hindi = sum(1 for char in visible if "\u0900" <= char <= "\u097F")
    return "hi" if visible and hindi / len(visible) > 0.15 else "en"


def extract_skills(text: str) -> list[str]:
    value = str(text or "")
    return [name for name, pattern in SKILL_PATTERNS if re.search(pattern, value, re.I)]


def _profile_for(text: str) -> dict[str, Any]:
    value = str(text or "").lower()
    for profile in ROLE_PROFILES:
        if any(term in value for term in profile["terms"]):
            return profile
    return ROLE_PROFILES[-1]


def _resources(skill: str) -> list[dict[str, str]]:
    title, url = RESOURCE_URLS.get(skill, ("Free learning search", "https://www.freecodecamp.org/learn/"))
    return [{"name": title, "url": url, "type": "official/free learning"}]


def _learning_time(skill: str) -> str:
    if skill in {"Machine Learning", "Deep Learning", "Cybersecurity", "Kubernetes", "System Design"}:
        return "3–6 weeks"
    if skill in {"Python", "Java", "JavaScript", "SQL", "Data Structures and Algorithms", "Statistics"}:
        return "2–4 weeks"
    return "1–3 weeks"


def _jd_skills(job_description: str) -> list[str]:
    found = extract_skills(job_description)
    if found:
        return found
    words = [word for word in re.findall(r"[A-Za-z][A-Za-z+#.-]{2,}", job_description)
             if word.lower() not in STOPWORDS]
    return list(dict.fromkeys(word.title() for word in words[:6]))


def _role_label(text: str) -> str:
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    head = " ".join(lines[:3])[:260].lower()
    for profile in ROLE_PROFILES:
        if any(term in head for term in profile["terms"]):
            return profile["name"]
    # When no clear job title is present, use the first non-generic line.
    if lines and len(lines[0]) <= 90 and not any(
        marker in lines[0].lower() for marker in ("we are looking", "job description", "responsibilities", "requirements")
    ):
        return lines[0].rstrip(".:")
    return "the advertised role"


def analyze_skill_gaps(resume_text: str, job_description: str) -> dict[str, Any]:
    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(job_description)
    if not jd_skills:
        jd_skills = _jd_skills(job_description)
    matched = [skill for skill in jd_skills if skill in resume_skills]
    missing = [skill for skill in jd_skills if skill not in resume_skills]
    gaps = [{
        "skill": skill,
        "importance": "high" if index < 3 else "medium",
        "reason": "Mentioned in the job description but not detected in the supplied resume text.",
        "learning_time": _learning_time(skill),
        "free_resources": _resources(skill),
    } for index, skill in enumerate(missing[:8])]
    role_profile = _profile_for(job_description)
    nice_to_have = [{
        "skill": skill,
        "free_resources": _resources(skill),
    } for skill in role_profile["skills"] if skill not in jd_skills and skill not in resume_skills][:4]
    planned = (missing or jd_skills or role_profile["skills"])[:4]
    roadmap = []
    for index, skill in enumerate(planned, 1):
        title, url = RESOURCE_URLS.get(skill, ("Free learning search", "https://www.freecodecamp.org/learn/"))
        roadmap.append({
            "week": index,
            "focus": f"Learn and practise {skill}",
            "resources": [title + " — " + url],
            "milestone": f"Complete a small exercise demonstrating {skill}.",
        })
    if not roadmap:
        roadmap = [{
            "week": 1,
            "focus": "Review the role requirements",
            "resources": ["https://www.freecodecamp.org/learn/"],
            "milestone": "Choose one required skill and complete a beginner exercise.",
        }]
    quick_wins = [
        f"Practise {missing[0]} with a small, verifiable project." if missing else "Keep the skills section aligned with the job description.",
        "Use project bullets to show what you personally built, tested or analysed.",
        "Add only skills you can explain and demonstrate in an interview.",
    ]
    return {
        "critical_gaps": gaps,
        "nice_to_have_gaps": nice_to_have,
        "learning_roadmap": roadmap,
        "quick_wins": quick_wins,
        "career_advice": (
            f"Detected {len(matched)} matching skill(s) and {len(missing)} potential gap(s). "
            "This is a keyword-based estimate, so review the job description and resume carefully. "
            "A missing keyword does not necessarily mean you lack the skill."
        ),
        "matched_skills": matched,
        "language": detect_language(resume_text + " " + job_description),
    }


def generate_cover_letter(resume_text: str, job_description: str, user_name: str = "Applicant") -> dict[str, Any]:
    name = (str(user_name or "").strip() or "Applicant")[:100]
    role = _role_label(job_description)
    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(job_description)
    overlap = [skill for skill in job_skills if skill in resume_skills]
    if overlap:
        evidence = "My resume reflects learning or experience in " + ", ".join(overlap[:5]) + "."
    elif resume_skills:
        evidence = (
            "My current skill set includes " + ", ".join(resume_skills[:5]) +
            ", and I am keen to apply these skills while learning the tools and practices used by your team."
        )
    else:
        relevant = ", ".join(job_skills[:4]) if job_skills else "the skills described in the job posting"
        evidence = (
            f"I am motivated to strengthen my foundation in {relevant} and contribute through careful work, "
            "consistent learning and collaboration. I would welcome the opportunity to discuss how my background "
            "and goals fit the role."
        )
    letter = (
        "Dear Hiring Manager,\n\n"
        f"I am writing to apply for the {role} position. I am interested in the opportunity to contribute to "
        "your team and continue developing practical, role-relevant skills.\n\n"
        f"{evidence} I value clear communication, thoughtful problem-solving and being honest about the work "
        "I have completed and the areas I am continuing to learn.\n\n"
        "I would be glad to discuss how my background, projects and willingness to learn align with your needs. "
        "Thank you for considering my application.\n\n"
        f"Sincerely,\n{name}"
    )
    return {
        "cover_letter": letter,
        "word_count": len(letter.split()),
        "language": detect_language(str(resume_text or "") + " " + str(job_description or "")),
    }


def generate_interview_questions(job_description: str, resume_text: str = "") -> dict[str, Any]:
    skills = extract_skills(job_description)
    if not skills:
        skills = _profile_for(job_description)["skills"][:5]
    technical = [{
        "question": f"Explain a project or exercise where you used {skill}. What did you do, and how did you check that it worked?",
        "expected_answer_points": [
            f"Explain the basic purpose of {skill}.",
            "Describe your own steps or decisions.",
            "Mention how you tested the result and what you learned.",
        ],
        "difficulty": "beginner" if index < 2 else "medium",
    } for index, skill in enumerate(skills[:6])]
    behavioral = [
        {
            "question": "Tell me about a time you had to learn something unfamiliar to finish a task.",
            "why_asked": "Assesses learning approach and adaptability.",
            "sample_answer_framework": "Use STAR: situation, task, actions you personally took, and the truthful result.",
            "tip": "Choose a real college, project or work example.",
        },
        {
            "question": "Describe a mistake or problem you found in a project. How did you respond?",
            "why_asked": "Assesses ownership and problem-solving.",
            "sample_answer_framework": "Explain the issue, how you investigated it, what you changed and what you learned.",
            "tip": "Be honest; do not invent metrics or outcomes.",
        },
        {
            "question": "How do you manage a task when the requirements are unclear?",
            "why_asked": "Assesses communication and planning.",
            "sample_answer_framework": "Explain how you clarify the goal, split the task and confirm assumptions.",
            "tip": "Give a concrete example.",
        },
    ]
    situational = [{
        "question": f"If a task involving {skills[0]} failed shortly before a deadline, how would you investigate it?",
        "ideal_approach": "Reproduce the issue, check logs or inputs, isolate the cause, test a small fix, and communicate the status.",
    }]
    return {
        "behavioral_questions": behavioral,
        "technical_questions": technical,
        "situational_questions": situational,
        "questions_to_ask_interviewer": [
            "What would a successful first month look like in this role?",
            "Which tools and practices does the team use most often?",
            "How are code reviews, feedback and learning supported for interns or new team members?",
        ],
        "preparation_checklist": [
            f"Review the fundamentals of {', '.join(skills[:4])}.",
            "Prepare two real project examples and clearly explain your individual contribution.",
            "Practise explaining your approach, tests, limitations and lessons learned.",
            "Read the job description again and prepare questions about the team's work.",
        ],
        "language": detect_language(job_description + " " + str(resume_text or "")),
    }


def generate_career_roadmap(resume_text: str, target_role: str) -> dict[str, Any]:
    target = str(target_role or "").strip()
    profile = _profile_for(target)
    skills = profile["skills"]
    current_skills = extract_skills(resume_text)
    priority = [skill for skill in skills if skill not in current_skills]
    focus = (priority + [skill for skill in skills if skill in current_skills])[:8]
    phase_one = focus[:3] or skills[:3]
    phase_two = focus[3:6] or skills[3:6]
    phase_three = focus[6:8] or skills[6:8]
    phases = [
        {
            "phase": "Phase 1: Build the foundations",
            "duration": "Weeks 1–4",
            "goals": ["Learn core concepts and practise consistently.", "Solve small exercises and record what you learn."],
            "skills_to_build": phase_one,
            "certifications": [],
            "projects_to_build": ["Complete two small exercises and publish clean notes or code."],
            "milestone": "Explain the core concepts and demonstrate them in a small working example.",
        },
        {
            "phase": "Phase 2: Apply the skills",
            "duration": "Weeks 5–8",
            "goals": ["Combine skills in a realistic task.", "Add input validation, tests and documentation."],
            "skills_to_build": phase_two,
            "certifications": [],
            "projects_to_build": [profile["project"]],
            "milestone": "Publish a working project with a README, screenshots or a short demo.",
        },
        {
            "phase": "Phase 3: Prepare for applications",
            "duration": "Weeks 9–12",
            "goals": ["Practise role-specific interview questions.", "Refine resume and portfolio using evidence from projects."],
            "skills_to_build": phase_three,
            "certifications": [],
            "projects_to_build": ["Polish the strongest project and prepare a two-minute explanation."],
            "milestone": "Have a role-focused resume, a demonstrable project and interview examples ready.",
        },
    ]
    return {
        "current_level": "Based on supplied text: " + (", ".join(current_skills[:5]) if current_skills else "not enough skills detected yet"),
        "target_level": "Entry-level readiness for " + target,
        "estimated_timeline": "12 weeks at a consistent study pace",
        "roadmap_phases": phases,
        "internship_opportunities": [{
            "type": target + " internship or entry-level role",
            "companies_to_target": [],
            "how_to_apply": "Use official company career pages and verified internship boards; check eligibility and deadlines before applying.",
        }],
        "networking_strategy": [
            "Keep GitHub repositories readable with setup steps and honest project descriptions.",
            "Ask for feedback on one project from a classmate, mentor or developer community.",
            "Track applications and follow up politely when the employer's process allows it.",
        ],
        "salary_range": {},
        "motivational_note": "Use this as a practical starting plan. Adjust the pace to your semester workload, and list a skill as mastered only when you can demonstrate it.",
        "resources": [{"name": profile["name"] + " learning resource", "url": profile["resource"]}],
        "language": detect_language(str(resume_text or "")),
    }


def improve_resume_bullets(resume_text: str, job_description: str = "") -> dict[str, Any]:
    raw_lines = [part.strip(" \t•●▪-") for part in re.split(r"[\r\n]+", str(resume_text or "")) if part.strip()]
    if len(raw_lines) <= 1 and raw_lines:
        raw_lines = [part.strip() for part in re.split(r"(?<=[.!?])\s+", raw_lines[0]) if part.strip()]
    headings = {
        "resume", "education", "skills", "technical skills", "projects",
        "experience", "work experience", "certifications", "certificates",
        "summary", "objective", "contact", "languages",
    }
    lines = [line for line in raw_lines if line.lower().rstrip(":") not in headings and len(line) >= 12][:8]
    improved = []
    actions = [
        ("worked on ", "Contributed to "),
        ("helped ", "Supported "),
        ("responsible for ", "Handled "),
        ("did ", "Completed "),
        ("made ", "Created "),
        ("used ", "Applied "),
        ("participated in ", "Contributed to "),
    ]
    strong_starts = (
        "built ", "developed ", "designed ", "implemented ", "created ", "analysed ",
        "analyzed ", "improved ", "tested ", "led ", "automated ", "deployed ",
        "documented ", "maintained ", "researched ", "engineered ", "configured ",
    )
    for line in lines:
        original = line
        normalized = line[0].upper() + line[1:]
        lower = line.lower()
        rewritten = normalized
        for weak, strong in actions:
            if lower.startswith(weak):
                rewritten = strong + line[len(weak):]
                break
        else:
            if not lower.startswith(strong_starts):
                rewritten = "Developed " + line[0].lower() + line[1:]
        rewritten = rewritten.rstrip(".") + "."
        improved.append({
            "original": original,
            "improved": rewritten,
            "improvement_reason": "Uses clearer action language while preserving the original meaning and avoiding invented metrics.",
        })
    return {
        "improved_bullets": improved,
        "general_tips": [
            "Start each bullet with a precise action verb.",
            "Name the tools you actually used and explain what you delivered.",
            "Add numbers only when you can verify them from your work.",
            "Align wording to the job description without claiming skills you do not have.",
        ],
        "professional_english_phrases": {
            "instead_of": "Worked on a project",
            "use": "Contributed to a project by describing the specific work completed",
        },
        "language": detect_language(resume_text),
    }


def chat_with_agent(user_message: str, session_context: str = "", resume_text: str = "") -> dict[str, Any]:
    message = str(user_message or "").strip()
    lower = message.lower()
    resume_skills = extract_skills(resume_text)
    if any(word in lower for word in ("interview", "question", "prepare")):
        response = "Start with the job description. Practise explaining two real projects, your individual contribution, the decisions you made, and how you tested the results. Avoid memorised claims or metrics you cannot verify."
    elif any(word in lower for word in ("resume", "cv", "ats")):
        response = "Use standard resume headings, mirror relevant keywords from the role only when accurate, and write project bullets with an action, the work you did, the tools used, and the result. Do not add invented numbers."
    elif any(word in lower for word in ("skill", "learn", "roadmap", "study")):
        response = "Choose one target role, identify the three most important skills in its job descriptions, study one at a time, and build a small project that demonstrates each skill. Review your progress weekly."
    elif any(word in lower for word in ("internship", "apply", "job")):
        response = "Tailor your resume to the specific role, check eligibility and deadlines on the official employer page, and keep a simple tracker for applications and follow-ups."
    else:
        response = "I can help you plan your career with rule-based guidance. Share your target role, current skills and the task you are working on, and I will suggest practical next steps."
    if resume_skills:
        response += "\n\nSkills detected in your supplied resume text: " + ", ".join(resume_skills[:8]) + ". Verify this list before using it in an application."
    return {"response": response, "language": detect_language(message)}


def enrich_ats_result(resume_text: str, job_description: str, result: dict[str, Any]) -> dict[str, Any]:
    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(job_description)
    matched = [skill for skill in job_skills if skill in resume_skills]
    missing = [skill for skill in job_skills if skill not in resume_skills]
    result["matched_skills"] = matched[:15]
    result["missing_skills"] = missing[:15]
    result["top_strengths"] = [f"Resume text includes {skill}." for skill in matched[:5]]
    result["improvement_actions"] = [
        f"Practise {skill} and add a project example if you can demonstrate it."
        for skill in missing[:5]
    ]
    if not result["top_strengths"]:
        result["top_strengths"] = ["The resume was checked against the supplied job description using local keyword rules."]
    if not result["improvement_actions"]:
        result["improvement_actions"] = [
            "Keep project descriptions specific and truthful.",
            "Review the job description for required skills not represented in the supplied resume text.",
        ]
    result["role_fit_summary"] = (
        f"Rule-based comparison found {len(matched)} matching skill(s) and {len(missing)} potential gap(s). "
        "Review the evidence manually; keyword matching cannot judge skill depth or overall suitability."
    )
    result["language"] = detect_language(resume_text + " " + job_description)
    return result

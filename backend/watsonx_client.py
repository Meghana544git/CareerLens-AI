"""
CareerLens AI — IBM watsonx.ai Client
Handles all communication with Granite models via the watsonx.ai SDK.
"""

import os
import json
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class WatsonxClient:
    """
    Wrapper around IBM watsonx.ai ModelInference API.
    Supports text generation with Granite models.
    """

    def __init__(self):
        self.api_key = os.getenv("IBM_API_KEY")
        self.project_id = os.getenv("IBM_PROJECT_ID")
        self.region = os.getenv("IBM_REGION", "us-south")
        self.model_primary = os.getenv("GRANITE_MODEL_PRIMARY", "ibm/granite-3-8b-instruct")
        self.model_fast = os.getenv("GRANITE_MODEL_FAST", "ibm/granite-3-2b-instruct")
        self._client = None
        self._initialized = False
        self._init_client()

    def _init_client(self):
        """Initialize the watsonx.ai client."""
        if not self.api_key or not self.project_id:
            logger.warning(
                "IBM_API_KEY or IBM_PROJECT_ID not set. "
                "Using mock responses for development."
            )
            self._initialized = False
            return

        try:
            from ibm_watsonx_ai import APIClient, Credentials
            from ibm_watsonx_ai.foundation_models import ModelInference

            self._Credentials = Credentials
            self._ModelInference = ModelInference
            self._initialized = True
            logger.info(f"✅ watsonx.ai client initialized — region: {self.region}")
        except ImportError as e:
            logger.error(f"ibm-watsonx-ai SDK not installed: {e}")
            self._initialized = False

    def _get_model(self, use_fast: bool = False):
        """Create a ModelInference instance for the selected model."""
        from ibm_watsonx_ai import Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference

        url_map = {
            "us-south": "https://us-south.ml.cloud.ibm.com",
            "eu-de":    "https://eu-de.ml.cloud.ibm.com",
            "eu-gb":    "https://eu-gb.ml.cloud.ibm.com",
            "jp-tok":   "https://jp-tok.ml.cloud.ibm.com",
            "au-syd":   "https://au-syd.ml.cloud.ibm.com",
        }
        url = url_map.get(self.region, "https://us-south.ml.cloud.ibm.com")
        model_id = self.model_fast if use_fast else self.model_primary

        return ModelInference(
            model_id=model_id,
            credentials=Credentials(api_key=self.api_key, url=url),
            project_id=self.project_id,
        )

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 2048,
        temperature: float = 0.3,
        use_fast_model: bool = False,
        expect_json: bool = False,
    ) -> str:
        """
        Send a prompt to Granite and return the generated text.
        Falls back to mock response if credentials are not configured.
        """
        if not self._initialized:
            return self._mock_response(prompt, expect_json)

        try:
            model = self._get_model(use_fast=use_fast_model)

            params = {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "repetition_penalty": 1.1,
                "stop_sequences": ["</s>", "<|endoftext|>"],
            }
            if expect_json:
                params["temperature"] = 0.1  # More deterministic for JSON

            result = model.generate_text(prompt=prompt, params=params)
            return result.strip() if result else ""

        except Exception as e:
            logger.error(f"watsonx.ai generation error: {e}")
            return self._mock_response(prompt, expect_json)

    def generate_json(self, prompt: str, max_new_tokens: int = 2048) -> dict:
        """
        Generate text and parse it as JSON.
        Handles common JSON formatting issues from LLM output.
        """
        raw = self.generate(prompt, max_new_tokens=max_new_tokens, expect_json=True)
        return self._parse_json_safe(raw)

    @staticmethod
    def _parse_json_safe(text: str) -> dict:
        """Robustly extract JSON from LLM output."""
        if not text:
            return {}
        # Strip markdown code blocks if present
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last ``` lines
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        # Find the first { and last }
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
        # Try array too
        start = text.find("[")
        end = text.rfind("]") + 1
        if start != -1 and end > start:
            try:
                return {"data": json.loads(text[start:end])}
            except json.JSONDecodeError:
                pass
        logger.warning("Could not parse JSON from model output")
        return {"raw_response": text}

    # ─────────────────────────────────────────────────────────────────────────
    # Mock responses for development (when credentials not configured)
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _mock_response(prompt: str, expect_json: bool) -> str:
        """Return realistic mock data when watsonx is not configured."""
        prompt_lower = prompt.lower()

        # Chat takes priority — identified by the "User:" turn format
        if "user:" in prompt_lower and "careerlens ai" in prompt_lower and "score_breakdown" not in prompt_lower:
            return (
                "Great question! ATS (Applicant Tracking System) is software that companies use to filter resumes before a human reads them. "
                "Here's how to improve your ATS score:\n\n"
                "**1. Use exact keywords from the job description** — copy the exact terms they use (e.g. 'Python' not 'py').\n"
                "**2. Use standard section headings** — Experience, Education, Skills, Projects.\n"
                "**3. Quantify your achievements** — '↑ model accuracy by 15%' beats 'improved model accuracy'.\n"
                "**4. Avoid tables and graphics** — ATS can't read them.\n"
                "**5. Use strong action verbs** — Developed, Built, Designed, Led, Optimized.\n\n"
                "Upload your resume and paste a job description in the **ATS Analyzer** section to get your exact score with a detailed breakdown!"
            )

        if "score_breakdown" in prompt_lower or ("analyze this resume" in prompt_lower and "ats" in prompt_lower):
            return json.dumps({
                "ats_score": 72,
                "score_breakdown": {
                    "keyword_match": 70, "skills_coverage": 75,
                    "experience_relevance": 65, "education_match": 80, "resume_quality": 70
                },
                "matched_skills": ["Python", "SQL", "Machine Learning", "Data Analysis", "Git"],
                "missing_keywords": ["Kubernetes", "Spark", "Airflow", "Tableau"],
                "weak_skills": ["System Design", "Cloud Architecture"],
                "role_fit_summary": "Strong candidate with solid Python and ML foundation. Needs to develop cloud and big data skills to be highly competitive for this senior role.",
                "top_strengths": [
                    "Strong Python programming skills", "Relevant ML project experience",
                    "Good educational background", "SQL proficiency demonstrated"
                ],
                "improvement_actions": [
                    "Add Kubernetes to your skill set — take a free course on KodeKloud",
                    "Include quantified results: 'Improved model accuracy by X%'",
                    "Add Apache Spark or PySpark experience",
                    "Get a cloud certification (AWS/GCP/Azure)"
                ],
                "resume_bullet_rewrites": [
                    {"original": "Built a machine learning model", "improved": "Developed and deployed a classification model achieving 94% accuracy, reducing false positives by 23%"},
                    {"original": "Worked on data analysis", "improved": "Analyzed 50K+ customer records using Python (Pandas, NumPy), uncovering insights that reduced churn by 12%"}
                ],
                "overall_verdict": "Good Match — Minor tweaks recommended."
            })

        if "cover_letter" in prompt_lower or "cover letter" in prompt_lower:
            return """Dear Hiring Manager,

I am writing to express my strong interest in the Data Scientist position at your organization. With a solid foundation in Python, machine learning, and data analysis — backed by hands-on project experience delivering measurable results — I am confident I can make an immediate contribution to your team.

In my recent projects, I developed end-to-end ML pipelines processing over 50,000 data points, achieving 94% model accuracy and directly reducing operational costs by 15%. My experience with Python, scikit-learn, and SQL aligns directly with the technical requirements outlined in your job description. Beyond technical skills, I bring a strong analytical mindset and a track record of translating complex data into clear, actionable business insights.

What excites me most about this role is the opportunity to work on real-world problems at scale. Your team's commitment to data-driven decision making resonates deeply with my professional philosophy — I believe the best data science work happens at the intersection of rigorous analysis and practical business impact.

I would welcome the opportunity to discuss how my background aligns with your team's needs. Thank you for your time and consideration.

Best regards,
[Your Name]"""

        if "interview" in prompt_lower or "behavioral_questions" in prompt_lower:
            return json.dumps({
                "behavioral_questions": [
                    {"question": "Tell me about a time you had to learn a new technology quickly.", "why_asked": "Assessing learning agility", "sample_answer_framework": "Use STAR: describe a challenging deadline, the tech you learned, and the outcome.", "tip": "Prepare 2-3 examples of rapid learning."},
                    {"question": "Describe a project where you had to handle messy or incomplete data.", "why_asked": "Assessing data engineering skills", "sample_answer_framework": "Explain your data cleaning approach and how it impacted results.", "tip": "Quantify the improvement."}
                ],
                "technical_questions": [
                    {"question": "Explain the bias-variance tradeoff.", "expected_answer_points": ["High bias = underfitting", "High variance = overfitting", "Goal is balanced model"], "difficulty": "medium"},
                    {"question": "How would you handle class imbalance in a dataset?", "expected_answer_points": ["Oversampling (SMOTE)", "Undersampling", "Class weights", "Evaluation with F1/AUC-ROC"], "difficulty": "medium"}
                ],
                "situational_questions": [
                    {"question": "If your model's accuracy drops in production, what steps do you take?", "ideal_approach": "Mention data drift detection, model monitoring, retraining pipeline, and stakeholder communication."}
                ],
                "questions_to_ask_interviewer": [
                    "What does the ML infrastructure look like, and what are the biggest scaling challenges?",
                    "How does the data science team collaborate with product and engineering?"
                ],
                "preparation_checklist": ["Review ML fundamentals (bias-variance, regularization)", "Prepare 5 STAR stories", "Research the company's data products", "Practice coding on LeetCode (medium SQL + Python)"]
            })

        if "skill_gap" in prompt_lower or "learning_roadmap" in prompt_lower:
            return json.dumps({
                "critical_gaps": [
                    {"skill": "Apache Spark", "importance": "high", "reason": "Required for large-scale data processing mentioned in JD", "learning_time": "3-4 weeks", "free_resources": [{"name": "Spark by Example", "url": "https://sparkbyexamples.com", "type": "tutorial"}]},
                    {"skill": "Cloud Platforms (AWS/GCP)", "importance": "high", "reason": "Job requires deploying models to cloud", "learning_time": "4-6 weeks", "free_resources": [{"name": "AWS Free Tier", "url": "https://aws.amazon.com/free/", "type": "practice"}]}
                ],
                "nice_to_have_gaps": [
                    {"skill": "Tableau", "free_resources": [{"name": "Tableau Public", "url": "https://public.tableau.com", "type": "practice"}]}
                ],
                "learning_roadmap": [
                    {"week": 1, "focus": "Python Advanced + Pandas", "resources": ["Real Python", "Kaggle Pandas Course"], "milestone": "Comfortable with advanced data manipulation"},
                    {"week": 2, "focus": "Apache Spark basics", "resources": ["Databricks free courses"], "milestone": "Can run Spark jobs locally"},
                    {"week": 3, "focus": "Cloud fundamentals", "resources": ["AWS Cloud Practitioner Essentials"], "milestone": "Understand cloud deployment basics"},
                    {"week": 4, "focus": "Build a project combining all", "resources": ["Personal project + GitHub"], "milestone": "Portfolio-ready project deployed on cloud"}
                ],
                "quick_wins": ["Add Apache Spark to LinkedIn skills", "Complete Kaggle ML course this week", "Get AWS Cloud Practitioner cert (free practice exam available)"],
                "career_advice": "You have a strong foundation — the gap is primarily cloud and big data tooling. Invest 4 focused weeks and you'll be highly competitive for senior roles."
            })

        if "roadmap" in prompt_lower or "roadmap_phases" in prompt_lower:
            return json.dumps({
                "current_level": "Junior / Entry-level",
                "target_level": "Mid-level Data Scientist",
                "estimated_timeline": "8-12 months",
                "roadmap_phases": [
                    {"phase": "Phase 1: Foundation", "duration": "0-3 months", "goals": ["Master Python data stack", "Complete 2 Kaggle competitions"], "skills_to_build": ["Pandas", "NumPy", "Scikit-learn"], "certifications": ["IBM Data Science Certificate"], "projects_to_build": ["End-to-end ML pipeline on Kaggle dataset"], "milestone": "First GitHub portfolio project live"},
                    {"phase": "Phase 2: Cloud & Scale", "duration": "3-6 months", "goals": ["Deploy a model to production", "Learn SQL at advanced level"], "skills_to_build": ["AWS SageMaker", "SQL", "Docker"], "certifications": ["AWS Cloud Practitioner"], "projects_to_build": ["Deployed API serving an ML model"], "milestone": "Live deployed project in portfolio"},
                    {"phase": "Phase 3: Job Search", "duration": "6-9 months", "goals": ["Apply to 10 targeted roles/week", "Ace technical interviews"], "skills_to_build": ["System design basics", "LeetCode Medium"], "certifications": [], "projects_to_build": ["Domain-specific project in target industry"], "milestone": "First Data Scientist offer"}
                ],
                "internship_opportunities": [
                    {"type": "Summer Data Science Internship", "companies_to_target": ["IBM", "Microsoft", "startups via AngelList"], "how_to_apply": "Apply via LinkedIn and company portals in Nov-Feb for summer internships"}
                ],
                "networking_strategy": ["Comment on 5 LinkedIn data science posts per week", "Join local data science meetups on Meetup.com", "Contribute to open source ML libraries"],
                "salary_range": {"entry": "₹5-10 LPA / $60-90K", "experienced": "₹12-25 LPA / $110-160K"},
                "motivational_note": "You're already halfway there. The skills gap is real but very bridgeable — many successful data scientists followed this exact path. Stay consistent, build in public, and opportunities will come."
            })

        # Default chat response
        return (
            "I'm CareerLens AI, your career coach! I can help you with resume analysis, "
            "ATS optimization, cover letters, interview prep, skill gap analysis, and career roadmaps. "
            "Upload your resume and paste a job description to get started with a full analysis!"
        )


# Singleton instance
_client: Optional[WatsonxClient] = None


def get_watsonx_client() -> WatsonxClient:
    """Get or create the singleton WatsonxClient instance."""
    global _client
    if _client is None:
        _client = WatsonxClient()
    return _client

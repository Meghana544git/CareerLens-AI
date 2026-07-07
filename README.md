# CareerLens AI 🚀
### AI-Powered Career Coach — IBM watsonx.ai × Granite
[![WebLink](https://web-production-6a332.up.railway.app/)

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green)](https://flask.palletsprojects.com)
[![IBM watsonx.ai](https://img.shields.io/badge/IBM-watsonx.ai-1261FE)](https://www.ibm.com/products/watsonx-ai)
[![Granite](https://img.shields.io/badge/Granite-3--8B--Instruct-purple)](https://www.ibm.com/granite)

A fully-featured, production-ready AI career assistant that helps students and job seekers with:
- **ATS Resume Scoring** (0–100 with breakdown)
- **Cover Letter Generation** (personalized to every JD)
- **Interview Question Prediction** (behavioral + technical + situational)
- **Skill Gap Analysis** with free learning resource links
- **Career Roadmap** (phased plan to your target role)
- **Internship Fit Analyzer** (fresher-friendly scoring)
- **Multi-Job Comparison** (compare up to 5 JDs)
- **AI Career Coach Chat** (English + Hindi support)
- **Resume Bullet Rewriter** (action verbs + quantification)

---

## 📁 Project Structure

```
CareerLensAI/
├── app.py                      # Flask main app + all API routes
├── wsgi.py                     # Gunicorn entry point
├── agent_instructions.py       # ⭐ ALL AI behavior config (edit this!)
├── requirements.txt
├── Procfile                    # IBM Cloud / Heroku deployment
├── manifest.yml                # IBM Cloud Foundry manifest
├── runtime.txt
├── .env.sample                 # → copy to .env and fill in
├── .gitignore
│
├── backend/
│   ├── __init__.py
│   ├── watsonx_client.py       # IBM watsonx.ai / Granite integration
│   ├── resume_parser.py        # PDF, DOCX, TXT parsing
│   ├── ats_analyzer.py         # ATS scoring engine (rule-based + AI blend)
│   ├── career_tools.py         # All AI feature orchestration
│   └── models.py               # SQLAlchemy database models
│
├── frontend/
│   ├── templates/
│   │   └── index.html          # Single-page app template
│   └── static/
│       ├── css/main.css        # Dark-mode premium design
│       └── js/app.js           # Full client-side logic
│
├── uploads/                    # Uploaded resumes (auto-created)
└── database/                   # SQLite DB location
```

---

## ⚡ Quick Start (Local)

### 1. Clone / Download

```bash
cd CareerLensAI
```

### 2. Create Virtual Environment

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note:** spaCy model download (optional, for enhanced parsing):
> ```bash
> python -m spacy download en_core_web_sm
> ```

### 4. Configure Environment

```bash
cp .env.sample .env
```

Edit `.env` with your credentials:
```env
IBM_API_KEY=your_ibm_cloud_api_key
IBM_PROJECT_ID=your_watsonx_project_id
IBM_REGION=us-south
FLASK_SECRET_KEY=any_long_random_string_here
```

> **Get IBM Credentials:**
> 1. Go to [IBM Cloud](https://cloud.ibm.com) → Create a free account
> 2. Create a **watsonx.ai** service instance
> 3. Go to **Manage → API Keys** → Create a new key
> 4. In watsonx.ai, create a new **Project** → Copy the Project ID

### 5. Run the App

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

> **Without IBM credentials:** The app runs in demo mode with realistic mock responses so you can explore all features immediately!

---

## 🧠 Customizing the AI Agent

All AI behavior is controlled by [`agent_instructions.py`](agent_instructions.py). Edit it to customize:

```python
# 1. Change agent personality
AGENT_PERSONA = {
    "tone": "formal and strict",  # or "casual and friendly"
    ...
}

# 2. Adjust ATS scoring weights
ATS_SCORING_WEIGHTS = {
    "keyword_match":   0.40,   # Increase keyword importance
    "skills_coverage": 0.30,
    ...
}

# 3. Add career domains
CAREER_DOMAINS["blockchain"] = {
    "keywords": ["solidity", "ethereum", "web3", "defi", "smart contracts"],
    ...
}

# 4. Edit prompt templates
def get_ats_analysis_prompt(resume_text, job_description, language):
    return f"""Your custom prompt here..."""
```

---

## 🔌 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `POST /api/resume/upload` | multipart | Upload PDF/DOCX/TXT resume |
| `POST /api/ats/analyze` | JSON | Full ATS analysis |
| `POST /api/cover-letter/generate` | JSON | Generate cover letter |
| `POST /api/interview/questions` | JSON | Predict interview questions |
| `POST /api/skills/gap` | JSON | Skill gap + learning roadmap |
| `POST /api/roadmap/generate` | JSON | Career roadmap |
| `POST /api/internship/fit` | JSON | Internship fit score |
| `POST /api/resume/improve` | JSON | Bullet point rewrites |
| `POST /api/jobs/compare` | JSON | Multi-job comparison |
| `POST /api/jobs/save` | JSON | Save a target job |
| `GET /api/jobs/saved` | — | List saved jobs |
| `POST /api/chat` | JSON | AI career coach chat |
| `GET /api/chat/history` | — | Chat history |
| `GET /api/session/stats` | — | Dashboard statistics |
| `GET /health` | — | Health check |

### Example: ATS Analysis

```bash
curl -X POST http://localhost:5000/api/ats/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "We are looking for a Python developer...",
    "job_title": "Backend Engineer",
    "company_name": "TechCorp"
  }'
```

---

## ☁️ Deploy to IBM Cloud (Cloud Foundry)

### Prerequisites
```bash
# Install IBM Cloud CLI
# https://cloud.ibm.com/docs/cli?topic=cli-install-ibmcloud-cli

ibmcloud login
ibmcloud target --cf
```

### Set Environment Variables
```bash
ibmcloud cf set-env careerlens-ai IBM_API_KEY "your_key"
ibmcloud cf set-env careerlens-ai IBM_PROJECT_ID "your_project_id"
ibmcloud cf set-env careerlens-ai FLASK_SECRET_KEY "your_secret"
ibmcloud cf set-env careerlens-ai IBM_REGION "us-south"
ibmcloud cf set-env careerlens-ai DATABASE_URL "sqlite:///careerlens.db"
```

### Push the App
```bash
ibmcloud cf push
```

The app will be live at `https://careerlens-ai.us-south.cf.appdomain.cloud`

---

## ☁️ Deploy to IBM Code Engine (Container)

```bash
# Build and push
docker build -t careerlens-ai .
ibmcloud ce application create \
  --name careerlens-ai \
  --image us.icr.io/your_namespace/careerlens-ai \
  --env IBM_API_KEY=your_key \
  --env IBM_PROJECT_ID=your_project_id \
  --port 5000
```

---

## 🐳 Docker

```bash
docker build -t careerlens-ai .
docker run -p 5000:5000 \
  -e IBM_API_KEY=your_key \
  -e IBM_PROJECT_ID=your_project_id \
  careerlens-ai
```

**Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:5000", "--workers", "2"]
```

---

## 🌐 Features In Detail

### ATS Scoring Algorithm
The score is computed by blending **IBM Granite AI analysis (60%)** with **rule-based analysis (40%)**:

| Component | Weight | What it measures |
|---|---|---|
| Keyword Match | 35% | JD keywords found in resume |
| Skills Coverage | 25% | Technical skill overlap |
| Experience Relevance | 15% | Years + domain alignment |
| Education Match | 10% | Degree level + field |
| Resume Quality | 10% | Structure, verbs, quantification |
| Bonus Points | +1 to +14 | Metrics, GitHub, certifications |

### Language Support
- Automatically detects if user writes in **Hindi** and responds in Hindi
- Professional terms (ATS, resume, keywords) kept in English
- Bilingual support in the chat assistant

### Mock Mode (No IBM Credentials)
The app works fully without IBM credentials — realistic mock responses are returned for all features, perfect for demos and development.

---

## 🔧 Configuration Reference

| `.env` Variable | Default | Description |
|---|---|---|
| `IBM_API_KEY` | — | IBM Cloud API Key (required for real AI) |
| `IBM_PROJECT_ID` | — | watsonx.ai Project ID |
| `IBM_REGION` | `us-south` | IBM Cloud region |
| `GRANITE_MODEL_PRIMARY` | `ibm/granite-3-8b-instruct` | Main model for complex tasks |
| `GRANITE_MODEL_FAST` | `ibm/granite-3-2b-instruct` | Fast model for scoring |
| `FLASK_SECRET_KEY` | random | Session encryption key |
| `MAX_UPLOAD_MB` | `10` | Max resume file size |
| `DATABASE_URL` | SQLite | Database connection string |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Edit `agent_instructions.py` to customize AI behavior
4. Test thoroughly
5. Submit a pull request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **IBM watsonx.ai** — Granite foundation models
- **IBM SkillsBuild** — Career resources integration
- **Bootstrap 5** — UI framework
- **Flask** — Python web framework

---

*Built with ❤️ using IBM watsonx.ai and Granite AI*

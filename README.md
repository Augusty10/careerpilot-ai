# 🚀 CareerPilot AI

### One Profile. Multiple Careers. Smarter Applications.

CareerPilot AI is an AI-powered career platform designed specifically for freshers and recent graduates. It simplifies the entire entry-level job search journey: candidates maintain one master career profile, generate tailored role-specific resumes, discover verified fresher opportunities, and submit smarter applications coordinated with AI agents.

---

## 📦 Module 1: User Registration & Authentication (Complete)

- **Registration & Login**: Bcrypt salted password hashing, JWT access token authentication, duplicate email prevention.
- **Protected Sessions**: Reusable `@token_required` decorator attaching the current user to requests.
- **Account Management**: Protected `/api/auth/me` endpoints for display name changes and secure password updates.
- **Password Recovery**: Single-use token flow with SHA-256 token hashing, expiration enforcement, and console links.
- **Security Hardening**: Anti-enumeration error handling, `Flask-Limiter` rate limiting, strict CORS, and Pydantic validation.

---

## 📦 Module 2: Master Career Profile (Complete)

Module 2 creates the **Master Career Profile**—the single source of truth for all candidate career data, powering role-specific resumes and AI agent job discovery.

### ✨ Key Features in Module 2
- **Master Profile Schema (`candidate_profiles` collection)**:
  - Scoped to `user_id` with a database-level unique index.
  - Multi-section schema: Personal, Education, Categorized Skills (Languages, Frameworks, Databases, Tools, Other), Projects, Internships, Certifications, Achievements, Work Experience, and Preferences.
- **Secure Resume Upload & Parsing**:
  - Accepts `.pdf` and `.docx` up to 5 MB.
  - **Magic Bytes Validation**: Verifies `%PDF-` for PDFs and `PK\x03\x04` for Word documents; immediately rejects spoofed executables or unsupported files.
  - Digital text extraction via PyMuPDF (`pymupdf`) and `python-docx`.
  - Scanned/empty PDF detection with friendly guidance.
  - Files stored in **isolated, private storage** (`backend/private_storage/<user_id>/`), gitignored, and never exposed to the public.
- **AI Resume Extraction & Verification**:
  - Swappable AI Provider architecture (`services/ai_service.py`).
  - **Strict Anti-Hallucination Rules**: Extracts only explicit facts; never fabricates degrees, skills, or dates; leaves missing fields empty.
  - Automatic self-correcting retry on malformed JSON outputs.
  - **Critical User-Review Mandate**: Extraction results are returned directly to the client **WITHOUT saving to the database**. The candidate reviews, edits, and explicitly clicks *"Approve & Save"* to make it the master profile.
  - **Built-in Mock Mode (`AI_MOCK_MODE=true`)**: Allows immediate local testing and full end-to-end walkthroughs without needing an external API key.
- **Modern Fresher UI (React + Tailwind CSS)**:
  - Multi-section tabbed form with dynamic row additions/deletions.
  - Interactive skill chips/tag inputs with categorization.
  - Dynamic **Profile Strength & Completeness Bar** (0% to 100%).
  - Highlighted empty fields after AI extraction.
  - Dashboard prompts alerting the candidate when their master profile is incomplete.
  - User-controlled privacy deletion endpoint.

---

## 📦 Module 3: Multiple AI-Powered Resume Generator (Complete)

From one approved Master Career Profile, candidates generate **MULTIPLE role-specific resumes** (e.g., Python Developer, Full Stack Developer, Data Analyst, Frontend Engineer, QA Automation Engineer). The underlying career facts never change; only selection, ordering, and presentation change per target role.

### ✨ Key Features in Module 3
- **100% Truthfulness Guarantee & Resume Validator (`resume_validator.py`)**:
  - **Zero Hallucination / Invention**: Resume skills are verified against the candidate's master profile whitelist; any unverified or hallucinated skill is automatically stripped with an explicit warning.
  - Personal details (name, email, phone, links) and education details (degree, institution, year, score) are strictly bound to master profile facts.
  - Projects and internships trace back via `source_index` to verified master entries.
  - Only master profiles with `profile_status == "approved"` can generate resumes.
- **Role-Aware AI Tailoring (`ai_service.py`)**:
  - Intelligently categorizes and prioritizes the candidate's verified skills for the target role (e.g., UI/React technologies for Frontend, Python/SQL/Flask for Backend/Data).
  - Crafts a targeted 2-3 sentence professional summary tailored to the role.
  - Re-writes and emphasizes project accomplishments with action-oriented bullet points.
- **Version History & Outdated Tracking**:
  - Compound MongoDB index: `(user_id, target_role, version)`.
  - Automatic version incrementing (`v1`, `v2`, `v3`) for iterative generations without overwriting past variants.
  - **Outdated Warning Badge**: Displays a clear `⚠️ Outdated` badge whenever the candidate's Master Profile has been updated since the resume was generated (`master_updated_at > generated_from_profile_updated_at`).
- **ATS-Optimized PDF & DOCX Export (`resume_export_service.py`)**:
  - Single-column ATS-friendly layouts free of unparseable tables or confusing graphics.
  - Two visual styles:
    - **Modern**: Clean sans-serif, slate typography, subtle indigo section headers.
    - **Classic**: Traditional serif, centered header, classic horizontal divider rules.
  - Streaming downloads via authenticated endpoints with ownership verification.
- **Interactive Resume Hub & Editor (React + Tailwind CSS)**:
  - Predefined fresher role chips + custom role input.
  - **Batch Generation Mode**: Generate up to 5 role-specific resumes in a single request.
  - Live ATS Resume Preview with dynamic Modern/Classic template switching.
  - In-browser Resume Editor to tweak summaries and project bullets while enforcing master truthfulness.
  - Duplicate-to-new-version action and delete functionality.

---

## 📦 Module 4: AI Job Discovery (Complete)

Module 4 aggregates, normalizes, deduplicates, and filters fresher-friendly job opportunities from **authorized sources**, empowering candidates to discover relevant opportunities without manual hunting across portals.

### ✨ Key Features in Module 4
- **Authorized Sourcing Architecture**:
  - `JobSource` abstract base class with standardized timeouts (8s), error isolation, and 5-minute in-memory response caching.
  - `SampleJobSource`: Ingests 30 curated fresher listings across software, frontend, backend, data, QA, and cybersecurity roles.
  - `AdzunaJobSource`: Production-ready external API adapter for Adzuna free-tier API (gracefully disabled when API credentials are unset).
  - Parallel multi-source dispatcher powered by `ThreadPoolExecutor`.
- **Normalization & Intelligence Engine (`job_normalizer.py`)**:
  - **Deterministic Experience Parser**: Robust regex extraction handling varied phrasing (`"0-1 years"`, `"Freshers eligible"`, `"2+ yrs"`, `"3-5 years"`).
  - **Fresher Status Classifier**: Accurately categorizes listings into `fresher_friendly`, `entry_level`, `experience_required`, or `unclear`. Automatically overrides senior/lead titles.
  - **Skill Dictionary Extractor**: Extracts over 100 industry-standard tech skills from unstructured text descriptions.
  - **Security Sanitization**: Strips raw HTML tags from external descriptions and verifies that `application_url` strictly adheres to `http://` or `https://`.
- **Intelligent Deduplication & Expiry Engine (`dedup_service.py`)**:
  - Fuzzy title matching using `difflib.SequenceMatcher` ($\ge 0.82$) combined with word set overlap ($\ge 0.60$) across identical companies and normalized locations.
  - Links duplicate postings under a canonical `duplicate_group_id` instead of polluting search results.
  - Automated expiration checking marking jobs as `expired` if their application deadline has elapsed or if first seen $>45$ days ago.
- **Candidate Saved Jobs Pipeline & Discovery Preferences**:
  - Scoped `saved_jobs` collection with unique `(user_id, job_id)` compound index.
  - Candidates can bookmark and remove opportunities from their personal tracking pipeline.
  - Discovery preferences (`preferred_roles`, `preferred_locations`, `preferred_work_modes`, `fresher_only`) are persisted to the candidate profile.
- **Fresher UI Experience (React + Tailwind CSS)**:
  - Multi-faceted filter bar: Quick-filter fresher role chips, work mode filter (`remote`, `hybrid`, `onsite`), search keyword input, and a single-click "Fresher Friendly Only" toggle.
  - Clear **Sample Listing Badges & Banners**: Highlights sample listings with visible `⚠️ Sample listing - not a real vacancy` warnings to prevent misleading freshers.
  - Dedicated **Job Details View** with required skills pills, sanitized description, application link, and placeholder sections for upcoming Module 5 & 6 capabilities (*"Eligibility match and verification coming soon"*).
  - Dashboard integration featuring live saved jobs counters and one-click discovery navigation.

---

## 📦 Module 5: AI Job Matching & Eligibility Checking (Complete)

Module 5 provides candidates with transparent, rule-based eligibility evaluation and skill gap analysis comparing their approved Master Profile against discovered job listings.

### ✨ Key Features in Module 5
- **Strict 4-Category System**:
  - Exactly four discrete match categories: `strong_match`, `partial_match`, `low_match`, and `not_eligible`.
  - **Zero Hiring Predictions**: No "chances of selection" or probability claims. Numeric scores are strictly labelled *"Skill coverage"* or *"Match score"* with mandatory disclaimers: *"This reflects how many required skills you have. It is not a prediction of being hired."* Wording states the candidate *"appears to meet the stated requirement"*.
- **Deterministic Rules Engine (`eligibility_rules.py`)**:
  - **Hard Ineligibility Rules**: Candidate is flagged as `not_eligible` if:
    - Education qualification level is strictly below stated requirements (e.g., Diploma applying for a Master's role, unless "Any graduate" or unspecified).
    - Graduation batch year is excluded by job posting criteria (e.g. job restricted to 2024 batch while candidate graduated in 2022).
    - Job requires senior experience (>2 years) while candidate is a fresher.
    - Mandatory certifications specified in the job posting are missing.
  - **Location & Work Mode Analysis**: Detects remote flexibility and location alignment. Location mismatches are flagged as non-fatal warnings rather than hard failures, recognizing entry-level willingness to relocate.
  - **Deterministic Categorization Thresholds**:
    - $\ge 75\%$ Skill Coverage $\rightarrow$ `strong_match`
    - $40\% - 74\%$ Skill Coverage $\rightarrow$ `partial_match`
    - $< 40\%$ Skill Coverage $\rightarrow$ `low_match`
    - Any failed hard requirement $\rightarrow$ `not_eligible` (AI cannot override)
- **Curated Skill Normalizer & Related Skills (`skill_normalizer.py`)**:
  - Curated alias dictionary normalizing variants (`reactjs`/`react.js` $\rightarrow$ `React`, `nodejs` $\rightarrow$ `Node.js`, `postgres` $\rightarrow$ `PostgreSQL`).
  - Related technology pairing mapping alternative frameworks (Flask $\leftrightarrow$ Django, React $\leftrightarrow$ Vue, PostgreSQL $\leftrightarrow$ MySQL).
  - Configurable partial credit ($0.5\times$ weight via `MATCH_RELATED_SKILL_WEIGHT`):
    $$\text{Skill Coverage} = \frac{\text{Exact Matches} + 0.5 \times \text{Related Matches}}{\text{Total Required Skills}} \times 100$$
- **Explainable AI Integration (`ai_service.py`)**:
  - Deterministic-first architecture: AI only performs semantic related-skill checks and drafts plain-language explanations; **AI is strictly barred from overriding or upgrading a rule-based `not_eligible` status**.
  - **Data Minimization**: Zero candidate personal identifiable information (name, email, phone, links) is ever passed to AI prompts.
- **Profile Version Hash & Out-of-Date Tracking**:
  - Generates a SHA-256 fingerprint (`profile_version_hash`) of profile skills, education, and experience.
  - Flags match records with `is_stale: true` and an `⚠️ Out of date` badge whenever the Master Profile is modified, providing a single-click "Recompute Match" action.
- **Personalized Recommendations & Fresher UI (React + Tailwind CSS)**:
  - `MatchScore.jsx`: Category badge with 4 distinct colors, skill coverage pill, out-of-date notice, and tooltip disclaimer.
  - `MatchBreakdown.jsx`: Comprehensive requirement-by-requirement evaluation (Technical Skills, Education, Graduation Year, Experience, Location, Certifications), hard ineligibility alert, warnings list, and actionable gap-closing advice.
  - `RecommendedJobs.jsx`: Dedicated feed (`/jobs/recommended`) ranking opportunities by fit category and skill coverage, featuring category filter tabs and a "Hide Not Eligible" toggle.
  - Seamlessly integrated into `JobCard.jsx`, `JobDetails.jsx`, and candidate `Dashboard.jsx`.

---

CareerPilot AI adheres strictly to legal, ethical, and privacy standards:
1. **Zero Unauthorized Scraping**: We do not scrape websites in violation of their Terms of Service.
2. **No Evasion or Circumvention**: The system never bypasses logins, paywalls, CAPTCHAs, rate limits, or `robots.txt`.
3. **Authorized Sourcing Only**: Data is collected solely from curated sample datasets, official partner/free-tier APIs requiring authentication keys, and permitted public feeds.
4. **Transparent Sample Labelling**: Demo and sample jobs are explicitly marked in the database (`is_sample: true`) and in the UI with a prominent yellow warning badge.
5. **Candidate Privacy**: No candidate personal identifiable information (name, email, phone, master profile) is ever transmitted to external job boards or APIs.
6. **Content Sanitization**: External job descriptions are stripped of raw HTML to prevent cross-site scripting (XSS), and external URLs are strictly validated.

---

## 🔌 How to Add a New Job Source Adapter

Adding a new job source is modular and adheres to the Open-Closed Principle:

```python
from backend.services.job_sources.base import JobSource
from typing import List, Dict, Any

class CustomCompanyFeedSource(JobSource):
    name = "custom_feed"

    def is_configured(self) -> bool:
        # Check if necessary API keys or feeds are configured in config.py
        return True

    def fetch_jobs(self, query: str = None, location: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        # 1. Fetch data from authorized REST API or public JSON/RSS feed
        # 2. Return a list of raw job dicts matching the standard ingest fields:
        return [
            {
                "title": "Junior Backend Engineer",
                "company": "Acme Corp",
                "location": "Bengaluru, India",
                "work_mode": "hybrid",
                "experience_text": "0-1 years",
                "description": "Looking for freshers proficient in Python...",
                "application_url": "https://acme.careers/jobs/123",
                "is_sample": False,
                "source": self.name
            }
        ]
```

Register the new source in `backend/services/job_sources/registry.py`:
```python
from backend.services.job_sources.custom_source import CustomCompanyFeedSource
registry.register(CustomCompanyFeedSource())
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, Vite, React Router 6, Axios, Tailwind CSS |
| **Backend** | Python 3.14+, Flask 3, Flask-CORS, Flask-Limiter, Python-dotenv |
| **Database** | MongoDB (PyMongo) with compound indexes & MongoMock fallback |
| **Document Export** | ReportLab 5 (`reportlab.platypus`), `python-docx` |
| **File Parsing** | PyMuPDF (`pymupdf`), `python-docx` |
| **AI Integration** | Swappable AI Engine (Google Gemini via `google-genai` SDK / Role-Aware Mock Mode) |
| **Authentication** | JWT (HS256) via PyJWT, Bcrypt password hashing |
| **Validation** | Pydantic v2, email-validator |
| **Testing** | Pytest, MongoMock, Puppeteer Core (End-to-End Walkthroughs) |

---

## 📂 Project Structure

```text
careerpilot-ai/
├── backend/
│   ├── data/
│   │   └── sample_jobs.json         # Module 4: 30 curated sample fresher vacancies
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                  # Module 1: User schemas & serialization
│   │   ├── profile.py               # Module 2: Master Profile schemas & completeness
│   │   ├── resume.py                # Module 3: Resume schemas, validation & serialization
│   │   ├── job.py                   # Module 4: Job schemas, preferences & serialization
│   │   └── match.py                 # Module 5: Job match schemas, breakdowns & serialization
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py                  # Module 1: Auth endpoints (/api/auth)
│   │   ├── profiles.py              # Module 2: Profile endpoints (/api/profile)
│   │   ├── resumes.py               # Module 3: Resume generation & export (/api/resumes)
│   │   ├── jobs.py                  # Module 4: Job discovery & saved jobs (/api/jobs)
│   │   └── matching.py              # Module 5: Matching, batch & recommended jobs (/api/matches, /api/jobs/recommended)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py          # Module 1: @token_required decorator, Bcrypt & JWT
│   │   ├── resume_service.py        # Module 2: Magic bytes validation, text extraction & storage
│   │   ├── ai_service.py            # Modules 2, 3 & 5: Swappable AI provider (Gemini / Mock Mode)
│   │   ├── resume_validator.py      # Module 3: Deterministic truthfulness validator
│   │   ├── resume_export_service.py # Module 3: ATS PDF & DOCX generator (Modern & Classic)
│   │   ├── resume_generation_service.py # Module 3: Versioning, generation & private storage
│   │   ├── job_normalizer.py        # Module 4: Experience parsing, fresher classification & sanitization
│   │   ├── dedup_service.py         # Module 4: SequenceMatcher fuzzy deduplication & expiration engine
│   │   ├── job_service.py           # Module 4: Discovery coordination, search/filter & saved jobs
│   │   ├── skill_normalizer.py      # Module 5: Skill alias dictionary & related tech pairs
│   │   ├── eligibility_rules.py     # Module 5: Deterministic rules (education, year, exp, thresholds)
│   │   ├── matching_service.py      # Module 5: Match orchestrator, version hash & recommended feed
│   │   └── job_sources/
│   │       ├── __init__.py
│   │       ├── base.py              # Module 4: JobSource base class with caching & timeout
│   │       ├── sample_source.py     # Module 4: Sample job listings loader
│   │       ├── api_source_example.py # Module 4: Adzuna API adapter
│   │       └── registry.py          # Module 4: Source registry & parallel dispatcher
│   ├── private_storage/             # Private user uploaded resumes & exports (gitignored)
│   ├── app.py                       # Flask app factory, CORS, Rate Limiter & Blueprints
│   ├── config.py                    # Environment configuration loader (.env)
│   ├── database.py                  # PyMongo client, compound indexes & MongoMock fallback
│   ├── limiter.py                   # Flask-Limiter instance
│   └── requirements.txt             # Python backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Alert.jsx            # Reusable dismissible alerts
│   │   │   ├── Button.jsx           # Button with loading spinner states
│   │   │   ├── CompletenessBar.jsx  # Module 2: Dynamic profile strength progress bar
│   │   │   ├── Input.jsx            # Form input with inline validation & password toggle
│   │   │   ├── Navbar.jsx           # Responsive header with branding & navigation
│   │   │   ├── ProtectedRoute.jsx   # Route guard for authenticated users
│   │   │   ├── PublicRoute.jsx      # Route guard redirecting logged-in users to /dashboard
│   │   │   ├── ResumeUploadCard.jsx # Module 2: Drag & drop resume upload with AI loading state
│   │   │   ├── SkillTagInput.jsx    # Module 2: Categorized chip input component
│   │   │   ├── ResumeCard.jsx       # Module 3: Resume card with version, badges & actions
│   │   │   ├── ResumePreview.jsx    # Module 3: Live visual ATS preview (Modern & Classic)
│   │   │   ├── ResumeEditor.jsx     # Module 3: Interactive modal editor with truthfulness alerts
│   │   │   ├── JobCard.jsx          # Module 4 & 5: Job card with sample badge, fresher pill, save & match score
│   │   │   ├── MatchScore.jsx       # Module 5: Category badge, skill coverage pill & out-of-date notice
│   │   │   └── MatchBreakdown.jsx   # Module 5: Requirement evaluation table, warnings & advice
│   │   ├── context/
│   │   │   └── AuthContext.jsx      # React Context (user, login, register, logout)
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx        # Fresher dashboard with module status & quick actions
│   │   │   ├── ForgotPassword.jsx   # Password reset request
│   │   │   ├── Login.jsx            # Login page
│   │   │   ├── Profile.jsx          # Module 2: Master Career Profile multi-section builder
│   │   │   ├── Register.jsx         # Registration page
│   │   │   ├── ResetPassword.jsx    # Reset password with token
│   │   │   ├── ResumeBuilder.jsx    # Module 3: Multiple Resume Generator hub & gallery
│   │   │   ├── JobDiscovery.jsx     # Module 4: Job discovery feed, search, filter chips & saved tab
│   │   │   ├── JobDetails.jsx       # Modules 4 & 5: Full job details, sample banner & MatchBreakdown
│   │   │   ├── RecommendedJobs.jsx  # Module 5: Recommended opportunities ranked feed
│   │   │   └── Settings.jsx         # Name update & password change
│   │   ├── services/
│   │   │   ├── api.js               # Axios instance with authAPI, profileAPI, resumeAPI, jobAPI & matchingAPI
│   │   │   └── token.js             # Token storage abstraction (memory + localStorage)
│   │   ├── App.jsx                  # React Router routes (/jobs, /jobs/recommended, /jobs/:jobId, /resumes, /profile, etc.)
│   │   ├── index.css                # Tailwind CSS base styles
│   │   └── main.jsx                 # Vite React entry point
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── vite.config.js
├── tests/
│   ├── conftest.py                  # Pytest fixtures & isolated in-memory DB
│   ├── test_auth_me.py              # Protected route & password update tests
│   ├── test_login.py                # Login tests & generic error checks
│   ├── test_password_reset.py       # Password recovery flow tests
│   ├── test_profile.py              # Module 2: Profile CRUD, approval, isolation & AI retry tests
│   ├── test_register.py             # Registration tests
│   ├── test_resume_parser.py        # Module 2: Magic bytes, parsing, empty PDF & storage tests
│   ├── test_resume_validator.py     # Module 3: Truthfulness validator & anti-hallucination tests
│   ├── test_resume_generator.py     # Module 3: Resume generation, versions, batch & export tests
│   ├── test_job_discovery.py        # Module 4: Sourcing, parsing, classifier, dedup, expiry & saved jobs
│   └── test_matching.py             # Module 5: Match scoring, deterministic rules, staleness & isolation tests
├── run_full_walkthrough.py          # Automated browser walkthrough orchestrator
├── .env.example
├── .gitignore
└── README.md
```

---

## ⚙️ Environment Variables

Create a `.env` file in the project root by copying `.env.example`:

```bash
cp .env.example .env
```

| Variable | Description | Default |
|---|---|---|
| `MONGO_URI` | MongoDB connection string | `mongodb://localhost:27017/careerpilot_db` |
| `DB_NAME` | Database name | `careerpilot_db` |
| `JWT_SECRET` | Secret key for signing JWT tokens | *(Required in production)* |
| `JWT_EXPIRY_MINUTES` | Access token lifespan in minutes | `60` |
| `FRONTEND_URL` | Allowed CORS origin for React | `http://localhost:5173` |
| `PORT` | Backend server port | `5000` |
| `FLASK_DEBUG` | Flask debug mode | `True` |
| `AI_MOCK_MODE` | Enable offline mock AI extraction & generation without an API key | `true` |
| `AI_PROVIDER` | AI provider (`gemini`) | `gemini` |
| `GEMINI_API_KEY` | Google Gemini API key (optional if `AI_MOCK_MODE=true`) | *(Optional in dev)* |
| `AI_MODEL` | Gemini model name | `gemini-2.5-flash` |
| `ENABLE_SAMPLE_SOURCE` | Enable curated sample fresher jobs feed | `true` |
| `ADZUNA_APP_ID` | Adzuna Job Search API Application ID | *(Optional)* |
| `ADZUNA_APP_KEY` | Adzuna Job Search API Key | *(Optional)* |
| `ADZUNA_COUNTRY` | Adzuna country code | `in` |
| `JOB_EXPIRY_DAYS` | Cutoff in days before job is marked expired | `45` |
| `MATCH_STRONG_THRESHOLD` | Threshold score (percentage) for strong match | `75` |
| `MATCH_PARTIAL_THRESHOLD` | Threshold score (percentage) for partial match | `40` |
| `MATCH_RELATED_SKILL_WEIGHT` | Partial credit weight multiplier for related skills | `0.5` |

---

## 🚀 Setup & Installation

### 1. Backend Setup

```bash
# 1. Activate Python virtual environment
.\.venv\Scripts\Activate.ps1   # Windows PowerShell
# or: source .venv/bin/activate  # Linux/macOS

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Start Flask backend
python backend/app.py
```

### 2. Frontend Setup

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start Vite dev server
npm run dev
```

Visit `http://localhost:5173` in your browser.

---

## 🧪 Running Automated Tests

Run the full pytest suite (covering Modules 1, 2, 3, 4, and 5):

```bash
.\.venv\Scripts\pytest -v tests
```

**75 comprehensive tests pass with 100% success rate:**
- ✅ **Module 1 (Auth)**: Registration, duplicate prevention, password complexity, login verification, token protection, generic error responses, password reset lifecycle.
- ✅ **Module 2 (Master Career Profile)**: PDF/DOCX magic bytes validation, text extraction, empty PDF handling, private storage isolation, skeleton creation, profile upsert, validation, approval lifecycle, user isolation.
- ✅ **Module 3 (Multiple Resume Generator)**: Master skill whitelisting, anti-hallucination stripping, education/personal detail lock, approval gate enforcement, version auto-incrementing, batch multi-role generation, outdated badge tracking, and ATS PDF/DOCX export.
- ✅ **Module 4 (AI Job Discovery)**:
  - `test_sample_source_returns_sample_jobs`: Verifying sample source loads 30 fresher jobs with correct schema.
  - `test_normalizer_experience_parsing`: Regex parsing of `0-1 years`, `Freshers eligible`, `2+ yrs`, and `3-5 years`.
  - `test_normalizer_fresher_status_classification`: Deterministic classification into `fresher_friendly`, `entry_level`, and `experience_required`.
  - `test_normalizer_security_sanitization`: HTML stripping, XSS entity sanitization, and URL protocol checks (`http/https`).
  - `test_deduplication_engine`: SequenceMatcher similarity ($\ge 0.82$) and word set overlap ($\ge 0.60$) linking duplicates to a canonical group.
  - `test_expiration_engine`: Detecting passed application deadlines and flagging jobs older than 45 days as expired.
  - `test_discover_and_filtering_endpoints`: Full discovery workflow, multi-source ingestion, query/role/work_mode filtering, and fresher-only toggle.
  - `test_saved_jobs_lifecycle_and_isolation`: Saving, retrieving, and unsaving jobs with strict user tenant isolation.
  - `test_adzuna_adapter_disabled_gracefully_when_keys_missing`: Verifying external API adapters fail safe and silent when keys are omitted.
  - `test_unauthenticated_requests_return_401`: Enforcing `@token_required` protection across all job discovery endpoints.
- ✅ **Module 5 (AI Job Matching & Eligibility Checking)**:
  - `test_skill_normalizer_exact_and_related`: Verifies alias normalization and deterministic related technology pairing.
  - `test_deterministic_related_skill_partial_credit`: Enforces 0.5x partial credit calculation without false full credit.
  - `test_education_requirement_checking`: Degree rank hierarchy, "Any graduate" flexibility, and missing field handling.
  - `test_graduation_year_batch_mismatch`: Detects graduation year mismatch (e.g. 2022 vs 2024 batch) as hard ineligibility.
  - `test_experience_checking_fresher_vs_senior`: Flags >2 years requirement as not eligible while tracking internships separately.
  - `test_location_mismatch_is_warning_not_hard_failure`: Treats location mismatch as an advisory warning rather than disqualification.
  - `test_thresholds_strong_partial_low`: Verifies deterministic category thresholds (75%+ -> strong, 40-74% -> partial, <40% -> low).
  - `test_limited_info_handling`: Gracefully handles jobs with unspecified skills or zero candidate skills.
  - `test_ai_cannot_upgrade_hard_failure`: Guarantees rule-based `not_eligible` can never be upgraded by AI.
  - `test_staleness_detection_on_profile_edit`: Detects profile modification via SHA-256 hash and flags matches as out-of-date.
  - `test_batch_match_max_limit_enforced`: Rejects batch requests exceeding the maximum limit of 50 jobs.
  - `test_tenant_isolation_on_matches`: Enforces strict per-user database scoping and isolation.

---

## 🌐 API Reference

### Module 3: Role-Specific Resumes (`/api/resumes`)

| Method | Endpoint | Protection | Description |
|---|---|---|---|
| `GET` | `/api/resumes/roles` | `@token_required` | Get recommended fresher target roles |
| `POST` | `/api/resumes/generate` | `@token_required` | Generate tailored resume for a specific role from approved profile |
| `POST` | `/api/resumes/generate-multiple` | `@token_required` | Batch generate resumes for up to 5 target roles |
| `GET` | `/api/resumes` | `@token_required` | List all user resumes with versioning & `is_outdated` flag |
| `GET` | `/api/resumes/<id>` | `@token_required` | Retrieve single resume by ID |
| `PUT` | `/api/resumes/<id>` | `@token_required` | Update resume content/template with truthfulness check and re-export |
| `POST` | `/api/resumes/<id>/duplicate` | `@token_required` | Duplicate resume to create a new version |
| `DELETE` | `/api/resumes/<id>` | `@token_required` | Delete resume and its associated PDF/DOCX files |
| `GET` | `/api/resumes/<id>/download?format=pdf\|docx` | `@token_required` | Download ATS-optimized PDF or DOCX file |

### Module 4: Job Discovery & Saved Jobs (`/api/jobs`)

| Method | Endpoint | Protection | Description |
|---|---|---|---|
| `POST` | `/api/jobs/discover` | `@token_required` | Trigger multi-source job discovery ingestion, normalization, and deduplication |
| `GET` | `/api/jobs` | `@token_required` | Query, filter, and paginate normalized active jobs (`role`, `work_mode`, `fresher_only`, `search`) |
| `GET` | `/api/jobs/<job_id>` | `@token_required` | Retrieve full details of a specific job posting by ID |
| `POST` | `/api/jobs/save` | `@token_required` | Save a job to candidate's personal tracking pipeline |
| `DELETE` | `/api/jobs/save/<job_id>` | `@token_required` | Remove a job from candidate's saved pipeline |
| `GET` | `/api/jobs/saved` | `@token_required` | List all saved jobs for current user |
| `GET` | `/api/jobs/preferences` | `@token_required` | Retrieve candidate discovery preferences from profile |
| `PUT` | `/api/jobs/preferences` | `@token_required` | Update candidate discovery preferences (`preferred_roles`, `locations`, etc.) |
| `GET` | `/api/jobs/sources` | `@token_required` | List registered job source adapters and their operational status |

### Module 5: Job Matching & Recommendations (`/api/matches`, `/api/jobs/recommended`)

| Method | Endpoint | Protection | Description |
|---|---|---|---|
| `POST` | `/api/matches/<job_id>` | `@token_required` | Compute or recompute match breakdown and category for a job |
| `POST` | `/api/matches/batch` | `@token_required` | Batch evaluate match for up to 50 jobs |
| `GET` | `/api/matches/<job_id>` | `@token_required` | Retrieve stored match breakdown (flags `is_stale: true` if profile changed) |
| `GET` | `/api/matches` | `@token_required` | List all computed matches with category filtering and sorting |
| `GET` | `/api/jobs/recommended` | `@token_required` | Retrieve personalized recommended jobs ranked by fit category and coverage |

---

## 🔮 Upcoming Modules (Roadmap)
- ✅ **Module 1**: User Registration & Authentication
- ✅ **Module 2**: Master Career Profile & AI Resume Extraction
- ✅ **Module 3**: Multiple AI-Powered Role-Specific Resume Generator
- ✅ **Module 4**: AI Job Discovery, Normalization & Filtering
- ✅ **Module 5**: AI Job Matching & Eligibility Checking Engine
- ⏳ **Module 6**: Recruiter & Legitimacy Verification (Domain checking, ghost job detection, salary sanity)
- ⏳ **Module 7**: Application Assistant & Pipeline Tracker

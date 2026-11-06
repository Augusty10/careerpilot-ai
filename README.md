# 🚀 CareerPilot AI

### One Profile. Multiple Careers. Smarter Applications.

CareerPilot AI is an AI-powered career platform designed specifically for freshers and recent graduates. It simplifies the entire entry-level job search journey: candidates maintain one master career profile, generate tailored role-specific resumes, discover verified fresher opportunities, and submit smarter applications coordinated with AI agents.

---

## 📦 Module 1: User Registration & Login (Current Milestone)

Module 1 delivers the production-ready authentication and user management foundation for CareerPilot AI. All subsequent modules (Master Profile, AI Resumes, Job Discovery, Switch Agents) build upon this authenticated infrastructure.

### ✨ Key Features in Module 1
- **User Registration**: Real-time form validation, bcrypt password hashing, and duplicate email prevention.
- **Secure Login**: Rate-limited endpoint returning a signed JWT access token and sanitized user profile.
- **Protected Sessions**: `@token_required` decorator attaching the current user to Flask requests and enforcing authorization across private routes.
- **Account Management**: Protected `/api/auth/me` endpoints to retrieve user profiles, edit display names, and change passwords with current-password verification.
- **Password Recovery**: Secure, time-limited token flow with SHA-256 token hashing, single-use enforcement, replay protection, and console link output for development.
- **Security Hardening**:
  - Bcrypt salted password hashing (plaintext passwords are never stored or logged).
  - Pydantic schema validation enforcing email formatting and password complexity (min 8 chars, letter + number).
  - Normalization of all email addresses to lowercase.
  - Zero sensitive leakage: `password_hash` and reset tokens are strictly excluded from all API responses.
  - Generic error messages ("Invalid email or password") to eliminate user enumeration vectors.
  - Rate limiting via `Flask-Limiter` on login and forgot-password endpoints.
  - Strict CORS origin filtering restricted to `FRONTEND_URL`.
  - Abstraction layer in `services/token.js` ready for future `httpOnly` cookie migration.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, Vite, React Router 6, Axios, Tailwind CSS |
| **Backend** | Python 3.14+, Flask 3, Flask-CORS, Flask-Limiter, Python-dotenv |
| **Database** | MongoDB (PyMongo) with automatic fallback to MongoMock for local testing |
| **Authentication** | JWT (HS256) via PyJWT, Bcrypt password hashing |
| **Validation** | Pydantic v2, email-validator |
| **Testing** | Pytest, MongoMock |

---

## 📂 Project Structure

```text
careerpilot-ai/
├── backend/
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py             # Pydantic validation schemas & serialization
│   ├── routes/
│   │   ├── __init__.py
│   │   └── auth.py             # Auth Blueprint (register, login, logout, reset, /me)
│   ├── services/
│   │   ├── __init__.py
│   │   └── auth_service.py     # Password hashing, JWT utils & @token_required decorator
│   ├── app.py                  # Flask app factory, CORS, Rate Limiter & error handlers
│   ├── config.py               # Environment configuration loader (.env)
│   ├── database.py             # MongoDB connection, unique email index & fallback
│   ├── limiter.py              # Flask-Limiter instance
│   └── requirements.txt        # Python backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Alert.jsx            # Reusable dismissible alerts
│   │   │   ├── Button.jsx           # Button with spinner loading states
│   │   │   ├── Input.jsx            # Form input with inline errors & password toggle
│   │   │   ├── Navbar.jsx           # Responsive header with branding & auth navigation
│   │   │   ├── ProtectedRoute.jsx   # Route guard for authenticated users
│   │   │   └── PublicRoute.jsx      # Route guard redirecting logged-in users to /dashboard
│   │   ├── context/
│   │   │   └── AuthContext.jsx      # React Context (user, login, register, logout)
│   │   ├── pages/
│   │   │   ├── Register.jsx         # Registration page
│   │   │   ├── Login.jsx            # Login page
│   │   │   ├── ForgotPassword.jsx   # Password reset request
│   │   │   ├── ResetPassword.jsx    # Reset password with token
│   │   │   ├── Dashboard.jsx        # Fresher dashboard placeholder
│   │   │   └── Settings.jsx         # Name update & password change
│   │   ├── services/
│   │   │   ├── api.js               # Axios instance with JWT interceptor & 401 handling
│   │   │   └── token.js             # Token storage abstraction (memory + localStorage)
│   │   ├── App.jsx                  # React Router routes
│   │   ├── index.css                # Tailwind CSS base styles
│   │   └── main.jsx                 # Vite React entry point
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── vite.config.js
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures & isolated in-memory DB
│   ├── test_register.py        # Registration tests
│   ├── test_login.py           # Login tests & generic error checks
│   ├── test_auth_me.py         # Protected route & password update tests
│   └── test_password_reset.py  # End-to-end password recovery flow tests
├── .env.example                # Template for environment variables
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
| `FRONTEND_URL` | Allowed CORS origin for the React app | `http://localhost:5173` |
| `PORT` | Backend server port | `5000` |
| `FLASK_DEBUG` | Flask debug mode | `True` |

> **Note on MongoDB**: If you have a local MongoDB daemon or MongoDB Atlas URI, specify it in `MONGO_URI`. If no MongoDB server is running locally, CareerPilot AI automatically and gracefully falls back to an in-memory database (`mongomock`) so you can develop and run tests without external friction.

---

## 🚀 Setup & Installation

### 1. Backend Setup

```bash
# 1. Create a Python virtual environment
python -m venv .venv

# 2. Activate the virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Windows (Command Prompt):
.\.venv\Scripts\activate.bat
# Linux / macOS:
source .venv/bin/activate

# 3. Install backend dependencies
pip install -r backend/requirements.txt

# 4. Start the backend development server
python backend/app.py
```

The backend will start at `http://127.0.0.1:5000` with CORS enabled for `http://localhost:5173`.

---

### 2. Frontend Setup

In a new terminal window:

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install frontend dependencies
npm install

# 3. Start the Vite React development server
npm run dev
```

Open your browser at `http://localhost:5173`.

---

## 🧪 Running Automated Tests

A comprehensive `pytest` test suite is included in `/tests`, covering registration, login, security rules, protected sessions, and the complete password recovery lifecycle:

```bash
# Ensure virtual environment is activated
.\.venv\Scripts\pytest -v tests
```

### Test Suite Highlights
- ✅ `test_register_success`: Validates account creation (HTTP 201).
- ✅ `test_register_duplicate_email_rejected`: Enforces unique email constraint (HTTP 409).
- ✅ `test_register_weak_password_rejected`: Enforces 8+ chars with letters and numbers.
- ✅ `test_register_invalid_email_rejected`: Enforces RFC email format.
- ✅ `test_login_success`: Validates JWT token and profile issuance (HTTP 200).
- ✅ `test_login_wrong_password_rejected`: Enforces generic 401 error.
- ✅ `test_login_unknown_email_same_generic_error`: Confirms identical generic errors across missing users and bad passwords (anti-enumeration).
- ✅ `test_me_without_token_returns_401`: Verifies `@token_required` rejects unauthenticated calls.
- ✅ `test_me_with_valid_token_returns_user`: Verifies authenticated profile extraction.
- ✅ `test_put_me_update_name`: Verifies profile name updates.
- ✅ `test_put_me_change_password`: Verifies password changes requiring old password verification.
- ✅ `test_password_reset_end_to_end`: Tests full forgot password -> token -> reset -> new login flow.
- ✅ `test_password_reset_reused_token_rejected`: Ensures single-use reset token security.
- ✅ `test_password_reset_expired_token_rejected`: Ensures token expiration enforcement.
- ✅ `test_password_hash_never_returned`: Enforces that `password_hash` is never exposed in any response.

---

## 🌐 API Reference (Module 1)

| Method | Endpoint | Protection | Description |
|---|---|---|---|
| `POST` | `/api/auth/register` | Public | Create new fresher user account |
| `POST` | `/api/auth/login` | Rate-limited (5/min) | Authenticate user & receive JWT |
| `POST` | `/api/auth/logout` | Public | Session logout confirmation |
| `POST` | `/api/auth/forgot-password` | Rate-limited (3/min) | Request time-limited reset link (link printed to console) |
| `POST` | `/api/auth/reset-password` | Public | Reset password using valid token |
| `GET` | `/api/auth/me` | `@token_required` | Get current user's profile |
| `PUT` | `/api/auth/me` | `@token_required` | Update name or change password |
| `GET` | `/api/health` | Public | Service health & module status |

---

## 🔮 Upcoming Modules (Roadmap)
- **Module 2**: Master Career Profile (Education, Projects, Skills, Internships)
- **Module 3**: AI Resume Generator (Tailored, role-specific resumes)
- **Module 4**: Job Discovery & Switch Agent Coordination (Scraping, matching, recruiter verification)
- **Module 5**: Application Assistant & Tracker

import os
from pathlib import Path
from dotenv import load_dotenv

# Locate and load the root .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Application configuration loaded from environment variables."""

    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/careerpilot_db")
    DB_NAME = os.getenv("DB_NAME", "careerpilot_db")
    JWT_SECRET = os.getenv("JWT_SECRET", "careerpilot-dev-jwt-secret-key-change-in-production")
    JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "60"))
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    PORT = int(os.getenv("PORT", "5000"))
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")

    # Rate limiting configuration (memory storage by default)
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "200 per day;50 per hour")
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")

    # Module 2: AI & Resume Extraction Settings
    AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    AI_MODEL = os.getenv("AI_MODEL", "gemini-2.5-flash")
    AI_MOCK_MODE = os.getenv("AI_MOCK_MODE", "true").lower() in ("true", "1", "yes")

    # File Upload & Private Storage (5 MB max)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    PRIVATE_STORAGE_DIR = os.getenv(
        "PRIVATE_STORAGE_DIR",
        str(BASE_DIR / "backend" / "private_storage")
    )

    # Module 4: Job Discovery Settings
    ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
    ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
    ADZUNA_COUNTRY = os.getenv("ADZUNA_COUNTRY", "in")
    JOB_EXPIRY_DAYS = int(os.getenv("JOB_EXPIRY_DAYS", "45"))
    ENABLE_SAMPLE_SOURCE = os.getenv("ENABLE_SAMPLE_SOURCE", "true").lower() in ("true", "1", "yes")

    # Module 5: Job Matching & Eligibility Settings
    MATCH_STRONG_THRESHOLD = int(os.getenv("MATCH_STRONG_THRESHOLD", "75"))
    MATCH_PARTIAL_THRESHOLD = int(os.getenv("MATCH_PARTIAL_THRESHOLD", "40"))
    MATCH_RELATED_SKILL_WEIGHT = float(os.getenv("MATCH_RELATED_SKILL_WEIGHT", "0.5"))

    # Module 6: Company & Recruiter Verification Settings
    VERIFICATION_CACHE_TTL_HOURS = int(os.getenv("VERIFICATION_CACHE_TTL_HOURS", "24"))
    DOMAIN_MIN_AGE_DAYS = int(os.getenv("DOMAIN_MIN_AGE_DAYS", "180"))
    VERIFICATION_NETWORK_TIMEOUT = int(os.getenv("VERIFICATION_NETWORK_TIMEOUT", "5"))
    MCA_API_KEY = os.getenv("MCA_API_KEY", "")
    VERIFICATION_RULES_PATH = os.getenv(
        "VERIFICATION_RULES_PATH",
        str(BASE_DIR / "backend" / "config" / "verification_rules.json")
    )

import os
from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError
import mongomock
from backend.config import Config

_client = None
_db = None


def get_db(client_override=None, db_name_override=None):
    """
    Returns the active MongoDB database instance.
    Initializes the connection if it hasn't been created yet.
    Supports client_override for testing.
    If live MongoDB is unreachable, gracefully falls back to mongomock.
    """
    global _client, _db

    if client_override is not None:
        _client = client_override
        db_name = db_name_override or Config.DB_NAME
        _db = _client[db_name]
        _ensure_indexes(_db)
        return _db

    if _db is None:
        use_mock = os.getenv("USE_MOCK_DB", "false").lower() in ("true", "1", "yes")

        if use_mock:
            print("[Database] Initializing in-memory mock database (USE_MOCK_DB=True)...")
            _client = mongomock.MongoClient()
            _db = _client[Config.DB_NAME]
            _ensure_indexes(_db)
            return _db

        try:
            _client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=800, connectTimeoutMS=800)
            # Ping database to confirm live connection
            _client.admin.command("ping")
            db_name = Config.DB_NAME
            try:
                default_db = _client.get_default_database()
                if default_db is not None:
                    db_name = default_db.name
            except Exception:
                pass
            _db = _client[db_name]
            print(f"[Database] Successfully connected to live MongoDB at {Config.MONGO_URI} (db: {db_name})")
            _ensure_indexes(_db)
        except (ServerSelectionTimeoutError, PyMongoError, Exception) as err:
            print(f"[Database] Notice: Live MongoDB server is not running on {Config.MONGO_URI} ({err}).")
            print("[Database] Gracefully falling back to in-memory MongoMock so CareerPilot AI runs seamlessly.")
            _client = mongomock.MongoClient()
            _db = _client[Config.DB_NAME]
            _ensure_indexes(_db)

    return _db


def _ensure_indexes(db):
    """Creates essential database indexes, including unique email index on users and unique user_id index on candidate_profiles."""
    try:
        db.users.create_index([("email", ASCENDING)], unique=True)
    except Exception as e:
        print(f"[Database] Index notice (users.email): {e}")

    try:
        db.candidate_profiles.create_index([("user_id", ASCENDING)], unique=True)
    except Exception as e:
        print(f"[Database] Index notice (candidate_profiles.user_id): {e}")

    try:
        db.resumes.create_index(
            [("user_id", ASCENDING), ("target_role", ASCENDING), ("version", ASCENDING)]
        )
    except Exception as e:
        print(f"[Database] Index notice (resumes): {e}")

    try:
        db.jobs.create_index([("job_id", ASCENDING)], unique=True)
        db.jobs.create_index([("status", ASCENDING), ("posted_at", -1)])
        db.jobs.create_index([("fresher_status", ASCENDING), ("status", ASCENDING)])
    except Exception as e:
        print(f"[Database] Index notice (jobs): {e}")

    try:
        db.saved_jobs.create_index(
            [("user_id", ASCENDING), ("job_id", ASCENDING)],
            unique=True
        )
    except Exception as e:
        print(f"[Database] Index notice (saved_jobs): {e}")

    try:
        db.job_matches.create_index(
            [("user_id", ASCENDING), ("job_id", ASCENDING)],
            unique=True
        )
        db.job_matches.create_index([("user_id", ASCENDING), ("category", ASCENDING)])
        db.job_matches.create_index([("user_id", ASCENDING), ("skill_coverage", -1)])
    except Exception as e:
        print(f"[Database] Index notice (job_matches): {e}")


def get_users_collection(db=None):
    """Convenience helper returning the 'users' collection."""
    database = db if db is not None else get_db()
    return database["users"]


def get_profiles_collection(db=None):
    """Convenience helper returning the 'candidate_profiles' collection."""
    database = db if db is not None else get_db()
    return database["candidate_profiles"]


def get_resumes_collection(db=None):
    """Convenience helper returning the 'resumes' collection."""
    database = db if db is not None else get_db()
    return database["resumes"]


def get_jobs_collection(db=None):
    """Convenience helper returning the 'jobs' collection."""
    database = db if db is not None else get_db()
    return database["jobs"]


def get_saved_jobs_collection(db=None):
    """Convenience helper returning the 'saved_jobs' collection."""
    database = db if db is not None else get_db()
    return database["saved_jobs"]


def get_job_matches_collection(db=None):
    """Convenience helper returning the 'job_matches' collection."""
    database = db if db is not None else get_db()
    return database["job_matches"]


def close_db():
    """Closes the MongoDB connection if open."""
    global _client, _db
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
        _client = None
        _db = None

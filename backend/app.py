import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, jsonify
from flask_cors import CORS

from backend.config import Config
from backend.database import get_db
from backend.limiter import limiter
from backend.routes.auth import auth_bp
from backend.routes.profiles import profiles_bp
from backend.routes.resumes import resumes_bp
from backend.routes.jobs import jobs_bp
from backend.routes.matching import matching_bp


def create_app(config_class=Config, client_override=None, db_name_override=None):
    """
    Application factory for CareerPilot AI backend.
    Supports dependency injection for database clients in automated tests.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize CORS restricted to FRONTEND_URL
    CORS(
        app,
        resources={r"/api/*": {"origins": [config_class.FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"]}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    # Initialize Rate Limiter
    limiter.init_app(app)

    # Initialize Database connection & indexes
    with app.app_context():
        get_db(client_override=client_override, db_name_override=db_name_override)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(profiles_bp)
    app.register_blueprint(resumes_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(matching_bp)

    # Health check endpoint
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "CareerPilot AI API",
            "modules": [
                "Module 1 - Auth",
                "Module 2 - Master Profile",
                "Module 3 - AI Resume Generator",
                "Module 4 - AI Job Discovery",
                "Module 5 - Job Matching & Eligibility"
            ]
        }), 200

    # Global Error Handlers
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({"error": f"Rate limit exceeded: {e.description}"}), 429

    @app.errorhandler(404)
    def not_found_handler(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error_handler(e):
        return jsonify({"error": "An internal server error occurred"}), 500

    return app


# Root app instance for development server
app = create_app()

if __name__ == "__main__":
    print(f"🚀 CareerPilot AI Backend running on http://127.0.0.1:{Config.PORT}")
    print(f"📡 CORS enabled for: {Config.FRONTEND_URL}")
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)


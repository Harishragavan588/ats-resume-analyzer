"""
app.py — Application entry point.
"""

import logging
import sys
from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from models import init_db
from routes.analysis_routes import bp as analysis_bp

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # Config
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH
    app.config["DEBUG"] = Config.DEBUG

    # CORS (development only — restrict in production)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    app.register_blueprint(analysis_bp)

    # Global error handlers
    @app.errorhandler(413)
    def request_too_large(e):
        return (
            jsonify({
                "success": False,
                "error": (
                    f"File too large. Maximum allowed size is "
                    f"{Config.MAX_UPLOAD_SIZE_MB} MB."
                ),
            }),
            413,
        )

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "Resource not found."}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"success": False, "error": "Internal server error."}), 500

    return app


if __name__ == "__main__":
    # Initialise database tables
    logger.info("Initialising database …")
    init_db()
    logger.info("Database ready.")

    Config.ensure_upload_folder()

    app = create_app()
    logger.info("Starting ATS Resume Analyzer on http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)

"""
config.py — Application configuration.
Loads environment variables and provides typed settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


class Config:
    # Flask
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    FLASK_ENV: str = os.environ.get("FLASK_ENV", "development")
    DEBUG: bool = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")

    # File uploads
    MAX_UPLOAD_SIZE_MB: int = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "5"))
    MAX_CONTENT_LENGTH: int = MAX_UPLOAD_SIZE_MB * 1024 * 1024  # bytes
    ALLOWED_EXTENSIONS: set = {"pdf", "docx"}
    UPLOAD_FOLDER: Path = BASE_DIR / os.environ.get("UPLOAD_FOLDER", "uploads")

    # Database
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'ats_analyzer.db'}"
    )

    # Logging
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")

    # ATS Scoring weights (must sum to 100)
    SCORE_WEIGHT_KEYWORD: float = float(os.environ.get("SCORE_WEIGHT_KEYWORD", "40"))
    SCORE_WEIGHT_SIMILARITY: float = float(os.environ.get("SCORE_WEIGHT_SIMILARITY", "30"))
    SCORE_WEIGHT_EXPERIENCE: float = float(os.environ.get("SCORE_WEIGHT_EXPERIENCE", "20"))
    SCORE_WEIGHT_FORMATTING: float = float(os.environ.get("SCORE_WEIGHT_FORMATTING", "10"))

    @classmethod
    def ensure_upload_folder(cls) -> None:
        cls.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

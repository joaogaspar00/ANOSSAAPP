"""
config.py — Application configuration

Separates dev/prod configs so the same codebase can run in both environments
without changing code. Sensitive values come from environment variables.
SQLite by default (single-file, zero setup); set DATABASE_URL to point
elsewhere (e.g. PostgreSQL) if needed.
"""
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Shared base configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production-please")
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = False   # flip to True behind HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'anossa.db')}"
    )


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

    @classmethod
    def init_app(cls, app):
        assert cls.SQLALCHEMY_DATABASE_URI, "DATABASE_URL must be set"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

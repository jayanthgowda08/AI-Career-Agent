"""
config.py — Application Settings

Uses pydantic-settings to load configuration from environment variables.
All settings are type-validated automatically. If a required variable is
missing from the .env file, the app will refuse to start and tell you exactly
which variable is missing — this prevents silent misconfigurations.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Central configuration for the entire application.
    Values are read from the .env file or actual environment variables.
    Environment variables take priority over the .env file.
    """

    # --- App ---
    app_name: str = "AI Career Agent"
    environment: str = "development"
    log_level: str = "INFO"
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # --- Database ---
    database_url: str
    postgres_user: str = "career_user"
    postgres_password: str = "career_password"
    postgres_db: str = "career_agent"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # --- Security ---
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # --- Gemini AI ---
    gemini_api_key: str
    gemini_model: str = "gemini-3.5-flash"

    # --- File Uploads ---
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 10

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        """
        Auto-corrects cloud database URLs (e.g. Render, Heroku) that supply
        'postgres://' or 'postgresql://' so SQLAlchemy loads the psycopg driver.
        """
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+psycopg://", 1)
            elif v.startswith("postgresql://") and not v.startswith("postgresql+"):
                return v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v

    @property
    def allowed_origins_list(self) -> list[str]:
        """Convert comma-separated origins string into a Python list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"

    # Tell pydantic-settings to read from a .env file
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../backend/.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # ignore unknown env vars
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.

    Using lru_cache means Settings is only instantiated once per process
    instead of on every request — this is important for performance because
    reading and validating env vars on every API call would be wasteful.
    """
    return Settings()


# Convenience export — import this directly in other modules
settings = get_settings()

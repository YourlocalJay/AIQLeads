from typing import Dict, Any, Optional
from functools import lru_cache
import os
import logging
from pathlib import Path
from pydantic import BaseSettings, validator, PostgresDsn, ValidationError


class Settings(BaseSettings):
    """
    Application settings management with environment variable configuration.
    Implements secure credential handling and environment-specific configurations.
    """

    # Environment Configuration
    ENV: str = "development"
    DEBUG: bool = False

    # Database Configuration
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str
    DB_NAME: str = "aiqleads"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DATABASE_URL: Optional[PostgresDsn] = None

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None

    # Elasticsearch Configuration
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200

    # Application Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    MIN_PASSWORD_LENGTH: int = 8

    @validator("DEBUG", pre=True)
    def set_debug(cls, v: Any, values: Dict[str, Any]) -> bool:
        return values.get("ENV", "development") == "development"

    @validator("SECRET_KEY", pre=True)
    def validate_secret_key(cls, v: Optional[str]) -> str:
        if not v or len(v) < 32:
            if os.getenv("ENV") == "production":
                raise ValueError(
                    "SECRET_KEY must be at least 32 characters in production"
                )
            return "development_secret_key_please_change_in_production"
        return v

    @validator("DB_POOL_SIZE", "DB_MAX_OVERFLOW", pre=True)
    def validate_positive_int(cls, v: Any, field: str) -> int:
        try:
            value = int(v)
            if value <= 0:
                raise ValueError
            return value
        except (TypeError, ValueError):
            raise ValueError(f"{field} must be a positive integer")

    @validator("DATABASE_URL", pre=True)
    def assemble_db_url(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        if v:
            return v

        user = values.get("DB_USER")
        password = values.get("DB_PASSWORD")
        host = values.get("DB_HOST")
        port = values.get("DB_PORT")
        db = values.get("DB_NAME")

        if not all([user, password, host, port, db]):
            if values.get("ENV") == "production":
                raise ValueError("Database configuration is incomplete")
            return "postgresql://postgres:postgres@localhost:5432/aiqleads"

        return f"postgresql://{user}:{password}@{host}:{port}/{db}"

    def _setup_logging(self) -> None:
        """Configure application logging based on environment"""
        log_level = logging.DEBUG if self.DEBUG else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert settings to dictionary, excluding sensitive information.
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        return {
            "ENV": self.ENV,
            "DEBUG": self.DEBUG,
            "DB_HOST": self.DB_HOST,
            "DB_PORT": self.DB_PORT,
            "DB_NAME": self.DB_NAME,
            "DB_POOL_SIZE": self.DB_POOL_SIZE,
            "DB_MAX_OVERFLOW": self.DB_MAX_OVERFLOW,
            "API_V1_PREFIX": self.API_V1_PREFIX,
            "REDIS_HOST": self.REDIS_HOST,
            "REDIS_PORT": self.REDIS_PORT,
            "ELASTICSEARCH_HOST": self.ELASTICSEARCH_HOST,
            "ELASTICSEARCH_PORT": self.ELASTICSEARCH_PORT,
        }

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Create and cache settings instance.
    Returns:
        Settings: Application settings instance
    """
    try:
        return Settings()
    except ValidationError as e:
        logging.error(f"Configuration error: {e}")
        raise

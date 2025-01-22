from typing import Dict, Any
from functools import lru_cache
import os
import logging
from pathlib import Path

class Settings:
    """
    Application settings management with environment variable configuration.
    Implements secure credential handling and environment-specific configurations.
    """
    def __init__(self):
        self.ENV: str = os.getenv("APP_ENV", "development")
        self.DEBUG: bool = self.ENV == "development"
        
        # Database Configuration
        self.DB_HOST: str = os.getenv("DB_HOST", "localhost")
        self.DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
        self.DB_USER: str = os.getenv("DB_USER", "postgres")
        self.DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
        self.DB_NAME: str = os.getenv("DB_NAME", "aiqleads")
        self.DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
        self.DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
        
        # Application Configuration
        self.API_V1_PREFIX: str = "/api/v1"
        self.PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
        
        # Security
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "development_key")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )
        
        # Initialize logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure application logging based on environment"""
        log_level = logging.DEBUG if self.DEBUG else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def get_database_url(self) -> str:
        """
        Construct database URL from configuration.
        Returns:
            str: SQLAlchemy-compatible database URL
        """
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
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
            "API_V1_PREFIX": self.API_V1_PREFIX
        }

@lru_cache()
def get_settings() -> Settings:
    """
    Create and cache settings instance.
    Returns:
        Settings: Application settings instance
    """
    return Settings()

# Convenience function for database URL
def get_database_url() -> str:
    """
    Get database URL from settings.
    Returns:
        str: Database URL string
    """
    return get_settings().get_database_url()
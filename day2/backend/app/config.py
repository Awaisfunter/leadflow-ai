"""LeadFlow AI — Application Configuration"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    gemini_api_key: str = ""

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    # Database
    sqlite_db_path: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "logs",
        "audit.db",
    )

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Human Approval
    demo_reviewer_id: str = "demo_user"

    # External integrations (Day 3 & Day 4 hardened)
    dns_timeout_seconds: float = 5.0
    website_timeout_seconds: float = 5.0
    website_max_redirects: int = 3

    # Data paths (points to day2/data/)
    data_dir: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data",
    )

    @property
    def synthetic_companies_path(self) -> str:
        return os.path.join(self.data_dir, "synthetic_companies.json")

    @property
    def business_rules_path(self) -> str:
        return os.path.join(self.data_dir, "business_rules.json")

    @property
    def gemini_available(self) -> bool:
        return bool(self.gemini_api_key and self.gemini_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()

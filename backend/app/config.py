from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ObjectLens"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    s3_endpoint_url: str | None = None
    s3_region: str = "us-east-1"
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_bucket: str | None = None
    s3_force_path_style: bool = True

    database_url: str = "sqlite:///./objectlens.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="OBJECTLENS_",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

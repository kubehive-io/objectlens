from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ObjectLens"
    cors_origins: str = "http://localhost:3000"
    objectlens_provider: str = Field(
        default="ceph",
        validation_alias=AliasChoices("OBJECTLENS_PROVIDER", "objectlens_provider"),
    )
    providers_config_dir: str = Field(
        default="backend/data/providers",
        validation_alias=AliasChoices("OBJECTLENS_PROVIDERS_CONFIG_DIR", "providers_config_dir"),
    )
    providers_reload_interval: int = Field(
        default=0,
        validation_alias=AliasChoices(
            "OBJECTLENS_PROVIDERS_RELOAD_INTERVAL", "providers_reload_interval"
        ),
    )

    ceph_s3_endpoint_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("CEPH_S3_ENDPOINT_URL", "ceph_s3_endpoint_url"),
    )
    ceph_s3_region: str = Field(
        default="us-east-1",
        validation_alias=AliasChoices("CEPH_S3_REGION", "ceph_s3_region"),
    )
    ceph_s3_access_key_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("CEPH_S3_ACCESS_KEY_ID", "ceph_s3_access_key_id"),
    )
    ceph_s3_secret_access_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("CEPH_S3_SECRET_ACCESS_KEY", "ceph_s3_secret_access_key"),
    )
    ceph_s3_default_bucket: str | None = Field(
        default=None,
        validation_alias=AliasChoices("CEPH_S3_DEFAULT_BUCKET", "ceph_s3_default_bucket"),
    )
    ceph_s3_verify_ssl: bool = Field(
        default=False,
        validation_alias=AliasChoices("CEPH_S3_VERIFY_SSL", "ceph_s3_verify_ssl"),
    )

    garage_s3_endpoint_url: str | None = Field(
        default="http://localhost:3900",
        validation_alias=AliasChoices("GARAGE_S3_ENDPOINT_URL", "garage_s3_endpoint_url"),
    )
    garage_s3_region: str = Field(
        default="garage",
        validation_alias=AliasChoices("GARAGE_S3_REGION", "garage_s3_region"),
    )
    garage_s3_access_key_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GARAGE_S3_ACCESS_KEY_ID", "garage_s3_access_key_id"),
    )
    garage_s3_secret_access_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GARAGE_S3_SECRET_ACCESS_KEY", "garage_s3_secret_access_key"),
    )
    garage_s3_default_bucket: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GARAGE_S3_DEFAULT_BUCKET", "garage_s3_default_bucket"),
    )
    garage_s3_verify_ssl: bool = Field(
        default=False,
        validation_alias=AliasChoices("GARAGE_S3_VERIFY_SSL", "garage_s3_verify_ssl"),
    )

    database_url: str = "sqlite:///./objectlens.db"

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_prefix="OBJECTLENS_",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Banking API"
    api_prefix: str = "/api/v1"
    secret_key: str = Field(default="change-me-in-production", min_length=16)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    database_url: str = "sqlite:///./data/banking.db"
    enable_swagger: bool = True
    bootstrap_admin_email: str = "admin@bankexample.com"
    bootstrap_admin_password: str = "Admin@12345"
    bootstrap_admin_name: str = "System Admin"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

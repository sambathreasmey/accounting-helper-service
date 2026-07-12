# app/config.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    # Production defaults or validated requirements
    ENVIRONMENT: str = Field(default="production")
    DATABASE_URL: str
    REDIS_URL: str
    
    # Restrict to loading from a local .env only during development
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = AppSettings()
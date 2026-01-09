"""
Application Configuration
Loads environment variables and provides typed settings.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    google_api_key: str
    browserbase_api_key: str
    browserbase_project_id: str
    
    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017"
    database_name: str = "exam_automation"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # Email SMTP
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # Captcha (optional)
    captcha_provider: Optional[str] = None
    captcha_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()

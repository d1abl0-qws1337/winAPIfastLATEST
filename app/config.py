from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "FinTech Payment Service"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://fintech:fintech@fintech_db:5432/fintech"

    redis_url: str = "redis://fintech_redis:6379/0"

    rabbitmq_url: str = "amqp://guest:guest@fintech_rabbitmq:5672/"

    jwt_secret_key: str = "your-super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_api_version: str = "2023-10-16"

    payment_queue_name: str = "payment_processing"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

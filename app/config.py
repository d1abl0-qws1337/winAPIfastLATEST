from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    app_name: str = "FinTech Payment Service"
    debug: bool = False

    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://fintech:fintech@db:5432/fintech"
    )

    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    rabbitmq_url: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    stripe_api_version: str = "2023-10-16"

    payment_queue_name: str = "payment_processing"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

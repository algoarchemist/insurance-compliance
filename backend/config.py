"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    APP_NAME: str = "Sugamai"
    APP_ENV: str = "development"
    SECRET_KEY: str = "dev-secret-key-change-in-production-64chars-long-xxxxxxxxxxxxxxxx"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://sugamai:sugamai@localhost:5432/sugamai_db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "sugamai"
    MINIO_SECRET_KEY: str = "sugamai123"
    MINIO_BUCKET_DOCUMENTS: str = "sugamai-docs"
    MINIO_SECURE: bool = False

    # UIDAI (Aadhaar) — sandbox
    UIDAI_AUTH_URL: str = "https://stage1.uidai.gov.in/authserver/2.5"
    UIDAI_AUA_CODE: str = ""
    UIDAI_LICENSE_KEY: str = ""

    # ABDM (ABHA) — sandbox
    ABDM_BASE_URL: str = "https://sandbox.abdm.gov.in/api/v3"
    ABDM_CLIENT_ID: str = ""
    ABDM_CLIENT_SECRET: str = ""

    # NHCX — sandbox
    NHCX_BASE_URL: str = "https://dev.hcxprotocol.io/api/v0.7"
    NHCX_PARTICIPANT_CODE: str = ""
    NHCX_AUTH_TOKEN: str = ""
    NHCX_ENCRYPTION_CERT: str = ""

    # NHA (PMJAY)
    NHA_BASE_URL: str = "https://pmjay.gov.in/api"
    NHA_API_KEY: str = ""

    # Google Maps
    GOOGLE_MAPS_API_KEY: str = ""

    # Claude AI (Anthropic)
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"

    # SMS (OTP delivery)
    SMS_PROVIDER: str = "twilio"
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""

    # Bank Penny Drop
    PENNY_DROP_PROVIDER: str = "razorpay"
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""

    # Frontend
    NEXT_PUBLIC_API_URL: str = "http://localhost:8000"
    NEXT_PUBLIC_GOOGLE_MAPS_KEY: str = ""
    NEXT_PUBLIC_APP_NAME: str = "Sugamai"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

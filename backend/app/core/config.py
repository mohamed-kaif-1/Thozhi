from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "THOZHI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DATA_BACKEND: str = ""
    REPOSITORY_BACKEND: str = ""

    # Primary Speech Recognition: Gnani AI Prisma v3
    GNANI_API_KEY: str = ""
    GNANI_API_URL: str = "https://api.vachana.ai"

    # Commercial Failover (Optional)
    SARVAM_API_KEY: str = ""
    SARVAM_API_URL: str = "https://api.sarvam.ai"

    # NLU Configuration
    GEMINI_API_KEY: str = ""

    # Supabase & Auth
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    SUPABASE_JWT_AUDIENCE: str = "authenticated"
    SUPABASE_JWT_ISSUER: Optional[str] = None
    SUPABASE_JWKS_URL: Optional[str] = None
    SUPABASE_JWT_ALGORITHMS: List[str] = ["HS256", "RS256", "ES256"]

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator(
        "GNANI_API_KEY", "SARVAM_API_KEY", "GEMINI_API_KEY",
        "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_KEY",
        "SUPABASE_JWT_SECRET", "SUPABASE_JWT_AUDIENCE",
        mode="before"
    )
    @classmethod
    def strip_whitespace(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v

    @model_validator(mode="after")
    def resolve_supabase_keys(self) -> "Settings":
        key = (self.SUPABASE_SERVICE_ROLE_KEY or self.SUPABASE_KEY or "").strip()
        self.SUPABASE_SERVICE_ROLE_KEY = key
        self.SUPABASE_KEY = key
        return self

    @field_validator("SUPABASE_JWT_ISSUER", "SUPABASE_JWKS_URL", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: object) -> Optional[str]:
        if isinstance(v, str):
            val = v.strip()
            return val if val else None
        return v if isinstance(v, str) else None

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

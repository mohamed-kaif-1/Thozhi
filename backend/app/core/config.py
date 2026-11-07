from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "THOZHI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    
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
    SUPABASE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator(
        "GNANI_API_KEY", "SARVAM_API_KEY", "GEMINI_API_KEY",
        "SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_JWT_SECRET",
        mode="before"
    )
    @classmethod
    def strip_whitespace(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

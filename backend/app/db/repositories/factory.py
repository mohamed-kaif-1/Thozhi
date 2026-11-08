import logging
from backend.app.core.config import settings
from backend.app.db.repositories.base import BaseRepository
from backend.app.db.repositories.memory import InMemoryRepository
from backend.app.db.repositories.supabase import SupabaseRepository

logger = logging.getLogger(__name__)

_global_repository_instance: BaseRepository | None = None

def get_repository() -> BaseRepository:
    """
    Factory creating or returning the configured data repository singleton.
    - Explicit development/test environments select InMemoryRepository (unless Supabase is explicitly configured).
    - Production MUST require valid SUPABASE_URL and SUPABASE_KEY; missing or invalid credentials raise a fatal RuntimeError.
    - Production never silently falls back to RAM.
    """
    global _global_repository_instance
    if _global_repository_instance is not None:
        return _global_repository_instance

    env = getattr(settings, "ENVIRONMENT", "development").lower()
    supabase_url = getattr(settings, "SUPABASE_URL", "").strip()
    supabase_key = (
        getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")
        or getattr(settings, "SUPABASE_KEY", "")
    ).strip()
    has_supabase = bool(supabase_url and supabase_key)
    configured_backend = (
        getattr(settings, "DATA_BACKEND", "")
        or getattr(settings, "REPOSITORY_BACKEND", "")
        or ""
    ).strip().lower()

    if env == "production" or configured_backend == "supabase":
        if not has_supabase:
            raise RuntimeError(
                "CRITICAL STARTUP FAILURE: DATA_BACKEND=supabase (or production environment) requires valid "
                "SUPABASE_URL and SUPABASE_KEY. Silent fallback to InMemoryRepository is strictly prohibited."
            )
        if not (supabase_url.startswith("http://") or supabase_url.startswith("https://")):
            raise RuntimeError(
                f"CRITICAL STARTUP FAILURE: Invalid SUPABASE_URL configured: '{supabase_url}'. "
                "Must be a valid HTTP/HTTPS URL."
            )
        logger.info("Initializing SupabaseRepository for durable persistence.")
        _global_repository_instance = SupabaseRepository()
    else:
        logger.info(f"Initializing InMemoryRepository for '{env}' environment.")
        _global_repository_instance = InMemoryRepository()

    return _global_repository_instance

def reset_repository() -> None:
    """
    Resets the repository singleton. Used exclusively for unit and integration testing.
    """
    global _global_repository_instance
    _global_repository_instance = None

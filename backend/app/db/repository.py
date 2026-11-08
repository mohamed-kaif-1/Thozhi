"""
THOZHI Central Repository Module.
Preserves backwards compatibility for routers and test suites while delegating
to the modular repository abstraction in `backend.app.db.repositories`.
"""
from backend.app.db.repositories import (
    BaseRepository,
    InMemoryRepository,
    InMemoryStore,
    SupabaseRepository,
    get_repository
)
from backend.app.db.repositories.memory import get_utc_now

# Global repository singleton instance
store = get_repository()

__all__ = [
    "BaseRepository",
    "InMemoryRepository",
    "InMemoryStore",
    "SupabaseRepository",
    "get_repository",
    "get_utc_now",
    "store",
]

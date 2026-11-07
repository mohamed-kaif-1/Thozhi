import httpx
import logging
from typing import Dict, List, Optional, Any
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class SupabaseClient:
    """
    Asynchronous lightweight Supabase REST Client utilizing httpx.
    Interfaces directly with Supabase PostgREST endpoints and Row Level Security.
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        jwt_secret: Optional[str] = None
    ):
        self.base_url = (base_url or settings.SUPABASE_URL).rstrip("/")
        self.api_key = api_key or settings.SUPABASE_KEY
        self.jwt_secret = jwt_secret or settings.SUPABASE_JWT_SECRET

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    def _get_headers(self, user_token: Optional[str] = None) -> Dict[str, str]:
        auth_bearer = user_token if user_token else self.api_key
        return {
            "apikey": self.api_key,
            "Authorization": f"Bearer {auth_bearer}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    async def check_health(self) -> Dict[str, Any]:
        """
        Pings Supabase PostgREST OpenAPI schema discovery endpoint.
        """
        if not self.is_configured:
            return {"status": "unconfigured", "detail": "SUPABASE_URL or SUPABASE_KEY missing in .env"}

        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.get(f"{self.base_url}/", headers=self._get_headers())
                if res.status_code == 200:
                    return {"status": "connected", "url": self.base_url, "code": 200}
                return {"status": "error", "code": res.status_code, "detail": res.text}
        except Exception as exc:
            logger.warning(f"Supabase health check connection failed: {exc}")
            return {"status": "offline", "detail": str(exc)}

    async def list_records(
        self,
        table: str,
        filters: Optional[Dict[str, str]] = None,
        user_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetches records from a Supabase table with PostgREST query parameters.
        """
        if not self.is_configured:
            return []

        url = f"{self.base_url}/{table}"
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(
                    url,
                    headers=self._get_headers(user_token),
                    params=filters or {}
                )
                if res.status_code == 200:
                    return res.json()
                logger.warning(f"Supabase list {table} failed: {res.status_code} - {res.text}")
                return []
        except Exception as exc:
            logger.error(f"Error querying Supabase table {table}: {exc}")
            return []

    async def insert_record(
        self,
        table: str,
        data: Dict[str, Any],
        user_token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Inserts a single record into Supabase table.
        """
        if not self.is_configured:
            return None

        url = f"{self.base_url}/{table}"
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(
                    url,
                    headers=self._get_headers(user_token),
                    json=data
                )
                if res.status_code in (200, 201):
                    results = res.json()
                    return results[0] if isinstance(results, list) and len(results) > 0 else results
                logger.warning(f"Supabase insert {table} failed: {res.status_code} - {res.text}")
                return None
        except Exception as exc:
            logger.error(f"Error inserting into Supabase table {table}: {exc}")
            return None

supabase_client = SupabaseClient()

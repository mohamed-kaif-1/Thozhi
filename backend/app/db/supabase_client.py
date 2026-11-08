import httpx
import logging
from typing import Dict, List, Optional, Any, Union
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class SupabaseClientError(Exception):
    """Base exception for all Supabase client operations."""
    pass

class SupabaseConnectionError(SupabaseClientError):
    """Raised when the client fails to establish a network connection to Supabase."""
    pass

class SupabaseQueryError(SupabaseClientError):
    """Raised when PostgREST returns an HTTP 4xx or 5xx database error."""
    def __init__(self, status_code: int, detail: str):
        super().__init__(f"PostgREST query failed ({status_code}): {detail}")
        self.status_code = status_code
        self.detail = detail

class SupabaseAuthError(SupabaseClientError):
    """Raised when authentication credentials or JWT tokens are missing, invalid, or unauthorized."""
    pass

class SupabaseClient:
    """
    Lightweight, dual-mode (sync + async) Supabase REST Client utilizing httpx.
    Interfaces directly with Supabase PostgREST endpoints and Row Level Security.
    Enforces request-scoped end-user JWT propagation and fails closed on missing tokens.
    Silent fallback to service-role authorization is strictly prohibited for user operations.
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        jwt_secret: Optional[str] = None
    ):
        raw_url = (base_url if base_url is not None else getattr(settings, "SUPABASE_URL", "")).rstrip("/")
        if raw_url and "supabase.co" in raw_url and not raw_url.endswith("/rest/v1"):
            raw_url = f"{raw_url}/rest/v1"
        self.base_url = raw_url
        self.api_key = api_key if api_key is not None else (
            getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")
            or getattr(settings, "SUPABASE_KEY", "")
        )
        self.jwt_secret = jwt_secret if jwt_secret is not None else getattr(settings, "SUPABASE_JWT_SECRET", "")

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    def _get_headers(
        self,
        user_token: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        allow_service_role: bool = False
    ) -> Dict[str, str]:
        """
        Builds PostgREST authorization headers.
        Strictly enforces request-scoped token isolation without mutating client instance state.
        Fails closed: if user_token is absent and allow_service_role is False, raises SupabaseAuthError.
        """
        token = (user_token or "").strip()
        if not token:
            if not allow_service_role:
                raise SupabaseAuthError(
                    "CRITICAL SECURITY REJECTION: Protected database operation called without authenticated user token. "
                    "Silent fallback to service-role authorization is strictly prohibited."
                )
            auth_bearer = self.api_key
        else:
            auth_bearer = token

        headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {auth_bearer}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def _request_sync(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, str]] = None,
        json: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        user_token: Optional[str] = None,
        allow_service_role: bool = False
    ) -> httpx.Response:
        """
        Executes synchronous HTTP request against PostgREST endpoint with robust error handling.
        """
        if not self.is_configured:
            raise SupabaseConnectionError("Supabase client is not configured with SUPABASE_URL / SUPABASE_KEY")

        url = f"{self.base_url}/{path.lstrip('/')}"
        req_headers = self._get_headers(user_token=user_token, extra_headers=headers, allow_service_role=allow_service_role)

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.request(method, url, params=params, json=json, headers=req_headers)
                if res.status_code in (200, 201, 204, 206):
                    return res
                if res.status_code in (401, 403):
                    logger.error(f"Supabase auth failure ({res.status_code}): {res.text}")
                    raise SupabaseAuthError(f"Supabase authorization failed ({res.status_code}): {res.text}")
                logger.error(f"Supabase request {method} {url} failed: {res.status_code} - {res.text}")
                raise SupabaseQueryError(res.status_code, res.text)
        except httpx.RequestError as exc:
            logger.error(f"Network error communicating with Supabase at {url}: {exc}")
            raise SupabaseConnectionError(f"Network request to Supabase failed: {exc}")

    async def _request_async(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, str]] = None,
        json: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        user_token: Optional[str] = None,
        allow_service_role: bool = False
    ) -> httpx.Response:
        """
        Executes asynchronous HTTP request against PostgREST endpoint with robust error handling.
        """
        if not self.is_configured:
            raise SupabaseConnectionError("Supabase client is not configured with SUPABASE_URL / SUPABASE_KEY")

        url = f"{self.base_url}/{path.lstrip('/')}"
        req_headers = self._get_headers(user_token=user_token, extra_headers=headers, allow_service_role=allow_service_role)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.request(method, url, params=params, json=json, headers=req_headers)
                if res.status_code in (200, 201, 204, 206):
                    return res
                if res.status_code in (401, 403):
                    logger.error(f"Supabase auth failure ({res.status_code}): {res.text}")
                    raise SupabaseAuthError(f"Supabase authorization failed ({res.status_code}): {res.text}")
                logger.error(f"Supabase request {method} {url} failed: {res.status_code} - {res.text}")
                raise SupabaseQueryError(res.status_code, res.text)
        except httpx.RequestError as exc:
            logger.error(f"Network error communicating with Supabase at {url}: {exc}")
            raise SupabaseConnectionError(f"Network request to Supabase failed: {exc}")

    # =========================================================================
    # SYNCHRONOUS OPERATIONS (For Domain Repository CRUD)
    # =========================================================================

    def list_records_sync(
        self,
        table: str,
        filters: Optional[Dict[str, str]] = None,
        user_token: Optional[str] = None,
        allow_service_role: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Synchronously lists records from PostgREST with parameterized filters.
        Enforces user token propagation.
        """
        res = self._request_sync("GET", table, params=filters, user_token=user_token, allow_service_role=allow_service_role)
        if not res.text or res.status_code == 204:
            return []
        data = res.json()
        return data if isinstance(data, list) else [data]

    def get_record_sync(
        self,
        table: str,
        filters: Dict[str, str],
        user_token: Optional[str] = None,
        allow_service_role: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Synchronously retrieves a single record from PostgREST matching filters.
        Enforces user token propagation.
        """
        records = self.list_records_sync(table, filters, user_token=user_token, allow_service_role=allow_service_role)
        return records[0] if records else None

    def insert_record_sync(
        self,
        table: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        user_token: Optional[str] = None,
        upsert: bool = False,
        allow_service_role: bool = False
    ) -> Any:
        """
        Synchronously inserts one or more records into PostgREST table.
        Enforces user token propagation.
        """
        headers = {"Prefer": "resolution=merge-duplicates,return=representation"} if upsert else {"Prefer": "return=representation"}
        res = self._request_sync("POST", table, json=data, headers=headers, user_token=user_token, allow_service_role=allow_service_role)
        if not res.text or res.status_code == 204:
            return data
        result = res.json()
        if isinstance(data, dict) and isinstance(result, list):
            return result[0] if len(result) > 0 else data
        return result

    def update_record_sync(
        self,
        table: str,
        filters: Dict[str, str],
        data: Dict[str, Any],
        user_token: Optional[str] = None,
        allow_service_role: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Synchronously updates records matching filters in PostgREST table.
        Enforces user token propagation.
        """
        res = self._request_sync(
            "PATCH",
            table,
            params=filters,
            json=data,
            headers={"Prefer": "return=representation"},
            user_token=user_token,
            allow_service_role=allow_service_role
        )
        if not res.text or res.status_code == 204:
            return []
        result = res.json()
        return result if isinstance(result, list) else [result]

    def delete_record_sync(
        self,
        table: str,
        filters: Dict[str, str],
        user_token: Optional[str] = None,
        allow_service_role: bool = False
    ) -> int:
        """
        Synchronously deletes records matching filters from PostgREST table.
        Returns the number of deleted records.
        Enforces user token propagation.
        """
        res = self._request_sync(
            "DELETE",
            table,
            params=filters,
            headers={"Prefer": "return=representation"},
            user_token=user_token,
            allow_service_role=allow_service_role
        )
        if not res.text or res.status_code == 204:
            return 0
        try:
            result = res.json()
            if isinstance(result, list):
                return len(result)
            return 1
        except Exception:
            return 1

    def rpc_sync(
        self,
        function_name: str,
        params: Dict[str, Any],
        user_token: Optional[str] = None,
        allow_service_role: bool = False
    ) -> Any:
        """
        Synchronously executes a PostgreSQL stored procedure / database function.
        Enforces user token propagation.
        """
        res = self._request_sync("POST", f"rpc/{function_name}", json=params, user_token=user_token, allow_service_role=allow_service_role)
        return res.json() if res.text else None

    # =========================================================================
    # ASYNCHRONOUS OPERATIONS (For Async Callers & Backward Compatibility)
    # =========================================================================

    async def check_health(self) -> Dict[str, Any]:
        """
        Pings Supabase PostgREST OpenAPI schema discovery endpoint.
        Uses explicit administrative authorization since no tenant data is queried.
        """
        if not self.is_configured:
            return {"status": "unconfigured", "detail": "SUPABASE_URL or SUPABASE_KEY missing in .env"}

        try:
            res = await self._request_async("GET", "", allow_service_role=True)
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
        user_token: Optional[str] = None,
        allow_service_role: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Asynchronously fetches records from a Supabase table with PostgREST query parameters.
        """
        res = await self._request_async("GET", table, params=filters, user_token=user_token, allow_service_role=allow_service_role)
        if not res.text or res.status_code == 204:
            return []
        data = res.json()
        return data if isinstance(data, list) else [data]

    async def insert_record(
        self,
        table: str,
        data: Dict[str, Any],
        user_token: Optional[str] = None,
        allow_service_role: bool = False
    ) -> Dict[str, Any]:
        """
        Asynchronously inserts a single record into Supabase table.
        """
        res = await self._request_async("POST", table, json=data, headers={"Prefer": "return=representation"}, user_token=user_token, allow_service_role=allow_service_role)
        if not res.text or res.status_code == 204:
            return data
        result = res.json()
        return result[0] if isinstance(result, list) and len(result) > 0 else result

    async def update_record(
        self,
        table: str,
        filters: Dict[str, str],
        data: Dict[str, Any],
        user_token: Optional[str] = None,
        allow_service_role: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Asynchronously updates records in Supabase table.
        """
        res = await self._request_async("PATCH", table, params=filters, json=data, headers={"Prefer": "return=representation"}, user_token=user_token, allow_service_role=allow_service_role)
        if not res.text or res.status_code == 204:
            return []
        result = res.json()
        return result if isinstance(result, list) else [result]

    async def delete_record(
        self,
        table: str,
        filters: Dict[str, str],
        user_token: Optional[str] = None,
        allow_service_role: bool = False
    ) -> int:
        """
        Asynchronously deletes records from Supabase table.
        """
        res = await self._request_async("DELETE", table, params=filters, headers={"Prefer": "return=representation"}, user_token=user_token, allow_service_role=allow_service_role)
        if not res.text or res.status_code == 204:
            return 0
        try:
            result = res.json()
            if isinstance(result, list):
                return len(result)
            return 1
        except Exception:
            return 1

supabase_client = SupabaseClient()

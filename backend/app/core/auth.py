import re
import jwt
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import PyJWKClient

from backend.app.core.config import settings

# HTTPBearer scheme configured with auto_error=False to provide RFC 6750 compliant error details
bearer_scheme = HTTPBearer(auto_error=False)

FALLBACK_DEV_JWT_SECRET = "2fdce485-4335-4f5e-8d2d-a35012f01c4e"

# Module-level cached JWKS client
_jwks_client: Optional[PyJWKClient] = None
_cached_jwks_url: Optional[str] = None


def get_jwt_secrets() -> List[str]:
    """
    Returns the list of configured Supabase JWT secrets to support key rotation.
    If multiple secrets are provided (comma-separated), all are tried in sequence.
    In production, a non-empty secret or valid JWKS URL is mandatory; otherwise fails closed.
    """
    raw = (getattr(settings, "SUPABASE_JWT_SECRET", "") or "").strip()
    if raw:
        secrets = [s.strip() for s in raw.split(",") if s.strip()]
        if secrets:
            return secrets

    # If no symmetric secret is configured, check if production allows running without it
    env = getattr(settings, "ENVIRONMENT", "development").lower()
    jwks_url = getattr(settings, "SUPABASE_JWKS_URL", None)
    if env == "production" and not jwks_url:
        raise RuntimeError("CRITICAL SECURITY ERROR: SUPABASE_JWT_SECRET or SUPABASE_JWKS_URL must be configured in production.")

    return [FALLBACK_DEV_JWT_SECRET]


def get_jwt_secret() -> str:
    """
    Backward-compatible helper returning the primary active symmetric secret.
    """
    return get_jwt_secrets()[0]


def get_jwks_client() -> Optional[PyJWKClient]:
    """
    Returns a cached PyJWKClient for asymmetric signing keys (RS256, ES256)
    supporting automatic key rotation via JWKS.
    """
    global _jwks_client, _cached_jwks_url

    jwks_url = getattr(settings, "SUPABASE_JWKS_URL", None)
    if not jwks_url and getattr(settings, "SUPABASE_URL", None):
        # Derive standard Supabase JWKS endpoint: https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json
        base_url = re.sub(r"/rest/v1/?$", "", settings.SUPABASE_URL).rstrip("/")
        if base_url:
            jwks_url = f"{base_url}/auth/v1/.well-known/jwks.json"

    if not jwks_url:
        return None

    if _jwks_client is None or _cached_jwks_url != jwks_url:
        _jwks_client = PyJWKClient(jwks_url, cache_keys=True, max_cached_keys=16, lifespan=3600)
        _cached_jwks_url = jwks_url

    return _jwks_client


class AuthenticatedUser(BaseModel):
    """
    Represents a cryptographically verified user identity extracted from a valid JWT.
    """
    id: UUID = Field(..., description="Verified tenant user UUID from JWT sub claim")
    email: Optional[str] = Field(None, description="User email if present in claims")
    role: str = Field("authenticated", description="Role claim from JWT (e.g. 'authenticated')")
    token: str = Field(..., description="Raw access token for propagation to downstream database/services")


def create_test_jwt(
    user_id: UUID,
    role: str = "authenticated",
    email: Optional[str] = None,
    expires_in: int = 3600,
    secret: Optional[str] = None,
    aud: str = "authenticated",
    iss: Optional[str] = None,
    algorithm: str = "HS256",
    nbf_offset: Optional[int] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
    omit_iss: bool = False,
    omit_aud: bool = False
) -> str:
    """
    Generates a cryptographically valid JWT for testing, seeding, and automated verification.
    By default, includes realistic issuer and audience claims matching system configuration.
    """
    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in)).timestamp()),
    }
    if not omit_aud and aud:
        payload["aud"] = aud
    if not omit_iss:
        effective_iss = iss if iss is not None else getattr(settings, "SUPABASE_JWT_ISSUER", None)
        if effective_iss:
            payload["iss"] = effective_iss
    if nbf_offset is not None:
        payload["nbf"] = int((now + timedelta(seconds=nbf_offset)).timestamp())
    if email:
        payload["email"] = email
    if extra_claims:
        payload.update(extra_claims)

    signing_secret = secret if secret is not None else get_jwt_secret()
    return jwt.encode(payload, signing_secret, algorithm=algorithm)


def verify_jwt(
    token: str,
    secret: Optional[str] = None,
    audience: Optional[str] = None,
    issuer: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validates token signature, algorithm, expiration, not-before, audience, issuer, and claims.
    Fails closed on any inconsistency or unauthorized access attempt.
    """
    if not token or not isinstance(token, str):
        raise jwt.InvalidTokenError("Token must be a non-empty string")

    # 1. Inspect unverified header for algorithm & kid
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise jwt.InvalidTokenError(f"Malformed JWT header: {exc}")

    alg = header.get("alg")
    if not alg or alg.lower() == "none":
        raise jwt.InvalidTokenError("Prohibited or missing JWT algorithm 'none'")

    allowed_algs: List[str] = getattr(settings, "SUPABASE_JWT_ALGORITHMS", ["HS256", "RS256", "ES256"])
    if alg not in allowed_algs:
        raise jwt.InvalidTokenError(f"Unsupported JWT algorithm '{alg}'. Allowed: {allowed_algs}")

    # 2. Inspect unverified payload for claims preflight
    try:
        unverified = jwt.decode(token, options={"verify_signature": False, "verify_exp": False})
    except jwt.PyJWTError as exc:
        raise jwt.InvalidTokenError(f"Malformed JWT payload: {exc}")

    # 3. Configure audience validation
    configured_aud = audience or getattr(settings, "SUPABASE_JWT_AUDIENCE", "authenticated")
    decode_options = {
        "verify_signature": True,
        "verify_exp": True,
        "verify_nbf": True,
        "verify_iat": True,
        "require": ["sub", "exp"]
    }

    if configured_aud:
        # Support both configured audience and standard "authenticated"
        if configured_aud != "authenticated":
            decode_audience = [configured_aud, "authenticated"]
        else:
            decode_audience = "authenticated"
        decode_options["verify_aud"] = True
        decode_options["require"].append("aud")
    else:
        decode_audience = None
        decode_options["verify_aud"] = False

    # 4. Configure issuer validation
    expected_iss = issuer if issuer is not None else getattr(settings, "SUPABASE_JWT_ISSUER", None)
    if expected_iss:
        decode_issuer = expected_iss
        decode_options["verify_iss"] = True
        decode_options["require"].append("iss")
    else:
        decode_issuer = None
        decode_options["verify_iss"] = False

    # 5. Cryptographic signature verification
    payload: Optional[Dict[str, Any]] = None

    if alg in ["RS256", "ES256"]:
        # Asymmetric key verification via JWKS
        jwks_client = get_jwks_client()
        if not jwks_client:
            raise jwt.InvalidTokenError(f"Asymmetric algorithm '{alg}' requires configured JWKS endpoint")
        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=[alg],
                audience=decode_audience,
                issuer=decode_issuer,
                leeway=10,
                options=decode_options
            )
        except (
            jwt.ExpiredSignatureError,
            jwt.InvalidAudienceError,
            jwt.InvalidIssuerError,
            jwt.MissingRequiredClaimError,
            jwt.ImmatureSignatureError,
        ):
            raise
        except jwt.PyJWTError as exc:
            raise jwt.InvalidTokenError(f"JWKS verification failed: {exc}")
    else:
        # Symmetric key verification with key rotation support
        secrets_to_try = [secret] if secret is not None else get_jwt_secrets()
        last_sig_error = None
        for s in secrets_to_try:
            try:
                payload = jwt.decode(
                    token,
                    s,
                    algorithms=[alg],
                    audience=decode_audience,
                    issuer=decode_issuer,
                    leeway=10,
                    options=decode_options
                )
                last_sig_error = None
                break
            except jwt.InvalidSignatureError as sig_err:
                last_sig_error = sig_err
                continue
            except (
                jwt.ExpiredSignatureError,
                jwt.ImmatureSignatureError,
                jwt.InvalidAudienceError,
                jwt.InvalidIssuerError,
                jwt.MissingRequiredClaimError,
            ):
                raise
            except jwt.PyJWTError as exc:
                raise jwt.InvalidTokenError(str(exc))

        if payload is None:
            if last_sig_error:
                raise last_sig_error
            raise jwt.InvalidTokenError("Token signature verification failed")

    # 6. Validate subject claim is valid UUID
    sub_val = payload.get("sub")
    if not sub_val:
        raise jwt.InvalidTokenError("Missing 'sub' claim in JWT")
    try:
        UUID(str(sub_val))
    except (ValueError, TypeError):
        raise jwt.InvalidTokenError(f"Invalid 'sub' claim in JWT: '{sub_val}' is not a valid UUID")

    # 7. Validate role is not anonymous
    role_val = payload.get("role", "authenticated")
    if role_val == "anon":
        raise jwt.InvalidTokenError("Anonymous 'anon' role is not permitted to access authenticated user data")

    return payload


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> AuthenticatedUser:
    """
    FastAPI Security Dependency.
    Extracts Bearer token from the Authorization header, verifies signature and claims,
    and returns an AuthenticatedUser principal.
    Fails closed with HTTP 401 on missing or invalid tokens.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": 'Bearer error="unauthorized", error_description="Missing Authorization header"'}
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme; Bearer scheme required",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token", error_description="Bearer scheme required"'}
        )

    raw_token = (credentials.credentials or "").strip()
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token cannot be empty",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token", error_description="Token cannot be empty"'}
        )

    try:
        payload = verify_jwt(raw_token)
        user_uuid = UUID(payload["sub"])
        return AuthenticatedUser(
            id=user_uuid,
            email=payload.get("email"),
            role=payload.get("role", "authenticated"),
            token=raw_token
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token", error_description="The access token has expired"'}
        )
    except jwt.ImmatureSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is not yet valid (nbf in future)",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token", error_description="The token is not yet valid"'}
        )
    except (jwt.InvalidAudienceError, jwt.InvalidIssuerError, jwt.InvalidSignatureError, jwt.InvalidTokenError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {exc}",
            headers={"WWW-Authenticate": f'Bearer error="invalid_token", error_description="{str(exc)}"'}
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {exc}",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'}
        )

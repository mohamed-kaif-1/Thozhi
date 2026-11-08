import pytest
import jwt
from uuid import uuid4, UUID
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from backend.app.core.auth import (
    verify_jwt,
    create_test_jwt,
    get_jwt_secrets,
    get_jwt_secret,
    FALLBACK_DEV_JWT_SECRET,
)
from backend.app.core.config import settings
from fastapi.testclient import TestClient
from backend.app.main import app

raw_client = TestClient(app)
raw_client._skip_test_auth = True


# ==============================================================================
# P2: JWT SECURITY HARDENING UNIT TESTS
# ==============================================================================

def test_p2_valid_hs256_token_accepted():
    """Valid standard HS256 token must decode and verify successfully."""
    user_id = uuid4()
    token = create_test_jwt(user_id=user_id, role="authenticated", email="user@example.com")
    payload = verify_jwt(token)
    assert payload["sub"] == str(user_id)
    assert payload["role"] == "authenticated"
    assert payload["email"] == "user@example.com"


def test_p2_expired_token_rejected():
    """Token with exp in the past must raise ExpiredSignatureError."""
    user_id = uuid4()
    expired_token = create_test_jwt(user_id=user_id, expires_in=-120)
    with pytest.raises(jwt.ExpiredSignatureError):
        verify_jwt(expired_token)


def test_p2_not_before_future_token_rejected():
    """Token with nbf in the future must raise ImmatureSignatureError."""
    user_id = uuid4()
    future_token = create_test_jwt(user_id=user_id, nbf_offset=300)
    with pytest.raises(jwt.ImmatureSignatureError):
        verify_jwt(future_token)


def test_p2_wrong_audience_rejected():
    """Token with an incorrect aud claim must raise InvalidAudienceError."""
    user_id = uuid4()
    wrong_aud_token = create_test_jwt(user_id=user_id, aud="some-other-audience")
    with pytest.raises(jwt.InvalidAudienceError):
        verify_jwt(wrong_aud_token, audience="authenticated")


def test_p2_valid_audience_accepted():
    """Token with matching aud claim must verify successfully."""
    user_id = uuid4()
    valid_aud_token = create_test_jwt(user_id=user_id, aud="authenticated")
    payload = verify_jwt(valid_aud_token, audience="authenticated")
    assert payload["aud"] == "authenticated"


def test_p2_wrong_issuer_rejected():
    """Token with mismatched iss claim must raise InvalidIssuerError."""
    user_id = uuid4()
    token = create_test_jwt(user_id=user_id, iss="https://wrong-issuer.com/auth/v1")
    with pytest.raises(jwt.InvalidIssuerError):
        verify_jwt(token, issuer="https://correct-issuer.supabase.co/auth/v1")


def test_p2_valid_issuer_accepted():
    """Token with matching iss claim must be accepted."""
    user_id = uuid4()
    issuer_url = "https://project.supabase.co/auth/v1"
    token = create_test_jwt(user_id=user_id, iss=issuer_url)
    payload = verify_jwt(token, issuer=issuer_url)
    assert payload["iss"] == issuer_url


def test_p2_missing_issuer_rejected_when_configured():
    """When SUPABASE_JWT_ISSUER is configured, a token missing the iss claim must be rejected."""
    user_id = uuid4()
    issuer_url = "https://bwzqudaaxfubtbgwmevo.supabase.co/auth/v1"
    token_no_iss = create_test_jwt(user_id=user_id, omit_iss=True)
    with patch.object(settings, "SUPABASE_JWT_ISSUER", issuer_url):
        with pytest.raises(jwt.MissingRequiredClaimError, match='Token is missing the "iss" claim'):
            verify_jwt(token_no_iss)


def test_p2_wrong_issuer_rejected_with_settings_issuer():
    """When SUPABASE_JWT_ISSUER is configured, a token with wrong iss must raise InvalidIssuerError."""
    user_id = uuid4()
    issuer_url = "https://bwzqudaaxfubtbgwmevo.supabase.co/auth/v1"
    token_wrong_iss = create_test_jwt(user_id=user_id, iss="https://attacker.supabase.co/auth/v1")
    with patch.object(settings, "SUPABASE_JWT_ISSUER", issuer_url):
        with pytest.raises(jwt.InvalidIssuerError):
            verify_jwt(token_wrong_iss)


def test_p2_valid_issuer_accepted_with_settings_issuer():
    """When SUPABASE_JWT_ISSUER is configured, a token with matching iss must be accepted."""
    user_id = uuid4()
    issuer_url = "https://bwzqudaaxfubtbgwmevo.supabase.co/auth/v1"
    token_valid = create_test_jwt(user_id=user_id, iss=issuer_url)
    with patch.object(settings, "SUPABASE_JWT_ISSUER", issuer_url):
        payload = verify_jwt(token_valid)
        assert payload["iss"] == issuer_url
        assert payload["sub"] == str(user_id)


def test_p2_missing_issuer_accepted_when_unconfigured():
    """When SUPABASE_JWT_ISSUER is None/unconfigured, tokens without iss must be accepted."""
    user_id = uuid4()
    token_no_iss = create_test_jwt(user_id=user_id, omit_iss=True)
    with patch.object(settings, "SUPABASE_JWT_ISSUER", None):
        payload = verify_jwt(token_no_iss, issuer=None)
        assert payload["sub"] == str(user_id)


def test_p2_missing_audience_rejected():
    """When audience is required, a token missing the aud claim must be rejected."""
    user_id = uuid4()
    token_no_aud = create_test_jwt(user_id=user_id, omit_aud=True)
    with pytest.raises(jwt.MissingRequiredClaimError, match='Token is missing the "aud" claim'):
        verify_jwt(token_no_aud)


def test_p2_invalid_signature_rejected():
    """Tampered token signature must raise InvalidSignatureError."""
    user_id = uuid4()
    wrong_sig_token = create_test_jwt(user_id=user_id, secret="wrong-secret-different-key-32chars")
    with pytest.raises(jwt.InvalidSignatureError):
        verify_jwt(wrong_sig_token)


def test_p2_missing_subject_rejected():
    """Token missing the 'sub' claim must raise InvalidTokenError."""
    now = datetime.now(timezone.utc)
    iss_val = (
        getattr(settings, "SUPABASE_JWT_ISSUER", None)
        or "https://bwzqudaaxfubtbgwmevo.supabase.co/auth/v1"
    )
    payload = {
        "role": "authenticated",
        "aud": "authenticated",
        "iss": iss_val,
        "exp": int((now + timedelta(hours=1)).timestamp())
    }
    token = jwt.encode(payload, get_jwt_secret(), algorithm="HS256")
    with pytest.raises(jwt.InvalidTokenError, match='sub'):
        verify_jwt(token)


def test_p2_malformed_uuid_subject_rejected():
    """Token whose 'sub' claim is not a valid RFC 4122 UUID must be rejected."""
    now = datetime.now(timezone.utc)
    iss_val = (
        getattr(settings, "SUPABASE_JWT_ISSUER", None)
        or "https://bwzqudaaxfubtbgwmevo.supabase.co/auth/v1"
    )
    payload = {
        "sub": "non-uuid-username",
        "role": "authenticated",
        "aud": "authenticated",
        "iss": iss_val,
        "exp": int((now + timedelta(hours=1)).timestamp())
    }
    token = jwt.encode(payload, get_jwt_secret(), algorithm="HS256")
    with pytest.raises(jwt.InvalidTokenError, match="not a valid UUID"):
        verify_jwt(token)


def test_p2_anonymous_role_rejected():
    """Token with role 'anon' must be rejected to prevent unauthenticated access."""
    user_id = uuid4()
    anon_token = create_test_jwt(user_id=user_id, role="anon")
    with pytest.raises(jwt.InvalidTokenError, match="Anonymous 'anon' role is not permitted"):
        verify_jwt(anon_token)


def test_p2_none_algorithm_rejected():
    """Unsigned token using 'none' algorithm must be rejected."""
    iss_val = (
        getattr(settings, "SUPABASE_JWT_ISSUER", None)
        or "https://bwzqudaaxfubtbgwmevo.supabase.co/auth/v1"
    )
    payload = {
        "sub": str(uuid4()),
        "role": "authenticated",
        "aud": "authenticated",
        "iss": iss_val,
        "exp": 9999999999
    }
    none_token = jwt.encode(payload, key="", algorithm="none")
    with pytest.raises(jwt.InvalidTokenError, match="algorithm"):
        verify_jwt(none_token)


def test_p2_unsupported_algorithm_rejected():
    """Token signed with an algorithm outside the allowed list must be rejected."""
    user_id = uuid4()
    now = datetime.now(timezone.utc)
    iss_val = (
        getattr(settings, "SUPABASE_JWT_ISSUER", None)
        or "https://bwzqudaaxfubtbgwmevo.supabase.co/auth/v1"
    )
    payload = {
        "sub": str(user_id),
        "role": "authenticated",
        "aud": "authenticated",
        "iss": iss_val,
        "exp": int((now + timedelta(hours=1)).timestamp())
    }
    # Encode with HS512 (not in default allowlist of HS256, RS256, ES256)
    with patch.object(settings, "SUPABASE_JWT_ALGORITHMS", ["HS256", "RS256", "ES256"]):
        hs512_token = jwt.encode(payload, get_jwt_secret(), algorithm="HS512")
        with pytest.raises(jwt.InvalidTokenError, match="Unsupported JWT algorithm"):
            verify_jwt(hs512_token)


def test_p2_symmetric_key_rotation_support():
    """
    Verifies that multiple symmetric secrets can be configured for key rotation.
    Tokens signed with either active or rotated secondary secret must both be accepted.
    """
    secret_old = "old-legacy-secret-key-32-chars-long-1"
    secret_new = "new-active-secret-key-32-chars-long-2"
    multi_secrets_env = f"{secret_new},{secret_old}"

    user_a = uuid4()
    user_b = uuid4()

    token_new = create_test_jwt(user_id=user_a, secret=secret_new)
    token_old = create_test_jwt(user_id=user_b, secret=secret_old)

    with patch.object(settings, "SUPABASE_JWT_SECRET", multi_secrets_env):
        payload_new = verify_jwt(token_new)
        assert payload_new["sub"] == str(user_a)

        payload_old = verify_jwt(token_old)
        assert payload_old["sub"] == str(user_b)


def test_p2_asymmetric_jwks_verification():
    """
    Verifies that asymmetric tokens (RS256) are validated via JWKS keys.
    """
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization

    # Generate test RSA key pair
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    user_id = uuid4()
    now = datetime.now(timezone.utc)
    iss_val = (
        getattr(settings, "SUPABASE_JWT_ISSUER", None)
        or "https://bwzqudaaxfubtbgwmevo.supabase.co/auth/v1"
    )
    payload = {
        "sub": str(user_id),
        "role": "authenticated",
        "aud": "authenticated",
        "iss": iss_val,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp())
    }
    rs256_token = jwt.encode(payload, pem_private, algorithm="RS256", headers={"kid": "test-key-id"})

    # Mock JWKS client returning the test public key
    mock_jwk_client = MagicMock()
    mock_signing_key = MagicMock()
    mock_signing_key.key = public_key
    mock_jwk_client.get_signing_key_from_jwt.return_value = mock_signing_key

    with patch("backend.app.core.auth.get_jwks_client", return_value=mock_jwk_client):
        verified_payload = verify_jwt(rs256_token)
        assert verified_payload["sub"] == str(user_id)


def test_p2_asymmetric_es256_jwks_verification():
    """
    Verifies that Elliptic Curve (ES256 / P-256) tokens matching Supabase standard are validated via JWKS.
    """
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization

    # Generate test EC P-256 key pair
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    user_id = uuid4()
    now = datetime.now(timezone.utc)
    iss_val = (
        getattr(settings, "SUPABASE_JWT_ISSUER", None)
        or "https://bwzqudaaxfubtbgwmevo.supabase.co/auth/v1"
    )
    payload = {
        "sub": str(user_id),
        "role": "authenticated",
        "aud": "authenticated",
        "iss": iss_val,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp())
    }
    es256_token = jwt.encode(payload, pem_private, algorithm="ES256", headers={"kid": "2fdce485-4335-4f5e-8d2d-a35012f01c4e"})

    # Mock JWKS client returning the EC public key
    mock_jwk_client = MagicMock()
    mock_signing_key = MagicMock()
    mock_signing_key.key = public_key
    mock_jwk_client.get_signing_key_from_jwt.return_value = mock_signing_key

    with patch("backend.app.core.auth.get_jwks_client", return_value=mock_jwk_client):
        verified_payload = verify_jwt(es256_token)
        assert verified_payload["sub"] == str(user_id)
        assert verified_payload["iss"] == iss_val


def test_p2_fail_closed_in_production_when_config_missing():
    """
    In production mode, if neither SUPABASE_JWT_SECRET nor SUPABASE_JWKS_URL is set,
    get_jwt_secrets must fail closed by raising RuntimeError.
    """
    with patch.object(settings, "ENVIRONMENT", "production"):
        with patch.object(settings, "SUPABASE_JWT_SECRET", ""):
            with patch.object(settings, "SUPABASE_JWKS_URL", None):
                with pytest.raises(RuntimeError, match="CRITICAL SECURITY ERROR"):
                    get_jwt_secrets()


def test_p2_endpoint_http_401_on_tampered_jwt():
    """Calling an actual protected endpoint with a tampered token returns HTTP 401."""
    user_id = uuid4()
    token = create_test_jwt(user_id=user_id)
    tampered = token[:-4] + "zzzz"
    res = raw_client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {tampered}"})
    assert res.status_code == 401
    assert "WWW-Authenticate" in res.headers

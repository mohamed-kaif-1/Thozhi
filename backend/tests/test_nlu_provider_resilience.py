import pytest
import httpx
from unittest.mock import MagicMock, patch
from uuid import uuid4

from backend.app.core.config import settings
from backend.app.core.errors import NLUProviderException
from backend.app.providers.nlu.mock import MockNLUProvider
from backend.app.providers.nlu.gemini import GeminiNLUProvider
from backend.app.routers.captures import get_nlu_provider, safe_extract_intent
from backend.app.main import validate_production_configuration


# ==============================================================================
# P1: NLU PROVIDER RESILIENCE & FAILURE HANDLING TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_mock_provider_strictly_forbidden_in_production():
    """Attempting to instantiate MockNLUProvider in production mode must raise RuntimeError."""
    with patch.object(settings, "ENVIRONMENT", "production"):
        with pytest.raises(RuntimeError, match="MockNLUProvider is strictly forbidden in production"):
            MockNLUProvider()


def test_get_nlu_provider_missing_credentials_in_production_raises_503():
    """In production mode, if GEMINI_API_KEY is unset, get_nlu_provider raises NLUProviderException (503)."""
    with patch.object(settings, "ENVIRONMENT", "production"):
        with patch.object(settings, "GEMINI_API_KEY", ""):
            with pytest.raises(NLUProviderException) as exc_info:
                get_nlu_provider()
            assert exc_info.value.status_code == 503
            assert exc_info.value.error_code == "NLU_CREDENTIALS_MISSING"


def test_get_nlu_provider_in_development_returns_mock_when_key_unset():
    """In development mode with no API key, get_nlu_provider safely returns MockNLUProvider."""
    with patch.object(settings, "ENVIRONMENT", "development"):
        with patch.object(settings, "GEMINI_API_KEY", ""):
            provider = get_nlu_provider()
            assert isinstance(provider, MockNLUProvider)


@pytest.mark.asyncio
async def test_gemini_429_in_production_raises_503_rate_limited():
    """In production mode, Gemini HTTP 429 must raise 503 NLU_RATE_LIMITED and NEVER silently switch to mock."""
    with patch.object(settings, "ENVIRONMENT", "production"):
        with patch.object(settings, "GEMINI_API_KEY", "test-fake-key"):
            mock_provider = MagicMock(spec=GeminiNLUProvider)
            mock_provider.extract_intent.side_effect = RuntimeError("Gemini API returned 429: RESOURCE_EXHAUSTED quota exceeded")

            with patch("backend.app.routers.captures.get_nlu_provider", return_value=mock_provider):
                with pytest.raises(NLUProviderException) as exc_info:
                    await safe_extract_intent(text="Submit financial report tomorrow", user_timezone="Asia/Kolkata")
                assert exc_info.value.status_code == 503
                assert exc_info.value.error_code == "NLU_RATE_LIMITED"


@pytest.mark.asyncio
async def test_gemini_timeout_in_production_raises_504_gateway_timeout():
    """In production mode, Gemini timeout must raise 504 NLU_TIMEOUT without fallback."""
    with patch.object(settings, "ENVIRONMENT", "production"):
        with patch.object(settings, "GEMINI_API_KEY", "test-fake-key"):
            mock_provider = MagicMock(spec=GeminiNLUProvider)
            mock_provider.extract_intent.side_effect = httpx.TimeoutException("Connection timed out after 20.0s")

            with patch("backend.app.routers.captures.get_nlu_provider", return_value=mock_provider):
                with pytest.raises(NLUProviderException) as exc_info:
                    await safe_extract_intent(text="Call customer tomorrow 10am", user_timezone="Asia/Kolkata")
                assert exc_info.value.status_code == 504
                assert exc_info.value.error_code == "NLU_TIMEOUT"


@pytest.mark.asyncio
async def test_gemini_malformed_response_in_production_raises_502_bad_gateway():
    """In production mode, malformed provider response raises 502 NLU_PROVIDER_ERROR without fallback."""
    with patch.object(settings, "ENVIRONMENT", "production"):
        with patch.object(settings, "GEMINI_API_KEY", "test-fake-key"):
            mock_provider = MagicMock(spec=GeminiNLUProvider)
            mock_provider.extract_intent.side_effect = ValueError("JSONDecodeError: Unterminated string starting at line 1")

            with patch("backend.app.routers.captures.get_nlu_provider", return_value=mock_provider):
                with pytest.raises(NLUProviderException) as exc_info:
                    await safe_extract_intent(text="Schedule dentist appointment", user_timezone="Asia/Kolkata")
                assert exc_info.value.status_code == 502
                assert exc_info.value.error_code == "NLU_PROVIDER_ERROR"


@pytest.mark.asyncio
async def test_mock_output_accurately_labeled_with_mock_provenance():
    """Mock extractions must be marked with is_mock=True and model_provider='mock'."""
    with patch.object(settings, "ENVIRONMENT", "development"):
        provider = MockNLUProvider()
        result = await provider.extract_intent("Client call tomorrow at 10am")
        assert result.is_mock is True
        assert result.model_provider == "mock"
        assert result.model_version.startswith("mock")


@pytest.mark.asyncio
async def test_asr_dispatcher_unaffected_by_nlu_state():
    """Gnani and Sarvam ASR dispatcher architecture operates independently of NLU providers."""
    from backend.app.providers.asr.dispatcher import ASRDispatcher
    dispatcher = ASRDispatcher()
    assert dispatcher.gnani is not None
    assert dispatcher.gnani.__class__.__name__ == "GnaniPrismaProvider"
    assert dispatcher.sarvam is not None
    assert dispatcher.sarvam.__class__.__name__ == "SarvamSaarasProvider"


# ==============================================================================
# P2: PRODUCTION JWT CONFIGURATION FAIL-CLOSED TESTS
# ==============================================================================

def test_production_fails_closed_when_issuer_missing():
    """Production startup must fail closed if SUPABASE_JWT_ISSUER is missing."""
    with patch.object(settings, "ENVIRONMENT", "production"):
        with patch.object(settings, "SUPABASE_JWT_ISSUER", None):
            with patch.object(settings, "SUPABASE_JWT_SECRET", "valid-secret-key-32-chars-minimum"):
                with patch.object(settings, "SUPABASE_URL", "https://example.supabase.co"):
                    with patch.object(settings, "SUPABASE_SERVICE_ROLE_KEY", "valid-key"):
                        with patch.object(settings, "GEMINI_API_KEY", "valid-key"):
                            with pytest.raises(RuntimeError, match="SUPABASE_JWT_ISSUER must be configured in production"):
                                validate_production_configuration()


def test_production_fails_closed_when_gemini_key_missing():
    """Production startup must fail closed if GEMINI_API_KEY is missing."""
    with patch.object(settings, "ENVIRONMENT", "production"):
        with patch.object(settings, "GEMINI_API_KEY", ""):
            with patch.object(settings, "SUPABASE_JWT_ISSUER", "https://example.supabase.co/auth/v1"):
                with patch.object(settings, "SUPABASE_JWT_SECRET", "valid-secret-key-32-chars-minimum"):
                    with patch.object(settings, "SUPABASE_URL", "https://example.supabase.co"):
                        with patch.object(settings, "SUPABASE_SERVICE_ROLE_KEY", "valid-key"):
                            with pytest.raises(RuntimeError, match="GEMINI_API_KEY must be configured in production"):
                                validate_production_configuration()


def test_production_fails_closed_when_supabase_url_missing():
    """Production startup must fail closed if SUPABASE_URL is missing."""
    with patch.object(settings, "ENVIRONMENT", "production"):
        with patch.object(settings, "SUPABASE_URL", ""):
            with patch.object(settings, "SUPABASE_JWT_ISSUER", "https://example.supabase.co/auth/v1"):
                with patch.object(settings, "SUPABASE_JWT_SECRET", "valid-secret-key-32-chars-minimum"):
                    with patch.object(settings, "SUPABASE_SERVICE_ROLE_KEY", "valid-key"):
                        with patch.object(settings, "GEMINI_API_KEY", "valid-key"):
                            with pytest.raises(RuntimeError, match="SUPABASE_URL must be configured in production"):
                                validate_production_configuration()

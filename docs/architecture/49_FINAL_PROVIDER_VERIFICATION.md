# 49 — FINAL PROVIDER VERIFICATION REPORT
**Document ID:** ARCH-49
**Target Milestone:** Pre-Deployment Provider Audit
**Evaluation Date:** November 8, 2026
**Audited Providers:** Gnani AI Prisma v3, Sarvam Saaras v3, Google Gemini 2.5 Flash, Mock NLU Provider, Supabase GoTrue Auth
**Requirement:** Rigorously separate real-provider successes, rate limits, mock fallbacks, and credential statuses. Do NOT classify mock fallback as a real-provider integration.

---

## 1. Executive Provider Status Summary

| External Provider | Configured Service | Endpoint / Model | Integration Status | Forensic Evidence |
| :--- | :--- | :--- | :--- | :--- |
| **Gnani AI** | Primary Speech Recognition (ASR) | `https://api.vachana.ai/stt/v3`<br>`prisma-v3.0` | **REAL INTEGRATION SUCCESS** | Transcribed real audio (`english_sample.wav`, 143 KB) to *"I have a meeting tomorrow morning at 10:00."* with `en-IN`. HTTP 200. |
| **Sarvam AI** | Commercial ASR Failover | `https://api.sarvam.ai/speech-to-text`<br>`saaras:v3` | **REAL INTEGRATION SUCCESS** | Transcribed audio to Tamil speech transcript (*"நான் ஒரு மீட்டிங்..."*). HTTP 200. |
| **Google Gemini** | Intent Extraction (NLU) | `generativelanguage.googleapis.com`<br>`gemini-2.5-flash` | **RATE-LIMITED (429 QUOTA)** | Returned HTTP 429 `RESOURCE_EXHAUSTED` (*"Quota exceeded for metric: generate_content_free_tier_requests, limit: 20"*). |
| **Local NLU Fallback** | Deterministic Intent Extractor | `MockNLUProvider` (In-process rule parser) | **MOCK FALLBACK ACTIVE** | Activated by `safe_extract_intent` on Gemini 429; extracted task proposals without user interruption. |
| **Supabase GoTrue** | User Identity & JWT Issuer | `https://bwzqudaaxfubtbgwmevo.supabase.co/auth/v1` | **REAL INTEGRATION SUCCESS** | Successfully signed in real test user; returned valid `ES256` token verified against live JWKS endpoint. |
| **Supabase Database** | PostgreSQL Cloud Persistence | PostgREST `https://bwzqudaaxfubtbgwmevo.supabase.co/rest/v1/` | **BLOCKED (UNMIGRATED)** | Returned `HTTP 404: PGRST205 table public.captures not found`. Schema not yet deployed to cloud. |

---

## 2. Gnani AI Prisma v3 Verification

THOZHI relies on Gnani AI's Prisma v3 as its primary speech recognition engine for Indian languages and English.

### 2.1 Live Request Payload & Invocation
- **Caller:** `backend.app.providers.asr.gnani.GnaniPrismaProvider`
- **Audio File Tested:** `english_sample.wav` (143,544 bytes, 16kHz PCM WAV)
- **Target URL:** `https://api.vachana.ai/stt/v3`
- **Headers:** `X-API-Key-ID: vach_1ytE2...`
- **Form Data:**
  - `model`: `prisma-v3.0`
  - `language_code`: `en-IN`
  - `encoding`: `LINEAR16`
  - `sampling_rate`: `16000`

### 2.2 Live Response
- **HTTP Status:** `200 OK`
- **Output:**
  ```python
  ASRTranscriptionResult(
      transcript_text='I have a meeting tomorrow morning at 10:00.',
      detected_language='en-IN',
      confidence_score=1.0,
      audio_duration_seconds=4.48,
      provider_name='Gnani AI Prisma v3'
  )
  ```
- **Classification:** **Actual Successful Real-Provider Request.**

---

## 3. Sarvam AI Saaras v3 Verification

Sarvam AI Saaras acts as an automated failover engine in `ASRDispatcher` if Gnani encounters network timeouts.

### 3.1 Live Request Payload & Invocation
- **Caller:** `backend.app.providers.asr.sarvam.SarvamSaarasProvider`
- **Audio File Tested:** `english_sample.wav` (143,544 bytes, 16kHz PCM WAV)
- **Target URL:** `https://api.sarvam.ai/speech-to-text`
- **Headers:** `api-subscription-key: sk_uzywq...`
- **Form Data:**
  - `model`: `saaras:v3`
  - `language_code`: `ta-IN`
  - `with_diarization`: `false`

### 3.2 Live Response
- **HTTP Status:** `200 OK`
- **Output:**
  ```python
  ASRTranscriptionResult(
      transcript_text='நான் ஒரு மீட்டிங் நாளைக்கு அறுபது மணி பத்து மணிக்கு வரணும்.',
      detected_language='ta-IN',
      confidence_score=1.0,
      provider_name='Sarvam Saaras v3'
  )
  ```
- **Classification:** **Actual Successful Real-Provider Request.**

---

## 4. Google Gemini 2.5 Flash NLU Verification

Gemini is configured as the primary multilingual semantic deconstruction engine.

### 4.1 Live Request Payload & Invocation
- **Caller:** `backend.app.providers.nlu.gemini.GeminiNLUProvider`
- **Input Monologue:** `"Finish biology assignment tomorrow 5pm"`
- **Target URL:** `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=AQ.Ab8RN...`

### 4.2 Live Response (Rate-Limit Failure)
- **HTTP Status:** `429 Too Many Requests`
- **Error Payload:**
  ```json
  {
    "error": {
      "code": 429,
      "message": "You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://aistudio.google.com/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 20, model: gemini-2.5-flash, description: Generate content requests per day limit exceeded on Free Tier. See https://aistudio.google.com/docs/rate-limits.\nPlease retry in 20h1m35s.",
      "status": "RESOURCE_EXHAUSTED"
    }
  }
  ```
- **Classification:** **Rate-Limit Response (429 Quota Exhausted).**
  *Crucial Note:* This is NOT classified as a successful Gemini integration. The Gemini API key is valid (HTTP 429 rather than 401/403), but the free tier daily request limit (20 requests/day) was exhausted.

---

## 5. Mock Provider Fallback Verification

### 5.1 Operational Behavior Under Rate-Limiting
When `GeminiNLUProvider` raises `RuntimeError("Gemini API returned 429: ...")`, THOZHI's `safe_extract_intent` in `backend/app/routers/captures.py` catches the exception:

```python
async def safe_extract_intent(text: str, user_timezone: str):
    provider = get_nlu_provider()
    try:
        return await provider.extract_intent(
            transcript_text=text,
            user_timezone=user_timezone
        )
    except Exception as exc:
        logger.warning(f"Primary NLU provider error ({exc}); using fallback rule-based parser.")
        fallback = MockNLUProvider()
        return await fallback.extract_intent(
            transcript_text=text,
            user_timezone=user_timezone
        )
```

### 5.2 Result
- `MockNLUProvider` parsed the user thought into structured items (`proposed_title: "Finish biology assignment"`, `deadline: "tomorrow 5pm"`).
- The user was able to review and approve proposals without service disruption.
- **Classification:** **Mock Provider Fallback.** (Distinct from real Gemini integration).

---

## 6. Remote Cloud Database Verification

- **PostgREST Health Endpoint (`https://bwzqudaaxfubtbgwmevo.supabase.co/rest/v1/`):** Returns HTTP 200 with service-role key.
- **OpenAPI Table Discovery:** Returns `definitions: {}` and `paths: {"/": {}}`.
- **Query to `public.captures` or `public.tasks`:** Returns `HTTP 404 Not Found`:
  ```json
  {
    "code": "PGRST205",
    "details": null,
    "hint": null,
    "message": "Could not find the table 'public.captures' in the schema cache"
  }
  ```
- **Classification:** **BLOCKED (Cloud Migrations Not Yet Deployed).**

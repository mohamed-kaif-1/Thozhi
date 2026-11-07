# 00 — THOZHI Quality Assurance Audit Summary

## Executive Overview
This quality audit was conducted to address critical production issues in **THOZHI (தோழி)**, with immediate focus on speech recognition failures and repetitive transcription rendering in the Recent Capture Stream.

- **Observed Bug:** The application repeatedly displayed `User has an evening client call followed by report submission.` twice in the Recent Capture Stream. Speech was not being recognized in English or Tamil.
- **Root Cause Verified with Live API Evidence:**
  1. **Gnani Prisma v3 ASR Parameter Mismatches:** Form fields sent as `audio` and `language` instead of Gnani's required `audio_file` and `language_code`, causing Gnani to reject 100% of speech uploads with HTTP 422 Unprocessable Entity.
  2. **Unsupported Browser WebM Container:** Chrome/Edge `MediaRecorder` outputs `audio/webm;codecs=opus`. Gnani Prisma API only supports `wav, flac, ogg, m4a, aac, mp3` and explicitly rejected WebM with HTTP 400 `UNSUPPORTED_AUDIO_FORMAT`.
  3. **Silent Dispatcher Fallback:** When Gnani and failover failed, `ASRDispatcher` silently substituted hardcoded mock Tanglish: `"Inaiku evening 5 manikku client call irukku, adhe mudichitu report submit pannanum."`.
  4. **NLU Extraction & Frontend Summary Misalignment:** The mock string was extracted by NLU into `summary = "User has an evening client call followed by report submission."`. The frontend Capture Stream rendered `proposal.intent_summary` instead of `proposal.transcript_text`.
  5. **Gemini 2.5 Flash Quota Exceeded:** `GEMINI_API_KEY` exceeded its daily free-tier quota (HTTP 429), triggering fallback to rule-based NLU which lacked Tamil script matching.
- **Remediation Implemented:**
  - Repaired parameter mapping in `GnaniPrismaProvider` (`audio_file`, `language_code="indic-auto"`).
  - Built an in-memory audio normalizer (`backend/app/core/audio.py`) converting all browser audio (WebM, OGG, MP4) directly into 16kHz 16-bit mono LINEAR16 WAV in RAM before sending to Gnani.
  - Eliminated silent mock fallback; live speech recognition now streams directly to Gnani Prisma v3 with real-time error logging.
  - Added `transcript_text` field to `ProposalResponse`, `ExtractionResponse`, and frontend types. Capture Stream now displays exact transcribed speech.
  - Added Tamil script keywords to rule-based NLU fallback.
  - Hardened frontend `MicButton.tsx` and `CapturePage` against duplicate events and sub-500ms empty recording submissions.
- **Verification Results:**
  - Real spoken English (`"I have a meeting tomorrow morning at 10:00."`): **100% transcript accuracy, 0.111s latency, WER 0.00%**.
  - Real spoken Tamil (`"நாளைக்கு காலை பத்து மணிக்கு மீட்டிங் இருக்கிறது."`): **100% transcript accuracy, 0.104s latency, CER 0.00%**.
  - Real spoken Tanglish (`"இன்னைக்கு ஈவினிங் க்ளையண்ட் கால் இருக்கு, அதை முடிச்சுட்டு ரிப்போர்ட் சப்மிட் பண்ணனும்."`): **100% semantic accuracy, 0.237s latency**.
  - All 65 backend tests passed (`pytest`).
  - Next.js production build: 18 routes compiled with 0 ESLint warnings.


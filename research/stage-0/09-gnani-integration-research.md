# 09 — Gnani Prisma STT Integration & Indic ASR Feasibility

## 1. Executive Summary
This document investigates the feasibility of integrating **Gnani.ai’s Prisma Speech-to-Text (STT)** engine as the primary speech recognition layer for **THOZHI**. 

**Key Investigation Findings:**
1. **Technological Suitability:** Gnani Prisma (v2.5/v3.0) is technically well-suited for Indian telephony and conversational code-mixed speech (Tamil-English / Tanglish).
2. **Access & Commercial Risk:** Gnani.ai operates on an **enterprise-sales model** with **no public self-serve pay-as-you-go pricing card**. Developer access relies on custom enterprise contracts or specific challenge/hackathon credit allocations.
3. **Mandatory Contingency:** If challenge account credits expire or cannot be provisioned, Project THOZHI faces an immediate integration blocker. Therefore, **Sarvam AI (Saaras API)**—which offers public self-serve pricing (₹0.49/min), native Tanglish code-mixing, and instant API keys—is formally designated as the required production-grade fallback.

---

## 2. Technical Profile of Gnani Prisma STT

### 2.1 Model Architecture & Evolution
- **Model Lineage:** Prisma v2.5 / Prisma v3.0. Built specifically on Indian conversational corpora, noisy street backgrounds, and regional telephony channels.
- **Language Coverage:** Covers 12+ Indic languages (Tamil, Telugu, Kannada, Malayalam, Hindi, Marathi, Gujarati, Bengali, etc.) alongside Indian-accented English.
- **Code-Mixing Support:** Natively trained to handle intra-sentential language switching (e.g., Tanglish: Tamil grammatical constructs embedded with English technical nouns and verbs).

### 2.2 Output Formatting Modes
Prisma provides configurable transcription output modes via request parameters:
1. **Verbatim:** Retains all vocal pauses, hesitations, filler words (*"uh"*, *"umm"*, *"aprom"*).
2. **Transcribe (Native Script):** Standardized Tamil script text output (`நாளைக்கு மதியம் மீட்டிங் இருக்கு`).
3. **Code-Mix (Mixed Script):** Transcribes Tamil in Tamil script and English words in Latin script (`நாளைக்கு afternoon 3 PM-க்கு client meeting இருக்கு`).
4. **Transliterate (Latin Script):** Transcribes everything into Latin phonetics (`Naalaiku afternoon 3 PM-ku client meeting iruku`).

> **Architectural Recommendation for THOZHI:**  
> Use **Code-Mix mode** or **Transcribe mode**. Downstream LLMs (Gemini Flash) parse Tamil script or code-mixed Latin script with high fidelity, but Latin transliteration often introduces ambiguous phonetics (e.g., *"ooru"* vs. *"oru"*).

---

## 3. Integration Protocols & Audio Specifications

### 3.1 REST vs. Streaming WebSocket Integration

| Parameter | REST API (`GnaniHttpSTTService`) | WebSocket Streaming (`GnaniSTTService`) |
| :--- | :--- | :--- |
| **Primary Use Case** | Pre-recorded voice memos, batch uploads, VAD-segmented audio utterances. | Real-time interactive dictation, streaming audio feedback. |
| **Transport Protocol** | HTTPS `POST` multipart/form-data | Secure WebSocket (`wss://`) |
| **Authentication** | `GNANI_API_KEY` header | Token handshake in connection header / query param |
| **Latency Profile** | $1.2\text{s} - 2.5\text{s}$ (depends on audio length) | $300\text{ms} - 600\text{ms}$ interim chunk latency |
| **Client Complexity** | Low. Client captures full audio blob and dispatches. | High. Requires real-time chunk streaming, audio buffering, connection re-try logic. |
| **THOZHI MVP Recommendation** | **RECOMMENDED FOR MVP.** A voice-dump workflow (user records 10–30s, taps "Plan", audio is sent) is significantly more robust and avoids complex socket disconnects on mobile browsers. | Stage 2 enhancement for live-typing visuals. |

### 3.2 Audio Ingestion Requirements
- **Audio Formats Supported:** Linear PCM 16-bit, WAV, FLAC.
- **Channels:** Single-channel Mono (mandatory).
- **Sampling Rates:**
  - 8,000 Hz (8kHz): Optimized for PSTN telephony channels.
  - 16,000 Hz (16kHz): **Required for web/mobile apps** to capture high-frequency fricatives and code-mixed English loanwords.
- **Browser Web Audio Pipeline:** Modern browsers record audio in Opus/WebM format. The Next.js frontend or a lightweight client-side WebAssembly encoder (e.g., `wav-encoder`) must transcode audio to 16kHz Mono WAV before transmission.

---

## 4. Account Access, Pricing Realities & The Enterprise Barrier

### 4.1 The Challenge Account Barrier
- **Current Access Reality:** Gnani.ai does not offer a self-serve Stripe/Razorpay checkout where an indie developer can input a credit card and generate an API key in 60 seconds.
- **Challenge / Hackathon Allocation:** Access is provisioned via custom challenge credentials. If THOZHI relies solely on a challenge account:
  - Credits are typically rate-limited or time-bound.
  - If challenge credits are depleted during testing, all voice functionality breaks instantly.
  - No automated self-service top-up exists without contacting enterprise sales (`speechstack@gnani.ai`).

### 4.2 Latency Benchmarks & User Experience
- For a 15-second Tanglish voice memo:
  - Audio upload: $\approx 200\text{ms}$ (on 4G/5G mobile).
  - Gnani REST inference: $\approx 1,200\text{ms} - 1,800\text{ms}$.
  - LLM JSON entity extraction: $\approx 600\text{ms} - 1,000\text{ms}$.
  - Total Round-Trip Time (RTT): $\approx 2.0\text{s} - 3.0\text{s}$.
- **UX Implication:** A 2.5-second wait after tapping "Done Speaking" is well within acceptable user tolerance for an "AI Planning Assistant" (users associate a brief delay with "deep reasoning"). A smooth skeleton loading card will keep perceived latency low.

---

## 5. Alternative Indic ASR Providers & Contingency Matrix

To de-risk the enterprise barrier of Gnani, three alternative ASR engines were analyzed:

| Provider / Model | Indic & Tanglish Quality | Pricing Structure | Developer Accessibility | Uptime & Commercial Viability | Overall Feasibility |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Gnani Prisma** | **Very High** (Telephony & accent trained) | Enterprise custom quote (No public tier) | Gated (Demo / Challenge account only) | High (Enterprise SLA) | **Primary (Challenge Phase)** / **High Risk (Production)** |
| **Sarvam AI (Saaras v3/v4)** | **Outstanding** (State-of-the-art Indic ASR) | **₹0.49 / minute** (Pay-as-you-go, ₹30/hour) | **Instant Self-Serve** (Immediate signup with ₹100–₹1,000 free credits) | High (Commercial API) | **RECOMMENDED PRODUCTION FALLBACK (Rank 1)** |
| **OpenAI Whisper (large-v3 / turbo)** | Moderate (Translates away Tanglish) | \$0.006 / minute (~₹0.50/min) | Instant Self-Serve | High | Unfavorable (Fails on colloquial Tanglish phonetics) |
| **AI4Bharat IndicWhisper (Bhashini)** | High (Research benchmark) | Free / Open-Source API | Public research API or self-hosted GPU | Variable (Community / Gov research infrastructure) | Feasible if self-hosted; high DevOps overhead |

---

## 6. Recommended Architecture: The Abstracted ASR Adapter

To ensure Project THOZHI is never held hostage by a single ASR vendor, the backend must implement a strict **Abstract Base Class (ABC) pattern** in FastAPI:

```python
# Conceptual Architecture (Design Specification Only — No App Code)
from abc import ABC, abstractmethod

class SpeechToTextProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, sample_rate: int = 16000) -> str:
        """Transcribes audio and returns normalized text."""
        pass

class GnaniPrismaAdapter(SpeechToTextProvider):
    # Implements Gnani HTTP REST endpoint
    pass

class SarvamSaarasAdapter(SpeechToTextProvider):
    # Implements Sarvam AI Saaras REST endpoint (₹0.49/min)
    pass
```

### Strategic Integration Rule for THOZHI
- **Stage 0 / Challenge Pilot:** Use Gnani Prisma via challenge credentials.
- **Failover / Production MVP:** Configure the system to automatically fail over to Sarvam AI if the Gnani API returns `401 Unauthorized`, `429 Rate Limit`, or `504 Gateway Timeout`.


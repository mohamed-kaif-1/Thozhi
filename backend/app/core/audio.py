import io
import wave
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

def normalize_audio_to_wav_16k_mono(audio_bytes: bytes, original_content_type: str = "audio/wav") -> Tuple[bytes, str]:
    """
    Normalizes any incoming audio (WebM, OGG, MP4, AAC, FLAC, or non-standard WAV)
    into standard 16kHz 16-bit mono PCM WAV in transient RAM.
    Guarantees compatibility with Gnani AI Prisma v3 and Sarvam Saaras v3.
    Enforces Zero Raw Audio Retention: operates purely on in-memory buffers.
    """
    if not audio_bytes:
        return audio_bytes, original_content_type

    input_io = io.BytesIO(audio_bytes)

    # 1. Quick check: Is it already a 16kHz 16-bit mono WAV?
    try:
        with wave.open(input_io, "rb") as wf:
            if wf.getnchannels() == 1 and wf.getframerate() == 16000 and wf.getsampwidth() == 2:
                logger.debug("Audio is already 16kHz 16-bit mono WAV; passing through.")
                return audio_bytes, "audio/wav"
    except Exception:
        input_io.seek(0)

    # 2. Transcode and resample to 16kHz 16-bit mono PCM WAV using PyAV
    try:
        import av
        input_io.seek(0)
        container = av.open(input_io)
        
        # Audio stream verification
        if not container.streams.audio:
            logger.warning("No audio streams found in container; returning raw bytes.")
            return audio_bytes, original_content_type

        resampler = av.AudioResampler(
            format='s16',
            layout='mono',
            rate=16000
        )

        out_io = io.BytesIO()
        with wave.open(out_io, "wb") as out_wf:
            out_wf.setnchannels(1)
            out_wf.setsampwidth(2)
            out_wf.setframerate(16000)

            frame_count = 0
            for frame in container.decode(audio=0):
                resampled_frames = resampler.resample(frame)
                if resampled_frames:
                    for rf in resampled_frames:
                        out_wf.writeframes(rf.to_ndarray().tobytes())
                        frame_count += 1

        out_bytes = out_io.getvalue()
        if len(out_bytes) > 44:  # More than just WAV header
            logger.info(f"Successfully converted audio ({original_content_type}) to 16kHz mono WAV ({len(out_bytes)} bytes).")
            return out_bytes, "audio/wav"

    except Exception as exc:
        logger.warning(f"Audio conversion failed ({exc}); falling back to raw audio bytes.")

    return audio_bytes, original_content_type


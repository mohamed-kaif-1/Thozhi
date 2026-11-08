"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Mic,
  Square,
  Loader2,
  Radio,
  Check,
  X,
  Pause,
  Play,
  RotateCcw,
  AlertCircle,
  Languages,
} from "lucide-react";
import { cn } from "@/lib/utils";

export type AgentState = "IDLE" | "LISTENING" | "PROCESSING" | "SPEAKING" | "COMPLETED" | "ERROR";

export type CaptureLanguage = "tanglish" | "ta" | "en";

interface VoiceAgentOrbProps {
  onAudioRecorded: (blob: Blob, language: CaptureLanguage) => void;
  isProcessing?: boolean;
  initialLanguage?: CaptureLanguage;
  onLanguageChange?: (lang: CaptureLanguage) => void;
  className?: string;
  variant?: "hero" | "compact";
}

export const VoiceAgentOrb: React.FC<VoiceAgentOrbProps> = ({
  onAudioRecorded,
  isProcessing = false,
  initialLanguage = "tanglish",
  onLanguageChange,
  className,
  variant = "hero",
}) => {
  const [agentState, setAgentState] = useState<AgentState>("IDLE");
  const [selectedLanguage, setSelectedLanguage] = useState<CaptureLanguage>(initialLanguage);
  const [recordSeconds, setRecordSeconds] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [audioVolume, setAudioVolume] = useState(0); // 0.0 to 1.0 real RMS
  const [frequencyBars, setFrequencyBars] = useState<number[]>(new Array(24).fill(0.1));
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  // Synchronize processing state from parent
  useEffect(() => {
    if (isProcessing) {
      setAgentState("PROCESSING");
    } else {
      setAgentState((prev) => {
        if (prev === "PROCESSING") {
          return "COMPLETED";
        }
        return prev;
      });
    }
  }, [isProcessing]);

  useEffect(() => {
    if (agentState === "COMPLETED") {
      const t = setTimeout(() => {
        setAgentState("IDLE");
        setRecordSeconds(0);
      }, 2500);
      return () => clearTimeout(t);
    }
  }, [agentState]);

  const cleanupAudioNodes = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      try {
        audioContextRef.current.close();
      } catch {
        // ignore
      }
      audioContextRef.current = null;
    }
    analyserRef.current = null;
    setAudioVolume(0);
    setFrequencyBars(new Array(24).fill(0.1));
  }, []);

  useEffect(() => {
    return () => {
      cleanupAudioNodes();
    };
  }, [cleanupAudioNodes]);

  // Real-time audio analyser loop
  const startAudioAnalysis = (stream: MediaStream) => {
    try {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const audioCtx = new AudioCtx();
      audioContextRef.current = audioCtx;

      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      analyser.smoothingTimeConstant = 0.75;
      analyserRef.current = analyser;

      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const renderAudioVisuals = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);

        // Calculate RMS / volume level
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
          sum += dataArray[i];
        }
        const average = sum / bufferLength;
        const normalizedVol = Math.min(1.0, average / 120); // Scale comfortably
        setAudioVolume(normalizedVol);

        // Map to 24 frequency bars
        const bars: number[] = [];
        const step = Math.max(1, Math.floor(bufferLength / 24));
        for (let i = 0; i < 24; i++) {
          const idx = Math.min(bufferLength - 1, i * step);
          const rawVal = dataArray[idx] / 255;
          // Add a baseline minimum height so bars are always visible
          bars.push(Math.max(0.1, rawVal));
        }
        setFrequencyBars(bars);

        animationFrameRef.current = requestAnimationFrame(renderAudioVisuals);
      };

      renderAudioVisuals();
    } catch (e) {
      console.warn("Web Audio API frequency analysis unsupported:", e);
    }
  };

  const startRecording = async () => {
    setErrorMessage(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      streamRef.current = stream;

      let mimeType = "audio/webm;codecs=opus";
      if (typeof MediaRecorder !== "undefined") {
        if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
          mimeType = "audio/webm;codecs=opus";
        } else if (MediaRecorder.isTypeSupported("audio/mp4")) {
          mimeType = "audio/mp4";
        } else if (MediaRecorder.isTypeSupported("audio/ogg")) {
          mimeType = "audio/ogg";
        } else {
          mimeType = "";
        }
      }

      const mediaRecorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const recordedType = mediaRecorder.mimeType || "audio/webm";
        const audioBlob = new Blob(audioChunksRef.current, { type: recordedType });

        if (audioBlob.size > 500) {
          setAgentState("PROCESSING");
          onAudioRecorded(audioBlob, selectedLanguage);
        } else {
          setErrorMessage("Audio recording was too brief or empty. Please try again.");
          setAgentState("ERROR");
          setTimeout(() => setAgentState("IDLE"), 4000);
        }
        cleanupAudioNodes();
      };

      mediaRecorder.start(250);
      setAgentState("LISTENING");
      setIsPaused(false);
      setRecordSeconds(0);

      // Start Web Audio Frequency Analyser
      startAudioAnalysis(stream);

      // Start recording timer
      timerRef.current = setInterval(() => {
        setRecordSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      console.error("Microphone access error:", err);
      setErrorMessage("Microphone access was denied. Please allow microphone permissions in your browser.");
      setAgentState("ERROR");
      setTimeout(() => setAgentState("IDLE"), 5000);
    }
  };

  const finishRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
  };

  const cancelRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      // Discard recorded chunks
      audioChunksRef.current = [];
      mediaRecorderRef.current.stop();
    }
    cleanupAudioNodes();
    setAgentState("IDLE");
    setRecordSeconds(0);
    setIsPaused(false);
  };

  const togglePause = () => {
    if (!mediaRecorderRef.current) return;
    if (isPaused) {
      mediaRecorderRef.current.resume();
      setIsPaused(false);
      timerRef.current = setInterval(() => {
        setRecordSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      mediaRecorderRef.current.pause();
      setIsPaused(true);
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const handleLanguageSelect = (lang: CaptureLanguage) => {
    setSelectedLanguage(lang);
    if (onLanguageChange) {
      onLanguageChange(lang);
    }
  };

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? "0" : ""}${secs}`;
  };

  const isHero = variant === "hero";

  return (
    <div className={cn("flex flex-col items-center justify-center select-none w-full", className)}>
      {/* Outer Atmospheric Aura & Orb Container */}
      <div className={cn("relative flex items-center justify-center", isHero ? "w-64 h-64 md:w-72 md:h-72" : "w-44 h-44")}>
        {/* State 2: LISTENING — Audio-Reactive Concentric Waves */}
        {agentState === "LISTENING" && (
          <>
            {/* Wave 1: Closest Glow Ring */}
            <div
              className="absolute inset-0 rounded-full border border-sky-400/40 pointer-events-none transition-transform duration-75 ease-out"
              style={{
                transform: `scale(${1.15 + audioVolume * 0.45})`,
                opacity: 0.35 + audioVolume * 0.5,
                boxShadow: `0 0 ${25 + audioVolume * 45}px rgba(56, 189, 248, ${0.25 + audioVolume * 0.5})`,
              }}
            />
            {/* Wave 2: Middle Concentric Ring */}
            <div
              className="absolute inset-0 rounded-full border border-violet-400/30 pointer-events-none transition-transform duration-100 ease-out"
              style={{
                transform: `scale(${1.32 + audioVolume * 0.7})`,
                opacity: 0.2 + audioVolume * 0.4,
                boxShadow: `0 0 ${35 + audioVolume * 55}px rgba(139, 92, 246, ${0.2 + audioVolume * 0.4})`,
              }}
            />
            {/* Wave 3: Outer Horizon Ambient Ring */}
            <div
              className="absolute inset-0 rounded-full border border-cyan-300/20 pointer-events-none transition-transform duration-150 ease-out"
              style={{
                transform: `scale(${1.5 + audioVolume * 0.95})`,
                opacity: 0.12 + audioVolume * 0.3,
              }}
            />
          </>
        )}

        {/* State 3: PROCESSING — Swirling Ambient Halo */}
        {agentState === "PROCESSING" && (
          <div className="absolute -inset-4 rounded-full bg-gradient-to-tr from-sky-500/20 via-violet-500/25 to-amber-500/20 blur-xl animate-spin-slow pointer-events-none" />
        )}

        {/* State 1: IDLE — Soft Ambient Glow */}
        {agentState === "IDLE" && (
          <div className="absolute inset-2 rounded-full bg-gradient-to-tr from-sky-500/10 via-cyan-400/15 to-violet-500/10 blur-xl animate-pulse pointer-events-none" />
        )}

        {/* Central Luminous Orb Button */}
        <button
          type="button"
          onClick={() => {
            if (agentState === "IDLE") {
              startRecording();
            } else if (agentState === "LISTENING") {
              finishRecording();
            } else if (agentState === "ERROR") {
              startRecording();
            }
          }}
          disabled={agentState === "PROCESSING"}
          aria-label={
            agentState === "LISTENING"
              ? "Finish speaking and extract plan"
              : "Activate THOZHI AI Voice Agent"
          }
          className={cn(
            "relative rounded-full flex items-center justify-center transition-all duration-300 focus:outline-none z-10 cursor-pointer group shadow-2xl",
            isHero ? "w-36 h-36 md:w-44 md:h-44" : "w-24 h-24",
            agentState === "IDLE" && [
              "bg-gradient-to-tr from-sky-600 via-sky-500 to-cyan-400 dark:from-sky-700 dark:via-sky-600 dark:to-cyan-400",
              "border-2 border-white/60 dark:border-sky-300/40",
              "shadow-sky-500/30 hover:shadow-sky-400/50 hover:scale-105 active:scale-95 animate-orb-breathe",
            ],
            agentState === "LISTENING" && [
              "bg-gradient-to-tr from-rose-500 via-pink-600 to-amber-500",
              "border-2 border-amber-300/80 shadow-rose-500/40 scale-105",
            ],
            agentState === "PROCESSING" && [
              "bg-gradient-to-tr from-violet-600 via-indigo-600 to-sky-500",
              "border-2 border-violet-300/60 shadow-violet-500/40 animate-pulse cursor-wait",
            ],
            agentState === "COMPLETED" && [
              "bg-gradient-to-tr from-emerald-600 to-teal-500",
              "border-2 border-emerald-300 shadow-emerald-500/40 scale-105",
            ],
            agentState === "ERROR" && [
              "bg-gradient-to-tr from-red-600 to-rose-700",
              "border-2 border-rose-300 shadow-rose-500/40",
            ]
          )}
        >
          {/* Inner Dimensional Specular Glare (Apple-inspired glass depth) */}
          <div className="absolute inset-0 rounded-full bg-gradient-to-b from-white/30 via-transparent to-black/20 pointer-events-none" />
          <div className="absolute top-2.5 left-1/2 -translate-x-1/2 w-3/4 h-1/3 rounded-full bg-gradient-to-b from-white/35 to-transparent blur-[1px] pointer-events-none" />

          {/* Icon Presentation based on Agent State */}
          {agentState === "IDLE" && (
            <div className="flex flex-col items-center justify-center text-white drop-shadow-md">
              <Mic className={cn("transition-transform group-hover:scale-110", isHero ? "w-12 h-12 md:w-14 md:h-14" : "w-8 h-8")} />
            </div>
          )}

          {agentState === "LISTENING" && (
            <div className="flex flex-col items-center justify-center text-white drop-shadow-md">
              <Square className={cn("fill-white transition-transform animate-pulse", isHero ? "w-10 h-10 md:w-12 md:h-12" : "w-6 h-6")} />
            </div>
          )}

          {agentState === "PROCESSING" && (
            <div className="flex flex-col items-center justify-center text-white">
              <Loader2 className={cn("animate-spin text-white drop-shadow-lg", isHero ? "w-12 h-12 md:w-14 md:h-14" : "w-8 h-8")} />
            </div>
          )}

          {agentState === "COMPLETED" && (
            <div className="flex flex-col items-center justify-center text-white">
              <Check className={cn("stroke-[3] drop-shadow-lg animate-bounce", isHero ? "w-12 h-12 md:w-14 md:h-14" : "w-8 h-8")} />
            </div>
          )}

          {agentState === "ERROR" && (
            <div className="flex flex-col items-center justify-center text-white">
              <RotateCcw className={cn("drop-shadow-lg", isHero ? "w-10 h-10 md:w-12 md:h-12" : "w-7 h-7")} />
            </div>
          )}
        </button>
      </div>

      {/* Real-Time Waveform Frequency Visualizer */}
      {agentState === "LISTENING" && (
        <div className="w-full max-w-xs md:max-w-sm mt-3 px-4 py-2 flex items-center justify-center gap-1 h-12">
          {frequencyBars.map((height, i) => (
            <div
              key={i}
              className="w-1.5 md:w-2 rounded-full bg-gradient-to-t from-sky-500 to-cyan-300 dark:from-sky-400 dark:to-cyan-200 transition-all duration-75"
              style={{
                height: `${Math.max(6, height * 42)}px`,
                opacity: Math.max(0.3, height),
              }}
            />
          ))}
        </div>
      )}

      {/* State Feedback Pill & Action Controls */}
      <div className="mt-4 flex flex-col items-center text-center space-y-3">
        {agentState === "IDLE" && (
          <div className="space-y-1.5">
            <h3 className="text-sm md:text-base font-bold text-slate-800 dark:text-white tracking-tight">
              Tap Orb to Speak Your Thoughts
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm">
              Speak naturally in Tamil, Tanglish, or English. THOZHI will extract tasks, commitments, and deadlines.
            </p>
          </div>
        )}

        {agentState === "LISTENING" && (
          <div className="flex flex-col items-center space-y-3">
            {/* Live Timer Pill */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-rose-500/15 border border-rose-500/40 text-xs font-bold text-rose-600 dark:text-rose-300 animate-pulse shadow-sm">
              <Radio className="w-3.5 h-3.5 text-rose-500 animate-ping" />
              <span>Listening • {formatTimer(recordSeconds)}</span>
              <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
              <span className="text-[11px] text-slate-600 dark:text-slate-300 capitalize font-medium">
                {selectedLanguage}
              </span>
            </div>

            {/* In-Flight Controls: Pause, Finish, Cancel */}
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={togglePause}
                className="w-9 h-9 rounded-full bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-200 flex items-center justify-center transition"
                title={isPaused ? "Resume recording" : "Pause recording"}
                aria-label={isPaused ? "Resume recording" : "Pause recording"}
              >
                {isPaused ? <Play className="w-4 h-4 ml-0.5 fill-current" /> : <Pause className="w-4 h-4 fill-current" />}
              </button>

              <button
                type="button"
                onClick={finishRecording}
                className="px-4 py-2 rounded-full bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-bold text-xs flex items-center gap-1.5 shadow-md shadow-emerald-500/25 transition active:scale-95"
                title="Finish and process"
              >
                <Check className="w-3.5 h-3.5 stroke-[3]" />
                <span>Done</span>
              </button>

              <button
                type="button"
                onClick={cancelRecording}
                className="w-9 h-9 rounded-full bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/40 dark:hover:bg-rose-900/60 border border-rose-200 dark:border-rose-800 text-rose-600 dark:text-rose-400 flex items-center justify-center transition"
                title="Cancel capture"
                aria-label="Cancel capture"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {agentState === "PROCESSING" && (
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-sky-500/15 border border-sky-500/40 text-xs font-bold text-sky-600 dark:text-sky-300 shadow-sm animate-pulse">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>Transcribing with Gnani AI Prisma v3 & Extracting Plan...</span>
          </div>
        )}

        {agentState === "COMPLETED" && (
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-500/15 border border-emerald-500/40 text-xs font-bold text-emerald-600 dark:text-emerald-300 shadow-sm">
            <Check className="w-3.5 h-3.5" />
            <span>Transcription Complete • AI Proposal Ready</span>
          </div>
        )}

        {agentState === "ERROR" && (
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-rose-500/15 border border-rose-500/40 text-xs font-bold text-rose-600 dark:text-rose-300 shadow-sm">
            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
            <span>{errorMessage || "Audio capture failed. Please tap orb to retry."}</span>
          </div>
        )}

        {/* Language Selection Chips (Tanglish, Tamil, English) */}
        {agentState === "IDLE" && (
          <div className="flex items-center gap-1.5 pt-1">
            <div className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 flex items-center gap-1 mr-1">
              <Languages className="w-3 h-3" />
              <span>Language:</span>
            </div>
            {[
              { id: "tanglish", label: "Tanglish (தமிழ் + Eng)" },
              { id: "ta", label: "தமிழ்" },
              { id: "en", label: "English" },
            ].map((lang) => (
              <button
                key={lang.id}
                type="button"
                onClick={() => handleLanguageSelect(lang.id as CaptureLanguage)}
                className={cn(
                  "px-2.5 py-1 rounded-full text-[11px] font-bold transition-all",
                  selectedLanguage === lang.id
                    ? "bg-sky-500/15 text-sky-600 dark:text-sky-400 border border-sky-500/40 shadow-sm"
                    : "bg-slate-100 hover:bg-slate-200 dark:bg-slate-800/60 dark:hover:bg-slate-700/60 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700/60"
                )}
              >
                {lang.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

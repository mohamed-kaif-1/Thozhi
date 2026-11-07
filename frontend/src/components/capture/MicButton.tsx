"use client";

import React, { useState, useRef } from "react";
import { Mic, Square, Loader2, Sparkles, Radio } from "lucide-react";
import { cn } from "@/lib/utils";

interface MicButtonProps {
  onAudioRecorded: (blob: Blob) => void;
  isProcessing?: boolean;
  className?: string;
  size?: "sm" | "md" | "lg";
}

export const MicButton: React.FC<MicButtonProps> = ({
  onAudioRecorded,
  isProcessing = false,
  className,
  size = "md",
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordSeconds, setRecordSeconds] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
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
        onAudioRecorded(audioBlob);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start(250);
      setIsRecording(true);
      setRecordSeconds(0);

      timerRef.current = setInterval(() => {
        setRecordSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      console.error("Microphone access denied or error:", err);
      alert("Could not access microphone. Please ensure microphone permissions are granted in your browser.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? "0" : ""}${secs}`;
  };

  return (
    <div className="flex flex-col items-center gap-3">
      <button
        onClick={isRecording ? stopRecording : startRecording}
        disabled={isProcessing}
        aria-label={isRecording ? "Stop recording speech" : "Start speaking thoughts"}
        className={cn(
          "relative flex items-center justify-center rounded-2xl transition-all duration-300 focus:outline-none",
          size === "lg" ? "w-28 h-28" : size === "sm" ? "w-16 h-16" : "w-24 h-24",
          isRecording
            ? "bg-gradient-to-tr from-rose-600 to-amber-500 border border-amber-300 shadow-2xl shadow-rose-500/40 animate-pulse scale-105"
            : "bg-gradient-to-tr from-sky-600 via-sky-500 to-cyan-400 border border-sky-300/40 shadow-xl shadow-sky-500/25 hover:shadow-sky-400/40 hover:scale-105 active:scale-95",
          isProcessing && "opacity-50 cursor-not-allowed",
          className
        )}
      >
        {isProcessing ? (
          <Loader2 className="w-10 h-10 animate-spin text-white" />
        ) : isRecording ? (
          <Square className="w-9 h-9 fill-white text-white" />
        ) : (
          <Mic className="w-10 h-10 text-white" />
        )}

        {isRecording && (
          <span className="absolute -inset-2.5 rounded-2xl border-2 border-amber-400 animate-ping opacity-60 pointer-events-none" />
        )}
      </button>

      <div className="text-center space-y-1.5">
        {isRecording ? (
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-500/20 border border-rose-500/40 text-xs font-bold text-rose-300 animate-pulse">
            <Radio className="w-3.5 h-3.5 text-rose-400" />
            <span>Listening • {formatTimer(recordSeconds)}</span>
          </div>
        ) : isProcessing ? (
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-sky-500/20 border border-sky-500/40 text-xs font-bold text-sky-300">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>Transcribing with Gnani Prisma v3...</span>
          </div>
        ) : (
          <>
            <p className="text-xs font-bold text-slate-200">
              Tap to speak in Tamil, Tanglish, or English
            </p>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/30 text-[11px] font-bold text-sky-400">
              <Sparkles className="w-3 h-3 text-sky-400" />
              <span>Gnani AI Prisma v3 Engine</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

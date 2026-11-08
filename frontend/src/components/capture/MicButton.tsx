"use client";

import React from "react";
import { VoiceAgentOrb } from "./VoiceAgentOrb";

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
  const handleAudio = (blob: Blob) => {
    onAudioRecorded(blob);
  };

  return (
    <VoiceAgentOrb
      onAudioRecorded={handleAudio}
      isProcessing={isProcessing}
      className={className}
      variant={size === "sm" ? "compact" : "hero"}
    />
  );
};

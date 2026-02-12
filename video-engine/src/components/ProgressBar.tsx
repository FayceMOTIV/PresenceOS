import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";

interface ProgressBarProps {
  color?: string;
  height?: number;
  position?: "top" | "bottom";
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  color = "#FF6B35",
  height = 4,
  position = "bottom",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const progress = interpolate(frame, [0, durationInFrames], [0, 100], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        [position]: 0,
        height,
        backgroundColor: "rgba(255,255,255,0.2)",
        zIndex: 100,
      }}
    >
      <div
        style={{
          width: `${progress}%`,
          height: "100%",
          backgroundColor: color,
          transition: "width 0.1s linear",
        }}
      />
    </div>
  );
};

import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Img,
  Video,
  AbsoluteFill,
} from "remotion";

interface BackgroundMediaProps {
  src: string;
  type: "image" | "video";
  zoomDirection?: "in" | "out" | "none";
  overlayColor?: string;
  overlayOpacity?: number;
}

export const BackgroundMedia: React.FC<BackgroundMediaProps> = ({
  src,
  type,
  zoomDirection = "in",
  overlayColor = "#000000",
  overlayOpacity = 0.4,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const scale =
    zoomDirection === "in"
      ? interpolate(frame, [0, durationInFrames], [1.0, 1.15], {
          extrapolateRight: "clamp",
        })
      : zoomDirection === "out"
        ? interpolate(frame, [0, durationInFrames], [1.15, 1.0], {
            extrapolateRight: "clamp",
          })
        : 1;

  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ transform: `scale(${scale})` }}>
        {type === "image" ? (
          <Img
            src={src}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
            }}
          />
        ) : (
          <Video
            src={src}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
            }}
          />
        )}
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          backgroundColor: overlayColor,
          opacity: overlayOpacity,
        }}
      />
    </AbsoluteFill>
  );
};

import React from "react";
import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
} from "remotion";
import { AnimatedText } from "../components/AnimatedText";
import { BackgroundMedia } from "../components/BackgroundMedia";
import { ProgressBar } from "../components/ProgressBar";

export interface DailyStoryProps {
  slides: Array<{
    text: string;
    image: string;
    type?: "image" | "video";
  }>;
  brandName: string;
  primaryColor?: string;
  textPosition?: "top" | "center" | "bottom";
}

export const DailyStory: React.FC<DailyStoryProps> = ({
  slides,
  brandName,
  primaryColor = "#6C63FF",
  textPosition = "bottom",
}) => {
  const { fps, durationInFrames } = useVideoConfig();
  const frame = useCurrentFrame();

  const perSlide = Math.floor(durationInFrames / Math.max(slides.length, 1));

  const justifyMap = {
    top: "flex-start" as const,
    center: "center" as const,
    bottom: "flex-end" as const,
  };

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {slides.map((slide, index) => (
        <Sequence
          key={index}
          from={index * perSlide}
          durationInFrames={perSlide}
        >
          {/* Background */}
          <BackgroundMedia
            src={slide.image}
            type={slide.type || "image"}
            zoomDirection={index % 2 === 0 ? "in" : "out"}
            overlayOpacity={0.3}
          />

          {/* Slide transition */}
          <AbsoluteFill
            style={{
              opacity: interpolate(
                frame - index * perSlide,
                [0, 8],
                [0, 1],
                { extrapolateRight: "clamp" }
              ),
            }}
          >
            <AbsoluteFill
              style={{
                display: "flex",
                flexDirection: "column",
                justifyContent: justifyMap[textPosition],
                padding: 50,
                paddingTop: textPosition === "top" ? 100 : 50,
                paddingBottom: textPosition === "bottom" ? 120 : 50,
              }}
            >
              <div
                style={{
                  backgroundColor: "rgba(0,0,0,0.5)",
                  backdropFilter: "blur(8px)",
                  borderRadius: 16,
                  padding: "20px 28px",
                  maxWidth: "90%",
                  alignSelf:
                    textPosition === "center" ? "center" : "flex-start",
                }}
              >
                <AnimatedText
                  text={slide.text}
                  fontSize={32}
                  fontWeight={600}
                  color="#FFFFFF"
                  style="slide"
                  align={textPosition === "center" ? "center" : "left"}
                />
              </div>
            </AbsoluteFill>
          </AbsoluteFill>
        </Sequence>
      ))}

      {/* Brand watermark at top */}
      <div
        style={{
          position: "absolute",
          top: 30,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          zIndex: 50,
        }}
      >
        <div
          style={{
            backgroundColor: "rgba(0,0,0,0.4)",
            backdropFilter: "blur(6px)",
            borderRadius: 20,
            padding: "6px 20px",
          }}
        >
          <span
            style={{
              color: "#FFFFFF",
              fontSize: 14,
              fontWeight: 600,
              fontFamily: "'Inter', sans-serif",
            }}
          >
            {brandName}
          </span>
        </div>
      </div>

      {/* Story progress segments */}
      <div
        style={{
          position: "absolute",
          top: 12,
          left: 16,
          right: 16,
          display: "flex",
          gap: 4,
          zIndex: 100,
        }}
      >
        {slides.map((_, index) => {
          const segStart = index * perSlide;
          const segEnd = (index + 1) * perSlide;
          const segProgress =
            frame < segStart
              ? 0
              : frame >= segEnd
                ? 100
                : interpolate(frame, [segStart, segEnd], [0, 100], {
                    extrapolateRight: "clamp",
                  });

          return (
            <div
              key={index}
              style={{
                flex: 1,
                height: 3,
                borderRadius: 2,
                backgroundColor: "rgba(255,255,255,0.3)",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${segProgress}%`,
                  height: "100%",
                  backgroundColor: primaryColor,
                }}
              />
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

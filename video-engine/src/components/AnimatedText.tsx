import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";

interface AnimatedTextProps {
  text: string;
  fontSize?: number;
  color?: string;
  fontWeight?: number;
  delay?: number;
  style?: "fade" | "slide" | "typewriter" | "scale";
  align?: "left" | "center" | "right";
}

export const AnimatedText: React.FC<AnimatedTextProps> = ({
  text,
  fontSize = 48,
  color = "#FFFFFF",
  fontWeight = 700,
  delay = 0,
  style = "slide",
  align = "center",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const adjustedFrame = Math.max(0, frame - delay);

  let opacity = 1;
  let transform = "none";

  switch (style) {
    case "fade": {
      opacity = interpolate(adjustedFrame, [0, 15], [0, 1], {
        extrapolateRight: "clamp",
      });
      break;
    }
    case "slide": {
      const slideProgress = spring({
        frame: adjustedFrame,
        fps,
        config: { damping: 12, stiffness: 80 },
      });
      opacity = slideProgress;
      transform = `translateY(${interpolate(slideProgress, [0, 1], [40, 0])}px)`;
      break;
    }
    case "typewriter": {
      const charsToShow = Math.floor(
        interpolate(adjustedFrame, [0, text.length * 2], [0, text.length], {
          extrapolateRight: "clamp",
        })
      );
      return (
        <div
          style={{
            fontSize,
            fontWeight,
            color,
            textAlign: align,
            fontFamily: "'Inter', sans-serif",
            lineHeight: 1.3,
          }}
        >
          {text.slice(0, charsToShow)}
          <span style={{ opacity: frame % 20 > 10 ? 0 : 1 }}>|</span>
        </div>
      );
    }
    case "scale": {
      const scaleProgress = spring({
        frame: adjustedFrame,
        fps,
        config: { damping: 10, stiffness: 100 },
      });
      opacity = scaleProgress;
      transform = `scale(${interpolate(scaleProgress, [0, 1], [0.5, 1])})`;
      break;
    }
  }

  return (
    <div
      style={{
        fontSize,
        fontWeight,
        color,
        textAlign: align,
        fontFamily: "'Inter', sans-serif",
        lineHeight: 1.3,
        opacity,
        transform,
      }}
    >
      {text}
    </div>
  );
};

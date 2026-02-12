import React from "react";
import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { AnimatedText } from "../components/AnimatedText";
import { BackgroundMedia } from "../components/BackgroundMedia";
import { ProgressBar } from "../components/ProgressBar";

export interface RestaurantShowcaseProps {
  brandName: string;
  tagline: string;
  dishes: Array<{
    name: string;
    image: string;
    description?: string;
  }>;
  primaryColor?: string;
  accentColor?: string;
  logoUrl?: string;
}

export const RestaurantShowcase: React.FC<RestaurantShowcaseProps> = ({
  brandName,
  tagline,
  dishes,
  primaryColor = "#FF6B35",
  accentColor = "#FFFFFF",
  logoUrl,
}) => {
  const { fps, durationInFrames } = useVideoConfig();
  const frame = useCurrentFrame();

  const perDish = Math.floor((durationInFrames - fps * 3) / Math.max(dishes.length, 1));

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Intro sequence */}
      <Sequence from={0} durationInFrames={fps * 2}>
        <AbsoluteFill
          style={{
            background: `linear-gradient(135deg, ${primaryColor}, #1a1a2e)`,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: 60,
          }}
        >
          {logoUrl && (
            <img
              src={logoUrl}
              style={{
                width: 120,
                height: 120,
                borderRadius: 24,
                marginBottom: 30,
                objectFit: "cover",
              }}
            />
          )}
          <AnimatedText
            text={brandName}
            fontSize={56}
            fontWeight={800}
            color={accentColor}
            style="scale"
          />
          <div style={{ height: 16 }} />
          <AnimatedText
            text={tagline}
            fontSize={28}
            fontWeight={400}
            color="rgba(255,255,255,0.8)"
            style="fade"
            delay={15}
          />
        </AbsoluteFill>
      </Sequence>

      {/* Dish sequences */}
      {dishes.map((dish, index) => (
        <Sequence
          key={index}
          from={fps * 2 + index * perDish}
          durationInFrames={perDish}
        >
          <BackgroundMedia
            src={dish.image}
            type="image"
            zoomDirection={index % 2 === 0 ? "in" : "out"}
            overlayOpacity={0.35}
          />
          <AbsoluteFill
            style={{
              display: "flex",
              flexDirection: "column",
              justifyContent: "flex-end",
              padding: 50,
              paddingBottom: 100,
            }}
          >
            <div
              style={{
                backgroundColor: "rgba(0,0,0,0.6)",
                backdropFilter: "blur(12px)",
                borderRadius: 20,
                padding: "24px 32px",
                borderLeft: `4px solid ${primaryColor}`,
              }}
            >
              <AnimatedText
                text={dish.name}
                fontSize={36}
                fontWeight={700}
                color={accentColor}
                style="slide"
                align="left"
              />
              {dish.description && (
                <AnimatedText
                  text={dish.description}
                  fontSize={20}
                  fontWeight={400}
                  color="rgba(255,255,255,0.75)"
                  style="fade"
                  delay={10}
                  align="left"
                />
              )}
            </div>
          </AbsoluteFill>
        </Sequence>
      ))}

      {/* Outro */}
      <Sequence from={durationInFrames - fps} durationInFrames={fps}>
        <AbsoluteFill
          style={{
            background: `linear-gradient(135deg, ${primaryColor}, #1a1a2e)`,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <AnimatedText
            text={brandName}
            fontSize={48}
            fontWeight={800}
            color={accentColor}
            style="scale"
          />
          <div style={{ height: 12 }} />
          <AnimatedText
            text="Suivez-nous!"
            fontSize={24}
            fontWeight={400}
            color="rgba(255,255,255,0.8)"
            style="fade"
            delay={8}
          />
        </AbsoluteFill>
      </Sequence>

      <ProgressBar color={primaryColor} />
    </AbsoluteFill>
  );
};

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

export interface PromoFlashProps {
  headline: string;
  subheadline: string;
  promoCode?: string;
  discount?: string;
  ctaText: string;
  backgroundImage: string;
  primaryColor?: string;
  brandName?: string;
  validUntil?: string;
}

export const PromoFlash: React.FC<PromoFlashProps> = ({
  headline,
  subheadline,
  promoCode,
  discount,
  ctaText,
  backgroundImage,
  primaryColor = "#E63946",
  brandName,
  validUntil,
}) => {
  const { fps, durationInFrames } = useVideoConfig();
  const frame = useCurrentFrame();

  const flashOpacity =
    frame < fps * 0.3
      ? interpolate(frame, [0, fps * 0.3], [1, 0], {
          extrapolateRight: "clamp",
        })
      : 0;

  const pulseScale =
    1 +
    Math.sin(frame * 0.15) * 0.03 *
      interpolate(frame, [fps * 2, durationInFrames], [1, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Background */}
      <BackgroundMedia
        src={backgroundImage}
        type="image"
        zoomDirection="in"
        overlayOpacity={0.55}
      />

      {/* Flash overlay intro */}
      <AbsoluteFill
        style={{
          backgroundColor: primaryColor,
          opacity: flashOpacity,
        }}
      />

      {/* Content */}
      <AbsoluteFill
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: 50,
        }}
      >
        {/* Discount badge */}
        {discount && (
          <Sequence from={Math.floor(fps * 0.5)} durationInFrames={durationInFrames}>
            <div
              style={{
                transform: `scale(${pulseScale})`,
                backgroundColor: primaryColor,
                borderRadius: "50%",
                width: 160,
                height: 160,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                marginBottom: 30,
                boxShadow: `0 0 40px ${primaryColor}66`,
              }}
            >
              <AnimatedText
                text={discount}
                fontSize={48}
                fontWeight={900}
                color="#FFFFFF"
                style="scale"
              />
            </div>
          </Sequence>
        )}

        {/* Headline */}
        <Sequence from={fps} durationInFrames={durationInFrames}>
          <AnimatedText
            text={headline}
            fontSize={52}
            fontWeight={800}
            color="#FFFFFF"
            style="slide"
          />
        </Sequence>

        <div style={{ height: 16 }} />

        {/* Subheadline */}
        <Sequence from={Math.floor(fps * 1.3)} durationInFrames={durationInFrames}>
          <AnimatedText
            text={subheadline}
            fontSize={24}
            fontWeight={400}
            color="rgba(255,255,255,0.85)"
            style="fade"
          />
        </Sequence>

        <div style={{ height: 40 }} />

        {/* Promo code */}
        {promoCode && (
          <Sequence from={fps * 2} durationInFrames={durationInFrames}>
            <div
              style={{
                border: "2px dashed rgba(255,255,255,0.6)",
                borderRadius: 12,
                padding: "12px 32px",
                backgroundColor: "rgba(0,0,0,0.4)",
              }}
            >
              <AnimatedText
                text={`CODE: ${promoCode}`}
                fontSize={28}
                fontWeight={700}
                color="#FFFFFF"
                style="typewriter"
              />
            </div>
          </Sequence>
        )}

        <div style={{ height: 30 }} />

        {/* CTA */}
        <Sequence from={Math.floor(fps * 2.5)} durationInFrames={durationInFrames}>
          <div
            style={{
              backgroundColor: primaryColor,
              borderRadius: 50,
              padding: "16px 48px",
              transform: `scale(${pulseScale})`,
            }}
          >
            <AnimatedText
              text={ctaText}
              fontSize={24}
              fontWeight={700}
              color="#FFFFFF"
              style="scale"
            />
          </div>
        </Sequence>

        {/* Valid until */}
        {validUntil && (
          <Sequence from={fps * 3} durationInFrames={durationInFrames}>
            <div style={{ marginTop: 16 }}>
              <AnimatedText
                text={`Valable jusqu'au ${validUntil}`}
                fontSize={16}
                fontWeight={400}
                color="rgba(255,255,255,0.6)"
                style="fade"
              />
            </div>
          </Sequence>
        )}
      </AbsoluteFill>

      {/* Brand watermark */}
      {brandName && (
        <div
          style={{
            position: "absolute",
            top: 40,
            left: 0,
            right: 0,
            textAlign: "center",
            opacity: 0.7,
          }}
        >
          <AnimatedText
            text={brandName}
            fontSize={18}
            fontWeight={600}
            color="#FFFFFF"
            style="fade"
            delay={5}
          />
        </div>
      )}

      <ProgressBar color={primaryColor} position="top" />
    </AbsoluteFill>
  );
};

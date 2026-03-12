import React, { useState, useCallback } from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
  Img,
  AbsoluteFill,
  delayRender,
  continueRender,
  cancelRender,
} from "remotion";

export interface BreakoutV4Props {
  originalPhotoUrl: string;
  cutoutUrl: string;
  businessName: string;
  instagramHandle: string;
  caption: string;
  accentColor: string;
}

const CANVAS_W = 720;
const CANVAS_H = 1280;
const VIDEO_ZONE_H = Math.floor(CANVAS_H * 0.58);
const UI_ZONE_H = CANVAS_H - VIDEO_ZONE_H;
const OVERLAP_PX = 80;

// ── Remote image loader ─────────────────────────────────────────────
const RemoteImg: React.FC<{
  src: string;
  style: React.CSSProperties;
  label: string;
}> = ({ src, style, label }) => {
  const [handle] = useState(() =>
    delayRender(`Loading ${label}`, { timeoutInMilliseconds: 30_000 })
  );

  const onLoad = useCallback(() => {
    continueRender(handle);
  }, [handle]);

  const onError = useCallback(() => {
    cancelRender(new Error(`Failed to load image: ${label} (${src})`));
  }, [handle, src, label]);

  return <Img src={src} style={style} onLoad={onLoad} onError={onError} />;
};

// ── Main V4 composition ─────────────────────────────────────────────
export const BreakoutV4: React.FC<BreakoutV4Props> = ({
  originalPhotoUrl,
  cutoutUrl,
  businessName,
  instagramHandle,
  caption = "",
  accentColor = "#F59E0B",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── Animations ──

  // Background zoom-in
  const bgScale = interpolate(frame, [0, 90], [1.0, 1.08], {
    extrapolateRight: "clamp",
  });

  // Subject pop-up with spring
  const subjectSpring = spring({
    frame: frame - 12,
    fps,
    config: { damping: 14, stiffness: 100, mass: 0.7 },
  });
  const subjectTranslateY = interpolate(subjectSpring, [0, 1], [-80, OVERLAP_PX]);
  const subjectScale = interpolate(subjectSpring, [0, 1], [0.9, 1.18]);

  // Shadow follows subject
  const shadowOpacity = interpolate(subjectSpring, [0, 1], [0, 0.4]);

  // UI fade-in
  const uiFade = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Caption slide-in
  const captionSlide = spring({
    frame: frame - 25,
    fps,
    config: { damping: 20, stiffness: 80, mass: 0.6 },
  });
  const captionTranslateX = interpolate(captionSlide, [0, 1], [-40, 0]);
  const captionOpacity = interpolate(captionSlide, [0, 1], [0, 1]);

  // Handle text slide-in
  const handleSlide = spring({
    frame: frame - 18,
    fps,
    config: { damping: 18, stiffness: 90, mass: 0.5 },
  });
  const handleTranslateY = interpolate(handleSlide, [0, 1], [20, 0]);
  const handleOpacity = interpolate(handleSlide, [0, 1], [0, 1]);

  // Like counter pop
  const likeSpring = spring({
    frame: frame - 30,
    fps,
    config: { damping: 12, stiffness: 150, mass: 0.4 },
  });
  const likeScale = interpolate(likeSpring, [0, 1], [0, 1]);

  const cutoutH = Math.floor(VIDEO_ZONE_H * 0.88);
  const cutoutW = cutoutH;

  return (
    <AbsoluteFill style={{ backgroundColor: "#FFFFFF" }}>
      {/* Layer 1: Background photo with blur + zoom */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: CANVAS_W,
          height: VIDEO_ZONE_H,
          overflow: "hidden",
        }}
      >
        <RemoteImg
          src={originalPhotoUrl}
          label="original photo"
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            filter: "blur(4px) brightness(0.82) saturate(1.1)",
            transform: `scale(${bgScale})`,
          }}
        />
        {/* Gradient overlay bottom of photo zone */}
        <div
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            width: "100%",
            height: 70,
            background:
              "linear-gradient(transparent, rgba(255,255,255,0.6))",
          }}
        />
      </div>

      {/* Frame separator line */}
      <div
        style={{
          position: "absolute",
          top: VIDEO_ZONE_H - 3,
          left: 0,
          width: CANVAS_W,
          height: 3,
          backgroundColor: "#E5E7EB",
          zIndex: 10,
        }}
      />

      {/* Layer 2: Instagram-like UI zone */}
      <div
        style={{
          position: "absolute",
          top: VIDEO_ZONE_H,
          left: 0,
          width: CANVAS_W,
          height: UI_ZONE_H,
          backgroundColor: "#FFFFFF",
          padding: "18px 24px",
          opacity: uiFade,
        }}
      >
        {/* Account header */}
        <div style={{ display: "flex", alignItems: "center", marginBottom: 14 }}>
          <div
            style={{
              width: 52,
              height: 52,
              borderRadius: "50%",
              background: `linear-gradient(135deg, ${accentColor}, #EC4899)`,
              border: "2px solid #E5E7EB",
              flexShrink: 0,
            }}
          />
          <div
            style={{
              marginLeft: 12,
              opacity: handleOpacity,
              transform: `translateY(${handleTranslateY}px)`,
            }}
          >
            <div
              style={{
                fontSize: 20,
                fontWeight: 700,
                color: "#111827",
                fontFamily: "sans-serif",
              }}
            >
              {instagramHandle}
            </div>
            <div
              style={{
                fontSize: 16,
                color: "#6B7280",
                fontFamily: "sans-serif",
                marginTop: 3,
              }}
            >
              {businessName}
            </div>
          </div>
        </div>

        <div
          style={{
            width: "100%",
            height: 1,
            backgroundColor: "#F3F4F6",
            marginBottom: 14,
          }}
        />

        {/* Action bar (Like / Comment / Share) */}
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              transform: `scale(${likeScale})`,
            }}
          >
            <svg width="32" height="32" viewBox="0 0 24 24" fill={accentColor}>
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
            </svg>
          </div>

          <svg
            width="28"
            height="28"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#9CA3AF"
            strokeWidth="2"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>

          <svg
            width="28"
            height="28"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#9CA3AF"
            strokeWidth="2"
          >
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>

          <div style={{ marginLeft: "auto" }}>
            <svg
              width="26"
              height="26"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#9CA3AF"
              strokeWidth="2"
            >
              <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
            </svg>
          </div>
        </div>

        {/* Caption */}
        {caption ? (
          <div
            style={{
              marginTop: 14,
              fontSize: 16,
              color: "#374151",
              fontFamily: "sans-serif",
              lineHeight: 1.5,
              opacity: captionOpacity,
              transform: `translateX(${captionTranslateX}px)`,
            }}
          >
            <span style={{ fontWeight: 700 }}>{instagramHandle} </span>
            {caption}
          </div>
        ) : (
          <div
            style={{
              marginTop: 14,
              fontSize: 16,
              color: "#374151",
              fontFamily: "sans-serif",
              lineHeight: 1.5,
              opacity: captionOpacity,
              transform: `translateX(${captionTranslateX}px)`,
            }}
          >
            <span style={{ fontWeight: 700 }}>{instagramHandle} </span>
            Decouvrez notre specialite du jour !
          </div>
        )}
      </div>

      {/* Subject shadow */}
      <div
        style={{
          position: "absolute",
          bottom: UI_ZONE_H - subjectTranslateY - 30,
          left: "50%",
          transform: "translateX(-50%)",
          width: cutoutW * subjectScale * 0.65,
          height: 50,
          background:
            "radial-gradient(ellipse, rgba(0,0,0,0.45) 0%, transparent 70%)",
          opacity: shadowOpacity,
          filter: "blur(16px)",
          zIndex: 19,
        }}
      />

      {/* Layer 3: Cutout subject — overlaps frame boundary */}
      <div
        style={{
          position: "absolute",
          bottom: UI_ZONE_H - subjectTranslateY,
          left: "50%",
          transform: `translateX(-50%) scale(${subjectScale})`,
          transformOrigin: "bottom center",
          width: cutoutW,
          height: cutoutH,
          zIndex: 20,
        }}
      >
        <RemoteImg
          src={cutoutUrl}
          label="cutout subject"
          style={{
            width: "100%",
            height: "100%",
            objectFit: "contain",
            objectPosition: "bottom center",
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

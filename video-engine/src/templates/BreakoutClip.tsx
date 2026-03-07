import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
  Img,
  AbsoluteFill,
} from "remotion";

export interface BreakoutClipProps {
  originalPhotoUrl: string;
  cutoutUrl: string;
  businessName: string;
  likesCount: number;
  instagramHandle: string;
  accentColor: string;
}

const CANVAS_W = 1080;
const CANVAS_H = 1920;
const VIDEO_ZONE_H = Math.floor(CANVAS_H * 0.6);
const UI_ZONE_H = CANVAS_H - VIDEO_ZONE_H;
const SUBJECT_SCALE = 1.15;
const OVERLAP_PX = 120;

export const BreakoutClip: React.FC<BreakoutClipProps> = ({
  originalPhotoUrl,
  cutoutUrl,
  businessName,
  likesCount,
  instagramHandle,
  accentColor = "#F59E0B",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const subjectProgress = spring({
    frame: frame - 15,
    fps,
    config: { damping: 18, stiffness: 120, mass: 0.8 },
  });

  const subjectTranslateY = interpolate(subjectProgress, [0, 1], [-50, OVERLAP_PX]);
  const subjectScale = interpolate(subjectProgress, [0, 1], [1, SUBJECT_SCALE]);
  const shadowOpacity = interpolate(subjectProgress, [0, 1], [0, 0.35]);

  const cutoutH = Math.floor(VIDEO_ZONE_H * 0.85);
  const cutoutW = cutoutH;

  return (
    <AbsoluteFill style={{ backgroundColor: "#FFFFFF" }}>
      {/* Zone 1 : Photo originale avec bokeh (60%) */}
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
        <Img
          src={originalPhotoUrl}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            filter: "blur(3px) brightness(0.85)",
            transform: "scale(1.05)",
          }}
        />
      </div>

      {/* Separateur cadre Instagram */}
      <div
        style={{
          position: "absolute",
          top: VIDEO_ZONE_H - 4,
          left: 0,
          width: CANVAS_W,
          height: 4,
          backgroundColor: "#E5E7EB",
          zIndex: 10,
        }}
      />

      {/* Zone 2 : Interface Instagram blanche (40%) */}
      <div
        style={{
          position: "absolute",
          top: VIDEO_ZONE_H,
          left: 0,
          width: CANVAS_W,
          height: UI_ZONE_H,
          backgroundColor: "#FFFFFF",
          display: "flex",
          flexDirection: "column",
          padding: "32px 40px",
        }}
      >
        {/* Header compte */}
        <div style={{ display: "flex", alignItems: "center", marginBottom: 24 }}>
          <div
            style={{
              width: 88,
              height: 88,
              borderRadius: "50%",
              background: `linear-gradient(135deg, ${accentColor}, #EC4899)`,
              border: "3px solid #E5E7EB",
              flexShrink: 0,
            }}
          />
          <div style={{ marginLeft: 20 }}>
            <div
              style={{
                fontSize: 36,
                fontWeight: 700,
                color: "#111827",
                fontFamily: "sans-serif",
              }}
            >
              {instagramHandle}
            </div>
            <div
              style={{
                fontSize: 26,
                color: "#6B7280",
                fontFamily: "sans-serif",
                marginTop: 4,
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
            marginBottom: 28,
          }}
        />

        {/* Actions (Like / Comment / Share) */}
        <div style={{ display: "flex", alignItems: "center", gap: 32 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <svg width="52" height="52" viewBox="0 0 24 24" fill={accentColor}>
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
            </svg>
            <span
              style={{
                fontSize: 30,
                fontWeight: 600,
                color: "#374151",
                fontFamily: "sans-serif",
              }}
            >
              {likesCount.toLocaleString()}
            </span>
          </div>

          <svg
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#9CA3AF"
            strokeWidth="2"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>

          <svg
            width="48"
            height="48"
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
              width="44"
              height="44"
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
        <div
          style={{
            marginTop: 24,
            fontSize: 26,
            color: "#374151",
            fontFamily: "sans-serif",
            lineHeight: 1.5,
          }}
        >
          <span style={{ fontWeight: 700 }}>{instagramHandle} </span>
          Decouvrez notre specialite du jour !
        </div>

        {/* Hashtags */}
        <div
          style={{
            marginTop: 12,
            fontSize: 24,
            color: accentColor,
            fontFamily: "sans-serif",
          }}
        >
          #restaurant #food #foodie #gastronomie
        </div>
      </div>

      {/* Ombre portee du sujet */}
      <div
        style={{
          position: "absolute",
          bottom: UI_ZONE_H - subjectTranslateY - 20,
          left: "50%",
          transform: "translateX(-50%)",
          width: cutoutW * subjectScale * 0.7,
          height: 40,
          background:
            "radial-gradient(ellipse, rgba(0,0,0,0.4) 0%, transparent 70%)",
          opacity: shadowOpacity,
          filter: "blur(12px)",
          zIndex: 19,
        }}
      />

      {/* Sujet detoure — overlapping */}
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
        <Img
          src={cutoutUrl}
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

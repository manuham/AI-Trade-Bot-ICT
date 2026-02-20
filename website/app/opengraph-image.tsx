import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "AI Trade Bot ICT — AI-Powered Forex Signals";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          background: "linear-gradient(135deg, #080b12 0%, #0d1117 50%, #111827 100%)",
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "Inter, system-ui, sans-serif",
          position: "relative",
        }}
      >
        {/* Glow effect */}
        <div
          style={{
            position: "absolute",
            top: -100,
            width: 600,
            height: 600,
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(99,102,241,0.2) 0%, transparent 70%)",
          }}
        />

        {/* Logo badge */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 16,
            marginBottom: 32,
          }}
        >
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: 14,
              background: "#6366f1",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "white",
              fontSize: 22,
              fontWeight: 700,
            }}
          >
            ICT
          </div>
          <span style={{ color: "#f1f5f9", fontSize: 28, fontWeight: 600 }}>
            AI Trade Bot
          </span>
        </div>

        {/* Headline */}
        <div
          style={{
            fontSize: 52,
            fontWeight: 700,
            color: "#f1f5f9",
            textAlign: "center",
            lineHeight: 1.2,
            marginBottom: 16,
          }}
        >
          AI-Powered Forex Signals
        </div>

        {/* Subtitle */}
        <div
          style={{
            fontSize: 24,
            color: "#818cf8",
            textAlign: "center",
            fontWeight: 600,
          }}
        >
          With Full Transparency
        </div>

        {/* Bottom tags */}
        <div
          style={{
            display: "flex",
            gap: 24,
            marginTop: 48,
            fontSize: 16,
            color: "#64748b",
            textTransform: "uppercase",
            letterSpacing: 2,
            fontWeight: 600,
          }}
        >
          <span>ICT Methodology</span>
          <span style={{ color: "#1e2d3d" }}>|</span>
          <span>Claude AI</span>
          <span style={{ color: "#1e2d3d" }}>|</span>
          <span>Multi-Pair</span>
        </div>
      </div>
    ),
    { ...size }
  );
}

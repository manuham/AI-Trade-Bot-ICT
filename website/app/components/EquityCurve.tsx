"use client";

import { useEffect, useRef, useState } from "react";
import useSWR from "swr";
import { API_URL, swrFetcher, PublicTrade } from "@/lib/api";
import AnimatedSection from "./AnimatedSection";

interface DataPoint {
  label: string;
  cumPnl: number;
}

export default function EquityCurve() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; label: string; value: string } | null>(null);

  const { data } = useSWR<{ trades: PublicTrade[] }>(
    `${API_URL}/public/trades?limit=100`,
    swrFetcher,
    { refreshInterval: 60000 }
  );

  const trades = data?.trades || [];

  // Build equity curve data
  const chartData: DataPoint[] = [];
  if (trades.length > 0) {
    const closedTrades = trades
      .filter((t) => t.status === "closed" && t.pnl_pips !== undefined)
      .reverse(); // oldest first

    let cumPnl = 0;
    chartData.push({ label: "Start", cumPnl: 0 });
    closedTrades.forEach((t) => {
      cumPnl += t.pnl_pips;
      const date = new Date(t.closed_at || t.created_at);
      chartData.push({
        label: date.toLocaleDateString("en-GB", { day: "2-digit", month: "short" }),
        cumPnl: Math.round(cumPnl * 10) / 10,
      });
    });
  }

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container || chartData.length < 2) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // HiDPI
    const dpr = window.devicePixelRatio || 1;
    const rect = container.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    canvas.style.width = `${rect.width}px`;
    canvas.style.height = `${rect.height}px`;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    const pad = { top: 20, right: 20, bottom: 40, left: 60 };
    const plotW = w - pad.left - pad.right;
    const plotH = h - pad.top - pad.bottom;

    const values = chartData.map((d) => d.cumPnl);
    const minVal = Math.min(0, ...values);
    const maxVal = Math.max(0, ...values);
    const range = maxVal - minVal || 1;

    const xStep = plotW / (chartData.length - 1);
    const getX = (i: number) => pad.left + i * xStep;
    const getY = (v: number) => pad.top + plotH - ((v - minVal) / range) * plotH;

    // Clear
    ctx.clearRect(0, 0, w, h);

    // Grid lines
    ctx.strokeStyle = "rgba(30, 45, 61, 0.5)";
    ctx.lineWidth = 1;
    const gridLines = 5;
    for (let i = 0; i <= gridLines; i++) {
      const y = pad.top + (plotH / gridLines) * i;
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(w - pad.right, y);
      ctx.stroke();

      // Y-axis labels
      const val = maxVal - (range / gridLines) * i;
      ctx.fillStyle = "#64748b";
      ctx.font = "11px Inter, sans-serif";
      ctx.textAlign = "right";
      ctx.fillText(`${val >= 0 ? "+" : ""}${val.toFixed(0)}`, pad.left - 10, y + 4);
    }

    // X-axis labels (show every few labels to avoid overlap)
    const labelEvery = Math.max(1, Math.floor(chartData.length / 8));
    ctx.textAlign = "center";
    chartData.forEach((d, i) => {
      if (i % labelEvery === 0 || i === chartData.length - 1) {
        ctx.fillStyle = "#64748b";
        ctx.font = "10px Inter, sans-serif";
        ctx.fillText(d.label, getX(i), h - pad.bottom + 20);
      }
    });

    // Zero line
    if (minVal < 0) {
      const zeroY = getY(0);
      ctx.strokeStyle = "rgba(100, 116, 139, 0.3)";
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(pad.left, zeroY);
      ctx.lineTo(w - pad.right, zeroY);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Gradient fill
    const lastVal = chartData[chartData.length - 1].cumPnl;
    const isPositive = lastVal >= 0;
    const gradColor = isPositive ? "52, 211, 153" : "248, 113, 113";

    const gradient = ctx.createLinearGradient(0, pad.top, 0, h - pad.bottom);
    gradient.addColorStop(0, `rgba(${gradColor}, 0.15)`);
    gradient.addColorStop(1, `rgba(${gradColor}, 0.01)`);

    ctx.beginPath();
    ctx.moveTo(getX(0), getY(chartData[0].cumPnl));
    chartData.forEach((d, i) => {
      if (i > 0) ctx.lineTo(getX(i), getY(d.cumPnl));
    });
    ctx.lineTo(getX(chartData.length - 1), h - pad.bottom);
    ctx.lineTo(getX(0), h - pad.bottom);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // Line
    ctx.beginPath();
    ctx.moveTo(getX(0), getY(chartData[0].cumPnl));
    chartData.forEach((d, i) => {
      if (i > 0) ctx.lineTo(getX(i), getY(d.cumPnl));
    });
    ctx.strokeStyle = isPositive ? "#34d399" : "#f87171";
    ctx.lineWidth = 2.5;
    ctx.lineJoin = "round";
    ctx.stroke();

    // End dot
    const lastX = getX(chartData.length - 1);
    const lastY = getY(lastVal);
    ctx.beginPath();
    ctx.arc(lastX, lastY, 5, 0, Math.PI * 2);
    ctx.fillStyle = isPositive ? "#34d399" : "#f87171";
    ctx.fill();
    ctx.beginPath();
    ctx.arc(lastX, lastY, 8, 0, Math.PI * 2);
    ctx.strokeStyle = isPositive ? "rgba(52,211,153,0.3)" : "rgba(248,113,113,0.3)";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Mouse move handler for tooltip
    const handleMouse = (e: MouseEvent) => {
      const canvasRect = canvas.getBoundingClientRect();
      const mx = e.clientX - canvasRect.left;
      const closestIdx = Math.round((mx - pad.left) / xStep);
      if (closestIdx >= 0 && closestIdx < chartData.length) {
        const d = chartData[closestIdx];
        setTooltip({
          x: getX(closestIdx),
          y: getY(d.cumPnl),
          label: d.label,
          value: `${d.cumPnl >= 0 ? "+" : ""}${d.cumPnl.toFixed(1)} pips`,
        });
      }
    };
    const handleLeave = () => setTooltip(null);

    canvas.addEventListener("mousemove", handleMouse);
    canvas.addEventListener("mouseleave", handleLeave);
    return () => {
      canvas.removeEventListener("mousemove", handleMouse);
      canvas.removeEventListener("mouseleave", handleLeave);
    };
  }, [chartData]);

  if (chartData.length < 2) {
    return null; // Don't show chart with insufficient data
  }

  const lastVal = chartData[chartData.length - 1]?.cumPnl ?? 0;
  const isPositive = lastVal >= 0;

  return (
    <section className="py-20 px-4">
      <AnimatedSection className="max-w-5xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-10">
          <p className="text-accent text-xs font-semibold uppercase tracking-widest mb-3">
            Performance
          </p>
          <h2 className="text-2xl sm:text-3xl font-bold mb-3">
            Cumulative P&amp;L Equity Curve
          </h2>
          <p className="text-text-secondary text-sm sm:text-base">
            Every pip tracked from the first trade — no resets, no hiding.
          </p>
        </div>

        {/* Chart container */}
        <div className="bg-bg-card border border-border rounded-xl p-4 sm:p-6">
          {/* Chart header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <span className={`text-2xl font-bold ${isPositive ? "text-green" : "text-red"}`}>
                {lastVal >= 0 ? "+" : ""}{lastVal.toFixed(1)} pips
              </span>
              <span className="text-text-muted text-sm">total</span>
            </div>
            <div className="flex items-center gap-2 text-text-muted text-xs">
              <span className="w-2 h-2 rounded-full bg-green pulse-dot" />
              Live data
            </div>
          </div>

          {/* Canvas chart */}
          <div ref={containerRef} className="relative w-full h-[280px] sm:h-[340px]">
            <canvas ref={canvasRef} className="w-full h-full cursor-crosshair" />
            {/* Tooltip */}
            {tooltip && (
              <div
                className="absolute pointer-events-none bg-bg-primary border border-border rounded-lg px-3 py-2 text-xs shadow-lg"
                style={{
                  left: tooltip.x,
                  top: tooltip.y - 50,
                  transform: "translateX(-50%)",
                }}
              >
                <div className="text-text-muted">{tooltip.label}</div>
                <div className={`font-bold ${isPositive ? "text-green" : "text-red"}`}>
                  {tooltip.value}
                </div>
              </div>
            )}
          </div>
        </div>
      </AnimatedSection>
    </section>
  );
}

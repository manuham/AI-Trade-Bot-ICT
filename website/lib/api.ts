// API configuration and fetch helpers
//
// Server-side (LiveStats etc): fetches directly from VPS — no mixed content issue
// Client-side (TradeTable, EquityCurve): uses /api/vps/ proxy defined in next.config.ts
//   Browser → https://icttradebot.com/api/vps/public/trades → Vercel → http://VPS:8000/public/trades

// Server-side: full URL (never exposed to browser)
const SERVER_API_URL =
  process.env.BACKEND_URL || "http://46.225.66.110:8000";

// Client-side: relative path through Next.js rewrite proxy (stays HTTPS)
const CLIENT_API_URL = "/api/vps";

export interface PublicStats {
  period_days: number;
  total_trades: number;
  win_rate: number;
  total_pnl_pips: number;
  avg_win_pips: number;
  avg_loss_pips: number;
  wins: number;
  losses: number;
}

export interface PublicTrade {
  id: string;
  symbol: string;
  bias: string;
  confidence: string;
  checklist_score: string;
  actual_entry: number;
  stop_loss: number;
  tp1: number;
  tp2: number;
  sl_pips: number;
  rr_tp2: number;
  status: string;
  outcome: string;
  pnl_pips: number;
  created_at: string;
  closed_at: string;
}

// Server component fetch — direct to VPS (server-to-server, no HTTPS issue)
export async function fetchStats(): Promise<PublicStats> {
  const res = await fetch(`${SERVER_API_URL}/public/stats`, {
    next: { revalidate: 60 },
  });
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

// Server component fetch — direct to VPS
export async function fetchTrades(limit = 50): Promise<PublicTrade[]> {
  const res = await fetch(`${SERVER_API_URL}/public/trades?limit=${limit}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to fetch trades");
  const data = await res.json();
  return data.trades;
}

// Client-side fetcher for SWR
export const swrFetcher = (url: string) =>
  fetch(url).then((r) => r.json());

export { CLIENT_API_URL, SERVER_API_URL };

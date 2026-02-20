"use client";

import useSWR from "swr";
import { CLIENT_API_URL, swrFetcher, PublicTrade } from "@/lib/api";

function formatTimeAgo(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffHours / 24);

  if (diffDays > 7) {
    return date.toLocaleDateString("en-GB", { day: "2-digit", month: "short" });
  }
  if (diffDays > 0) return `${diffDays}d ago`;
  if (diffHours > 0) return `${diffHours}h ago`;
  return "Just now";
}

export default function TradeTable() {
  const { data, error, isLoading } = useSWR<{ trades: PublicTrade[] }>(
    `${CLIENT_API_URL}/public/trades?limit=20`,
    swrFetcher,
    { refreshInterval: 30000 }
  );

  const trades = data?.trades || [];

  return (
    <section id="track-record" className="py-20 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-12">
          <p className="text-accent text-xs font-semibold uppercase tracking-widest mb-3">
            Track Record
          </p>
          <h2 className="text-2xl sm:text-3xl font-bold mb-3">
            Recent Trades — Live &amp; Unfiltered
          </h2>
          <p className="text-text-secondary text-sm sm:text-base">
            Every trade is recorded — no deletions, no cherry-picking. Updates every 30 seconds.
          </p>
        </div>

        {/* Table container */}
        <div className="border border-border rounded-xl bg-bg-card overflow-hidden">
          {isLoading ? (
            <div className="p-12 text-center">
              <div className="inline-flex items-center gap-3 text-text-secondary">
                <div className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin" />
                Loading trades...
              </div>
            </div>
          ) : error ? (
            <div className="p-12 text-center text-text-secondary">
              Unable to load trades — server may be offline.
            </div>
          ) : trades.length === 0 ? (
            <div className="p-12 text-center text-text-secondary">
              No trades yet — the bot is waiting for the next session.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left">
                    {["Date", "Pair", "Bias", "Score", "Entry", "SL", "TP2", "R:R", "Outcome", "P&L"].map((h) => (
                      <th
                        key={h}
                        className="px-4 py-3 text-text-muted font-semibold text-xs uppercase tracking-wider whitespace-nowrap"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {trades.map((t) => {
                    const isWin = t.pnl_pips > 0;
                    const isBE = t.pnl_pips === 0;
                    const isOpen = t.status === "open";

                    return (
                      <tr
                        key={t.id}
                        className="border-b border-border/50 table-row-hover"
                      >
                        <td className="px-4 py-3 whitespace-nowrap text-text-secondary">
                          {formatTimeAgo(t.created_at)}
                        </td>
                        <td className="px-4 py-3 font-semibold text-text-primary">
                          {t.symbol}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`font-semibold ${t.bias === "LONG" ? "text-green" : "text-red"}`}>
                            {t.bias}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-text-secondary">
                          {t.checklist_score}
                        </td>
                        <td className="px-4 py-3 text-text-secondary font-mono text-xs">
                          {t.actual_entry?.toFixed(3) || "—"}
                        </td>
                        <td className="px-4 py-3 text-text-secondary font-mono text-xs">
                          {t.stop_loss?.toFixed(3) || "—"}
                        </td>
                        <td className="px-4 py-3 text-text-secondary font-mono text-xs">
                          {t.tp2?.toFixed(3) || "—"}
                        </td>
                        <td className="px-4 py-3 text-text-secondary">
                          {t.rr_tp2 ? `1:${t.rr_tp2.toFixed(1)}` : "—"}
                        </td>
                        <td className="px-4 py-3">
                          {isOpen ? (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-accent-glow text-accent-light">
                              <span className="w-1.5 h-1.5 rounded-full bg-accent-light pulse-dot" />
                              OPEN
                            </span>
                          ) : (
                            <span
                              className={`inline-block px-2.5 py-1 rounded-md text-xs font-semibold ${
                                isWin
                                  ? "bg-green-bg text-green"
                                  : isBE
                                    ? "bg-yellow-bg text-yellow"
                                    : "bg-red-bg text-red"
                              }`}
                            >
                              {t.outcome || "—"}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          {isOpen ? (
                            <span className="text-text-muted">—</span>
                          ) : (
                            <span
                              className={`font-bold ${
                                isWin ? "text-green" : isBE ? "text-yellow" : "text-red"
                              }`}
                            >
                              {t.pnl_pips >= 0 ? "+" : ""}{t.pnl_pips.toFixed(1)}
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

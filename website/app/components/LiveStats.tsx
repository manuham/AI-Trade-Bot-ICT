import { fetchStats } from "@/lib/api";

export default async function LiveStats() {
  let stats;
  try {
    stats = await fetchStats();
  } catch {
    return (
      <section id="stats" className="py-16 px-4 text-center">
        <p className="text-text-secondary">
          Stats temporarily unavailable — check back soon.
        </p>
      </section>
    );
  }

  const cards = [
    {
      label: "Win Rate",
      value: `${stats.win_rate.toFixed(1)}%`,
      color: stats.win_rate >= 50 ? "text-green" : "text-red",
    },
    {
      label: "Total P&L",
      value: `${stats.total_pnl_pips >= 0 ? "+" : ""}${stats.total_pnl_pips.toFixed(0)} pips`,
      color: stats.total_pnl_pips >= 0 ? "text-green" : "text-red",
    },
    {
      label: "Trades Taken",
      value: stats.total_trades.toString(),
      color: "text-accent-light",
    },
    {
      label: "Avg Win",
      value: `+${stats.avg_win_pips.toFixed(1)} pips`,
      color: "text-green",
    },
  ];

  return (
    <section id="stats" className="py-20 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 text-accent text-xs font-semibold uppercase tracking-widest mb-3">
            <span className="w-2 h-2 rounded-full bg-green pulse-dot" />
            Live Performance
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold mb-3">
            Verified Track Record
          </h2>
          <p className="text-text-secondary text-sm sm:text-base">
            Last {stats.period_days} days — updated every 60 seconds from our live trading server.
          </p>
        </div>

        {/* Stat cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {cards.map((card) => (
            <div
              key={card.label}
              className="bg-bg-card border border-border rounded-xl p-6 text-center card-hover"
            >
              <div className={`text-3xl sm:text-4xl font-bold mb-2 ${card.color}`}>
                {card.value}
              </div>
              <div className="text-text-muted text-xs font-semibold uppercase tracking-wider">
                {card.label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

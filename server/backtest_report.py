# backtest_report.py — Performance report generator for backtests
"""Compiles detailed performance statistics from backtest results.

Provides breakdowns by:
  - Overall summary (win rate, profit factor, pips, drawdown)
  - Checklist score brackets (10-12, 7-9, 4-6, <4)
  - Confidence levels (HIGH, MEDIUM, LOW)
  - Bias (LONG vs SHORT)
  - Day of week
  - Equity curve data
  - Best/worst trades
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Main report generator
# ---------------------------------------------------------------------------
def generate_report(run: dict, trades: list[dict]) -> dict:
    """Generate a comprehensive backtest report.

    Args:
        run: Backtest run record (from backtest_runs table)
        trades: List of trade records (from backtest_trades table)

    Returns:
        Dict with all report sections.
    """
    # Filter to trades that actually entered the market
    entered = [t for t in trades if t["outcome"] not in ("no_data", "no_entry")]

    report = {
        "run_id": run["id"],
        "symbol": run["symbol"],
        "period": f"{run['start_date']} to {run['end_date']}",
        "mode": run.get("mode", "unknown"),
        "generated_at": datetime.utcnow().isoformat(),

        # Top-level stats (from the run record)
        "overview": _build_overview(run, entered),

        # Breakdowns
        "by_checklist_score": _breakdown_by_checklist(entered),
        "by_confidence": _breakdown_by_confidence(entered),
        "by_bias": _breakdown_by_bias(entered),
        "by_day_of_week": _breakdown_by_day(entered),

        # Equity curve
        "equity_curve": _build_equity_curve(entered),

        # Notable trades
        "best_trade": _find_best_trade(entered),
        "worst_trade": _find_worst_trade(entered),

        # Streaks
        "streaks": _compute_streaks(entered),
    }

    return report


def _build_overview(run: dict, trades: list[dict]) -> dict:
    """Build the overview section from run data."""
    return {
        "total_setups": run.get("total_setups", 0),
        "total_trades": run.get("total_trades", 0),
        "no_entry": run.get("no_entry", 0),
        "wins": run.get("wins", 0),
        "partial_wins": run.get("partial_wins", 0),
        "losses": run.get("losses", 0),
        "breakevens": run.get("breakevens", 0),
        "expired": run.get("expired", 0),
        "win_rate": run.get("win_rate", 0),
        "profit_factor": run.get("profit_factor", 0),
        "total_pnl_pips": run.get("total_pnl_pips", 0),
        "max_drawdown_pips": run.get("max_drawdown_pips", 0),
        "avg_rr_achieved": run.get("avg_rr_achieved", 0),
        "avg_duration_minutes": run.get("avg_duration_minutes", 0),
        "avg_pnl_per_trade": round(
            run.get("total_pnl_pips", 0) / max(run.get("total_trades", 1), 1), 1
        ),
    }


# ---------------------------------------------------------------------------
# Breakdown helpers
# ---------------------------------------------------------------------------
def _compute_group_stats(trades: list[dict]) -> dict:
    """Compute stats for a group of trades."""
    if not trades:
        return {
            "count": 0, "wins": 0, "losses": 0, "win_rate": 0,
            "total_pnl": 0, "avg_pnl": 0, "profit_factor": 0,
        }

    count = len(trades)
    wins = sum(1 for t in trades if t["outcome"] in ("full_win", "partial_win"))
    losses = sum(1 for t in trades if t["outcome"] == "loss")
    win_rate = (wins / count * 100) if count > 0 else 0

    total_pnl = sum(t["pnl_pips"] for t in trades)
    gross_profit = sum(t["pnl_pips"] for t in trades if t["pnl_pips"] > 0)
    gross_loss = abs(sum(t["pnl_pips"] for t in trades if t["pnl_pips"] < 0))
    pf = (gross_profit / gross_loss) if gross_loss > 0 else (
        float("inf") if gross_profit > 0 else 0
    )

    return {
        "count": count,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 1),
        "total_pnl": round(total_pnl, 1),
        "avg_pnl": round(total_pnl / count, 1) if count > 0 else 0,
        "profit_factor": round(pf, 2) if pf != float("inf") else "∞",
    }


def _get_checklist_bracket(score_str: str) -> str:
    """Map a checklist score string like '10/12' to a bracket."""
    try:
        num = int(score_str.split("/")[0])
        if num >= 10:
            return "10-12 (HIGH)"
        elif num >= 7:
            return "7-9 (MEDIUM)"
        elif num >= 4:
            return "4-6 (LOW)"
        else:
            return "<4 (REJECT)"
    except (ValueError, IndexError):
        return "Unknown"


def _breakdown_by_checklist(trades: list[dict]) -> dict:
    """Group performance by checklist score bracket."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for t in trades:
        bracket = _get_checklist_bracket(t.get("checklist_score", ""))
        groups[bracket].append(t)

    return {bracket: _compute_group_stats(group) for bracket, group in sorted(groups.items())}


def _breakdown_by_confidence(trades: list[dict]) -> dict:
    """Group performance by confidence level."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for t in trades:
        conf = (t.get("confidence") or "UNKNOWN").upper()
        groups[conf].append(t)

    return {conf: _compute_group_stats(group) for conf, group in sorted(groups.items())}


def _breakdown_by_bias(trades: list[dict]) -> dict:
    """Group performance by trade bias (long/short)."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for t in trades:
        bias = (t.get("bias") or "unknown").upper()
        groups[bias].append(t)

    return {bias: _compute_group_stats(group) for bias, group in sorted(groups.items())}


def _breakdown_by_day(trades: list[dict]) -> dict:
    """Group performance by day of week."""
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    groups: dict[str, list[dict]] = defaultdict(list)

    for t in trades:
        date_str = t.get("trade_date", "")
        try:
            dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
            day_name = day_names[dt.weekday()]
        except (ValueError, IndexError):
            day_name = "Unknown"
        groups[day_name].append(t)

    # Sort by day order
    ordered = {}
    for day in day_names:
        if day in groups:
            ordered[day] = _compute_group_stats(groups[day])
    if "Unknown" in groups:
        ordered["Unknown"] = _compute_group_stats(groups["Unknown"])

    return ordered


# ---------------------------------------------------------------------------
# Equity curve
# ---------------------------------------------------------------------------
def _build_equity_curve(trades: list[dict]) -> list[dict]:
    """Build cumulative P&L equity curve data points."""
    curve = []
    cumulative = 0.0

    for t in trades:
        cumulative += t.get("pnl_pips", 0)
        curve.append({
            "date": t.get("trade_date", ""),
            "time": t.get("entry_time", ""),
            "pnl": round(t["pnl_pips"], 1),
            "cumulative": round(cumulative, 1),
            "outcome": t["outcome"],
        })

    return curve


# ---------------------------------------------------------------------------
# Notable trades
# ---------------------------------------------------------------------------
def _find_best_trade(trades: list[dict]) -> Optional[dict]:
    """Find the most profitable trade."""
    if not trades:
        return None
    best = max(trades, key=lambda t: t.get("pnl_pips", 0))
    return {
        "date": best.get("trade_date"),
        "bias": best.get("bias"),
        "outcome": best.get("outcome"),
        "pnl_pips": best.get("pnl_pips"),
        "entry_price": best.get("entry_price"),
        "duration_minutes": best.get("duration_minutes"),
        "checklist_score": best.get("checklist_score"),
    }


def _find_worst_trade(trades: list[dict]) -> Optional[dict]:
    """Find the most losing trade."""
    if not trades:
        return None
    worst = min(trades, key=lambda t: t.get("pnl_pips", 0))
    return {
        "date": worst.get("trade_date"),
        "bias": worst.get("bias"),
        "outcome": worst.get("outcome"),
        "pnl_pips": worst.get("pnl_pips"),
        "entry_price": worst.get("entry_price"),
        "duration_minutes": worst.get("duration_minutes"),
        "checklist_score": worst.get("checklist_score"),
    }


# ---------------------------------------------------------------------------
# Streaks
# ---------------------------------------------------------------------------
def _compute_streaks(trades: list[dict]) -> dict:
    """Compute win/loss streak information."""
    if not trades:
        return {"max_win_streak": 0, "max_loss_streak": 0, "current_streak": 0, "current_type": ""}

    max_win = 0
    max_loss = 0
    current = 0
    current_type = ""

    for t in trades:
        if t["outcome"] in ("full_win", "partial_win"):
            if current_type == "win":
                current += 1
            else:
                current = 1
                current_type = "win"
            max_win = max(max_win, current)
        elif t["outcome"] == "loss":
            if current_type == "loss":
                current += 1
            else:
                current = 1
                current_type = "loss"
            max_loss = max(max_loss, current)
        else:
            # Breakeven/expired don't break streaks but don't extend them
            pass

    return {
        "max_win_streak": max_win,
        "max_loss_streak": max_loss,
        "current_streak": current,
        "current_type": current_type,
    }


# ---------------------------------------------------------------------------
# Telegram formatting
# ---------------------------------------------------------------------------
def format_telegram_report(report: dict) -> str:
    """Format a backtest report for Telegram delivery."""
    o = report["overview"]
    s = report.get("streaks", {})

    lines = [
        f"📊 *Backtest Report*",
        f"{'━' * 28}",
        f"*Period:* {report['period']}",
        f"*Symbol:* {report['symbol']}",
        "",
        f"*📈 Overview*",
        f"Setups: {o['total_setups']} | Traded: {o['total_trades']} | No entry: {o['no_entry']}",
        f"✅ Wins: {o['wins']} | 🟡 Partial: {o['partial_wins']} | ❌ Losses: {o['losses']}",
        f"⏸ Breakeven: {o['breakevens']} | ⏰ Expired: {o['expired']}",
        "",
        f"*Win Rate:* {o['win_rate']}%",
        f"*Profit Factor:* {o['profit_factor']}",
        f"*Total P&L:* {'+' if o['total_pnl_pips'] >= 0 else ''}{o['total_pnl_pips']} pips",
        f"*Avg P&L/trade:* {'+' if o['avg_pnl_per_trade'] >= 0 else ''}{o['avg_pnl_per_trade']} pips",
        f"*Max Drawdown:* {o['max_drawdown_pips']} pips",
        f"*Avg R:R:* {o['avg_rr_achieved']}",
        f"*Avg Duration:* {int(o['avg_duration_minutes'])} min",
    ]

    # Streaks
    if s:
        lines.append("")
        lines.append(f"*🔥 Streaks*")
        lines.append(f"Best win streak: {s.get('max_win_streak', 0)}")
        lines.append(f"Worst loss streak: {s.get('max_loss_streak', 0)}")

    # Breakdown by confidence
    by_conf = report.get("by_confidence", {})
    if by_conf:
        lines.append("")
        lines.append(f"*📋 By Confidence*")
        for conf, stats in by_conf.items():
            lines.append(
                f"  {conf}: {stats['count']} trades, "
                f"{stats['win_rate']}% WR, "
                f"{'+' if stats['total_pnl'] >= 0 else ''}{stats['total_pnl']} pips"
            )

    # Breakdown by checklist score
    by_score = report.get("by_checklist_score", {})
    if by_score:
        lines.append("")
        lines.append(f"*📝 By Checklist Score*")
        for bracket, stats in by_score.items():
            lines.append(
                f"  {bracket}: {stats['count']} trades, "
                f"{stats['win_rate']}% WR, "
                f"{'+' if stats['total_pnl'] >= 0 else ''}{stats['total_pnl']} pips"
            )

    # Best/worst trades
    best = report.get("best_trade")
    worst = report.get("worst_trade")
    if best or worst:
        lines.append("")
        lines.append(f"*🏆 Notable Trades*")
        if best:
            lines.append(
                f"  Best: +{best['pnl_pips']} pips ({best['bias']} on {best['date']})"
            )
        if worst:
            lines.append(
                f"  Worst: {worst['pnl_pips']} pips ({worst['bias']} on {worst['date']})"
            )

    return "\n".join(lines)


def format_json_report(report: dict) -> str:
    """Format report as pretty-printed JSON (for API/dashboard)."""
    return json.dumps(report, indent=2, default=str)

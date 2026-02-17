# backtest.py — Backtest runner & orchestrator
"""Orchestrates backtesting by combining historical data, trade simulation, and reporting.

Two modes:
  Mode A: Historical setup simulation — runs existing archived trade setups
          (or future screenshot replay) against M1 candle data.
  Mode B: Manual setup testing — lets user define a hypothetical setup
          and test it against a specific date's M1 data.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional

from historical_data import (
    get_candles,
    get_trading_dates,
    init_history_tables,
)
from trade_simulator import SimulatedResult, simulate_trade

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.getenv("DATA_DIR", "/data"), "trades.db")


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
@contextmanager
def _get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_backtest_tables():
    """Create backtest-specific tables if they don't exist."""
    with _get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS backtest_runs (
                id TEXT PRIMARY KEY,
                created_at TEXT,
                symbol TEXT,
                start_date TEXT,
                end_date TEXT,
                mode TEXT DEFAULT 'historical',
                total_setups INTEGER DEFAULT 0,
                total_trades INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                partial_wins INTEGER DEFAULT 0,
                breakevens INTEGER DEFAULT 0,
                expired INTEGER DEFAULT 0,
                no_entry INTEGER DEFAULT 0,
                win_rate REAL DEFAULT 0,
                profit_factor REAL DEFAULT 0,
                total_pnl_pips REAL DEFAULT 0,
                max_drawdown_pips REAL DEFAULT 0,
                avg_rr_achieved REAL DEFAULT 0,
                avg_duration_minutes REAL DEFAULT 0,
                notes TEXT DEFAULT '',
                report_json TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS backtest_trades (
                id TEXT PRIMARY KEY,
                run_id TEXT,
                trade_date TEXT,
                symbol TEXT,
                bias TEXT,
                entry_price REAL DEFAULT 0,
                entry_time TEXT DEFAULT '',
                entry_min REAL DEFAULT 0,
                entry_max REAL DEFAULT 0,
                stop_loss REAL DEFAULT 0,
                tp1 REAL DEFAULT 0,
                tp2 REAL DEFAULT 0,
                sl_pips REAL DEFAULT 0,
                checklist_score TEXT DEFAULT '',
                confidence TEXT DEFAULT '',
                outcome TEXT DEFAULT '',
                pnl_pips REAL DEFAULT 0,
                tp1_hit INTEGER DEFAULT 0,
                tp1_time TEXT DEFAULT '',
                tp1_pips REAL DEFAULT 0,
                tp2_hit INTEGER DEFAULT 0,
                tp2_time TEXT DEFAULT '',
                tp2_pips REAL DEFAULT 0,
                sl_hit INTEGER DEFAULT 0,
                sl_time TEXT DEFAULT '',
                max_adverse_pips REAL DEFAULT 0,
                max_favorable_pips REAL DEFAULT 0,
                duration_minutes INTEGER DEFAULT 0,
                expired INTEGER DEFAULT 0,
                source TEXT DEFAULT 'manual',
                analysis_json TEXT DEFAULT '',
                FOREIGN KEY (run_id) REFERENCES backtest_runs(id)
            );

            CREATE INDEX IF NOT EXISTS idx_bt_trades_run ON backtest_trades(run_id);
            CREATE INDEX IF NOT EXISTS idx_bt_trades_date ON backtest_trades(trade_date);
            CREATE INDEX IF NOT EXISTS idx_bt_trades_outcome ON backtest_trades(outcome);
        """)
    logger.info("Backtest tables initialized.")


# ---------------------------------------------------------------------------
# Mode B: Manual Setup Testing
# ---------------------------------------------------------------------------
def test_setup(
    symbol: str,
    date: str,
    bias: str,
    entry_min: float,
    entry_max: float,
    stop_loss: float,
    tp1: float,
    tp2: float,
    sl_pips: float,
    search_start: str = "",
    kill_zone_end_hour: int = 20,
    timezone_offset: int = 1,
    tp1_close_pct: float = 50.0,
    checklist_score: str = "",
    confidence: str = "",
) -> SimulatedResult:
    """Test a hypothetical trade setup against a specific date's M1 data.

    This is the quick 'what-if' mode — user defines a setup and sees
    what would have happened on a given trading day.

    Args:
        symbol: Trading pair (e.g. "GBPJPY")
        date: Trading date "YYYY-MM-DD"
        bias: "long" or "short"
        entry_min/max: Entry zone boundaries
        stop_loss: SL price level
        tp1/tp2: Take profit levels
        sl_pips: Stop loss distance in pips
        search_start: Optional start time for entry search
        kill_zone_end_hour: MEZ hour when trade expires (default 20)
        timezone_offset: UTC offset for MEZ (default 1)
        tp1_close_pct: % closed at TP1 (default 50)
        checklist_score: For tagging (e.g. "10/12")
        confidence: For tagging ("HIGH", "MEDIUM", "LOW")

    Returns:
        SimulatedResult with full outcome details.
    """
    # Load M1 candles for this date
    start_time = f"{date} 00:00:00"
    end_time = f"{date} 23:59:59"
    m1_candles = get_candles(symbol, "M1", start_time=start_time, end_time=end_time)

    if not m1_candles:
        logger.warning("No M1 data for %s on %s", symbol, date)
        result = SimulatedResult(bias=bias, outcome="no_data")
        return result

    logger.info(
        "Testing %s %s setup on %s (%d M1 candles)",
        bias, symbol, date, len(m1_candles),
    )

    return simulate_trade(
        bias=bias,
        entry_min=entry_min,
        entry_max=entry_max,
        stop_loss=stop_loss,
        tp1=tp1,
        tp2=tp2,
        sl_pips=sl_pips,
        m1_candles=m1_candles,
        search_start=search_start,
        kill_zone_end_hour=kill_zone_end_hour,
        timezone_offset=timezone_offset,
        tp1_close_pct=tp1_close_pct,
        checklist_score=checklist_score,
        confidence=confidence,
    )


# ---------------------------------------------------------------------------
# Mode A: Historical Backtest (batch run over date range)
# ---------------------------------------------------------------------------
def run_backtest(
    symbol: str,
    setups: list[dict],
    start_date: str = "",
    end_date: str = "",
    kill_zone_end_hour: int = 20,
    timezone_offset: int = 1,
    tp1_close_pct: float = 50.0,
    notes: str = "",
    mode: str = "manual_batch",
) -> dict:
    """Run a batch backtest over one or more setups.

    Each setup dict must contain:
        date, bias, entry_min, entry_max, stop_loss, tp1, tp2, sl_pips
    Optional keys: search_start, checklist_score, confidence

    The runner loads M1 data per-date, simulates each setup, stores results
    in the database, and returns a summary.

    Args:
        symbol: Trading pair
        setups: List of setup dicts (each must include 'date')
        start_date: For metadata (auto-calculated if empty)
        end_date: For metadata (auto-calculated if empty)
        kill_zone_end_hour: MEZ hour for trade expiry
        timezone_offset: UTC offset
        tp1_close_pct: Default % closed at TP1
        notes: Optional description of this backtest run
        mode: "manual_batch", "historical_replay", etc.

    Returns:
        Dict with run_id, summary stats, and list of trade results.
    """
    if not setups:
        return {"error": "No setups provided", "run_id": None}

    run_id = uuid.uuid4().hex[:12]
    created_at = datetime.now(timezone.utc).isoformat()

    # Determine date range from setups if not provided
    dates_in_setups = sorted(set(s["date"] for s in setups))
    if not start_date:
        start_date = dates_in_setups[0]
    if not end_date:
        end_date = dates_in_setups[-1]

    logger.info(
        "Starting backtest %s: %d setups, %s to %s",
        run_id, len(setups), start_date, end_date,
    )

    # Cache M1 candles by date to avoid re-loading
    candle_cache: dict[str, list[dict]] = {}
    results: list[SimulatedResult] = []
    trade_rows: list[dict] = []

    for setup in setups:
        date = setup["date"]

        # Load M1 candles (cached per date)
        if date not in candle_cache:
            st = f"{date} 00:00:00"
            et = f"{date} 23:59:59"
            candle_cache[date] = get_candles(symbol, "M1", start_time=st, end_time=et)

        m1_candles = candle_cache[date]

        if not m1_candles:
            logger.warning("No M1 data for %s — skipping setup", date)
            res = SimulatedResult(
                bias=setup["bias"],
                outcome="no_data",
                checklist_score=setup.get("checklist_score", ""),
                confidence=setup.get("confidence", ""),
            )
        else:
            res = simulate_trade(
                bias=setup["bias"],
                entry_min=setup["entry_min"],
                entry_max=setup["entry_max"],
                stop_loss=setup["stop_loss"],
                tp1=setup["tp1"],
                tp2=setup["tp2"],
                sl_pips=setup["sl_pips"],
                m1_candles=m1_candles,
                search_start=setup.get("search_start", ""),
                kill_zone_end_hour=kill_zone_end_hour,
                timezone_offset=timezone_offset,
                tp1_close_pct=setup.get("tp1_close_pct", tp1_close_pct),
                checklist_score=setup.get("checklist_score", ""),
                confidence=setup.get("confidence", ""),
            )

        results.append(res)

        # Build trade row for DB storage
        trade_id = uuid.uuid4().hex[:12]
        trade_rows.append({
            "id": trade_id,
            "run_id": run_id,
            "trade_date": date,
            "symbol": symbol,
            "bias": res.bias,
            "entry_price": res.entry_price,
            "entry_time": res.entry_time,
            "entry_min": setup["entry_min"],
            "entry_max": setup["entry_max"],
            "stop_loss": res.stop_loss,
            "tp1": res.tp1,
            "tp2": res.tp2,
            "sl_pips": res.sl_pips,
            "checklist_score": res.checklist_score,
            "confidence": res.confidence,
            "outcome": res.outcome,
            "pnl_pips": res.pnl_pips,
            "tp1_hit": 1 if res.tp1_hit else 0,
            "tp1_time": res.tp1_time or "",
            "tp1_pips": res.tp1_pips,
            "tp2_hit": 1 if res.tp2_hit else 0,
            "tp2_time": res.tp2_time or "",
            "tp2_pips": res.tp2_pips,
            "sl_hit": 1 if res.sl_hit else 0,
            "sl_time": res.sl_time or "",
            "max_adverse_pips": res.max_adverse_pips,
            "max_favorable_pips": res.max_favorable_pips,
            "duration_minutes": res.duration_minutes,
            "expired": 1 if res.expired else 0,
            "source": mode,
            "analysis_json": json.dumps(setup.get("analysis", {})),
        })

    # --- Compute summary statistics ---
    summary = _compute_run_summary(results)

    # --- Store to database ---
    _store_backtest_run(
        run_id=run_id,
        created_at=created_at,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        mode=mode,
        summary=summary,
        notes=notes,
    )
    _store_backtest_trades(trade_rows)

    logger.info(
        "Backtest %s complete: %d trades, %.1f%% win rate, %.1f pips",
        run_id, summary["total_trades"], summary["win_rate"], summary["total_pnl_pips"],
    )

    return {
        "run_id": run_id,
        "created_at": created_at,
        "symbol": symbol,
        "start_date": start_date,
        "end_date": end_date,
        "mode": mode,
        "summary": summary,
        "trades": [r.to_dict() for r in results],
    }


# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------
def _compute_run_summary(results: list[SimulatedResult]) -> dict:
    """Compute aggregate statistics from a list of simulation results."""
    # Only count trades that actually entered the market
    traded = [r for r in results if r.outcome not in ("no_data", "no_entry")]
    all_results = results

    total_setups = len(all_results)
    total_trades = len(traded)
    no_entry = sum(1 for r in all_results if r.outcome in ("no_entry", "no_data"))

    wins = sum(1 for r in traded if r.outcome == "full_win")
    partial_wins = sum(1 for r in traded if r.outcome == "partial_win")
    losses = sum(1 for r in traded if r.outcome == "loss")
    breakevens = sum(1 for r in traded if r.outcome == "breakeven")
    expired = sum(1 for r in traded if r.outcome == "expired")

    # Win rate: full wins + partial wins as wins
    win_count = wins + partial_wins
    win_rate = (win_count / total_trades * 100.0) if total_trades > 0 else 0.0

    # P&L
    total_pnl = sum(r.pnl_pips for r in traded)
    gross_profit = sum(r.pnl_pips for r in traded if r.pnl_pips > 0)
    gross_loss = abs(sum(r.pnl_pips for r in traded if r.pnl_pips < 0))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf") if gross_profit > 0 else 0.0

    # Drawdown (simple running max drawdown)
    max_dd = 0.0
    running_pnl = 0.0
    peak_pnl = 0.0
    for r in traded:
        running_pnl += r.pnl_pips
        if running_pnl > peak_pnl:
            peak_pnl = running_pnl
        dd = peak_pnl - running_pnl
        if dd > max_dd:
            max_dd = dd

    # Average R:R achieved (for winning trades only)
    rr_list = []
    for r in traded:
        if r.sl_pips > 0 and r.pnl_pips != 0:
            rr_list.append(r.pnl_pips / r.sl_pips)
    avg_rr = sum(rr_list) / len(rr_list) if rr_list else 0.0

    # Duration
    durations = [r.duration_minutes for r in traded if r.duration_minutes > 0]
    avg_duration = sum(durations) / len(durations) if durations else 0.0

    # Max adverse excursion
    max_adverse = max((r.max_adverse_pips for r in traded), default=0.0)

    return {
        "total_setups": total_setups,
        "total_trades": total_trades,
        "no_entry": no_entry,
        "wins": wins,
        "partial_wins": partial_wins,
        "losses": losses,
        "breakevens": breakevens,
        "expired": expired,
        "win_rate": round(win_rate, 1),
        "profit_factor": round(profit_factor, 2),
        "total_pnl_pips": round(total_pnl, 1),
        "gross_profit_pips": round(gross_profit, 1),
        "gross_loss_pips": round(gross_loss, 1),
        "max_drawdown_pips": round(max_dd, 1),
        "avg_rr_achieved": round(avg_rr, 2),
        "avg_duration_minutes": round(avg_duration, 0),
        "max_adverse_excursion": round(max_adverse, 1),
    }


# ---------------------------------------------------------------------------
# Database storage
# ---------------------------------------------------------------------------
def _store_backtest_run(
    run_id: str,
    created_at: str,
    symbol: str,
    start_date: str,
    end_date: str,
    mode: str,
    summary: dict,
    notes: str,
):
    """Insert a backtest run record."""
    with _get_db() as conn:
        conn.execute(
            """INSERT INTO backtest_runs
            (id, created_at, symbol, start_date, end_date, mode,
             total_setups, total_trades, wins, losses, partial_wins,
             breakevens, expired, no_entry,
             win_rate, profit_factor, total_pnl_pips, max_drawdown_pips,
             avg_rr_achieved, avg_duration_minutes, notes, report_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id, created_at, symbol, start_date, end_date, mode,
                summary["total_setups"], summary["total_trades"],
                summary["wins"], summary["losses"], summary["partial_wins"],
                summary["breakevens"], summary["expired"], summary["no_entry"],
                summary["win_rate"], summary["profit_factor"],
                summary["total_pnl_pips"], summary["max_drawdown_pips"],
                summary["avg_rr_achieved"], summary["avg_duration_minutes"],
                notes, json.dumps(summary),
            ),
        )


def _store_backtest_trades(trade_rows: list[dict]):
    """Insert backtest trade records."""
    if not trade_rows:
        return

    with _get_db() as conn:
        conn.executemany(
            """INSERT INTO backtest_trades
            (id, run_id, trade_date, symbol, bias, entry_price, entry_time,
             entry_min, entry_max, stop_loss, tp1, tp2, sl_pips,
             checklist_score, confidence, outcome, pnl_pips,
             tp1_hit, tp1_time, tp1_pips, tp2_hit, tp2_time, tp2_pips,
             sl_hit, sl_time, max_adverse_pips, max_favorable_pips,
             duration_minutes, expired, source, analysis_json)
            VALUES (:id, :run_id, :trade_date, :symbol, :bias, :entry_price,
             :entry_time, :entry_min, :entry_max, :stop_loss, :tp1, :tp2,
             :sl_pips, :checklist_score, :confidence, :outcome, :pnl_pips,
             :tp1_hit, :tp1_time, :tp1_pips, :tp2_hit, :tp2_time, :tp2_pips,
             :sl_hit, :sl_time, :max_adverse_pips, :max_favorable_pips,
             :duration_minutes, :expired, :source, :analysis_json)""",
            trade_rows,
        )


# ---------------------------------------------------------------------------
# Query functions
# ---------------------------------------------------------------------------
def get_backtest_runs(limit: int = 20) -> list[dict]:
    """Return recent backtest runs, newest first."""
    with _get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM backtest_runs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_backtest_run(run_id: str) -> Optional[dict]:
    """Return a single backtest run by ID."""
    with _get_db() as conn:
        row = conn.execute(
            "SELECT * FROM backtest_runs WHERE id = ?", (run_id,)
        ).fetchone()
    return dict(row) if row else None


def get_backtest_trades(run_id: str) -> list[dict]:
    """Return all trades for a given backtest run."""
    with _get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM backtest_trades WHERE run_id = ? ORDER BY trade_date, entry_time",
            (run_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def delete_backtest_run(run_id: str) -> bool:
    """Delete a backtest run and its trades."""
    with _get_db() as conn:
        conn.execute("DELETE FROM backtest_trades WHERE run_id = ?", (run_id,))
        cursor = conn.execute("DELETE FROM backtest_runs WHERE id = ?", (run_id,))
    return cursor.rowcount > 0

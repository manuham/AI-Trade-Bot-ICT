# trade_simulator.py — Core trade simulation engine for backtesting
"""Simulates trade outcomes against historical M1 OHLC data.
Given a trade setup (entry zone, SL, TP1, TP2), scans M1 candles to determine
whether the trade would have won, lost, or expired."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# Default kill zone end (MEZ hour) — trades expire if not resolved
DEFAULT_KILL_ZONE_END_MEZ = 20
# Pip size for JPY pairs
GBPJPY_PIP_SIZE = 0.01


@dataclass
class SimulatedResult:
    """Result of simulating a single trade against historical data."""
    # Setup info
    bias: str = ""                         # "long" or "short"
    entry_price: float = 0.0               # Actual simulated entry (midpoint of zone)
    entry_time: str = ""                   # When price entered the zone
    stop_loss: float = 0.0
    tp1: float = 0.0
    tp2: float = 0.0
    sl_pips: float = 0.0

    # Outcome
    tp1_hit: bool = False
    tp1_time: Optional[str] = None
    tp1_pips: float = 0.0
    tp2_hit: bool = False
    tp2_time: Optional[str] = None
    tp2_pips: float = 0.0
    sl_hit: bool = False
    sl_time: Optional[str] = None
    outcome: str = "pending"               # "full_win", "partial_win", "loss", "breakeven", "expired"
    pnl_pips: float = 0.0                  # Net P&L in pips (accounting for split positions)

    # Risk metrics
    max_adverse_pips: float = 0.0          # Max drawdown during trade (worst pip excursion)
    max_favorable_pips: float = 0.0        # Max favorable excursion
    duration_minutes: int = 0              # From entry to final close
    expired: bool = False                  # True if kill zone ended without resolution

    # Context
    checklist_score: str = ""
    confidence: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def simulate_trade(
    bias: str,
    entry_min: float,
    entry_max: float,
    stop_loss: float,
    tp1: float,
    tp2: float,
    sl_pips: float,
    m1_candles: list[dict],
    search_start: str = "",
    kill_zone_end_hour: int = DEFAULT_KILL_ZONE_END_MEZ,
    timezone_offset: int = 1,
    pip_size: float = GBPJPY_PIP_SIZE,
    tp1_close_pct: float = 50.0,
    checklist_score: str = "",
    confidence: str = "",
) -> SimulatedResult:
    """Simulate a trade against M1 candles.

    The simulation follows the real EA logic:
    1. Scan candles until price enters the entry zone (entry_min to entry_max)
    2. Enter at the zone midpoint
    3. Scan forward: check each candle for SL, TP1, TP2 hits
    4. After TP1 hit: move SL to breakeven for the TP2 runner
    5. If kill zone ends (20:00 MEZ): close at current price (expired)

    Args:
        bias: "long" or "short"
        entry_min/max: Entry zone boundaries
        stop_loss: SL price level
        tp1/tp2: Take profit levels
        sl_pips: Stop loss distance in pips
        m1_candles: List of M1 candle dicts [{time, open, high, low, close, volume}]
        search_start: Start searching for entry from this time (optional)
        kill_zone_end_hour: MEZ hour when watch expires (default 20)
        timezone_offset: Hours from UTC to MEZ (default 1 for CET)
        pip_size: Price per pip (0.01 for JPY pairs)
        tp1_close_pct: % of position closed at TP1 (for P&L calc)
        checklist_score: For tagging the result
        confidence: For tagging the result

    Returns:
        SimulatedResult with full outcome details.
    """
    result = SimulatedResult(
        bias=bias,
        stop_loss=stop_loss,
        tp1=tp1,
        tp2=tp2,
        sl_pips=sl_pips,
        checklist_score=checklist_score,
        confidence=confidence,
    )

    if not m1_candles:
        result.outcome = "no_data"
        return result

    # --- Phase 1: Find entry ---
    entry_price = (entry_min + entry_max) / 2.0
    result.entry_price = entry_price
    entered = False
    entry_idx = -1

    for i, candle in enumerate(m1_candles):
        # Skip candles before search_start
        if search_start and candle["time"] < search_start:
            continue

        # Check kill zone expiry before entry
        candle_mez_hour = _get_mez_hour(candle["time"], timezone_offset)
        if candle_mez_hour >= kill_zone_end_hour:
            result.outcome = "expired"
            result.expired = True
            return result

        # Check if price touches the entry zone
        if bias == "long":
            # For longs, we want Ask price to drop INTO the zone
            if candle["low"] <= entry_max:
                entered = True
                entry_idx = i
                result.entry_time = candle["time"]
                break
        else:
            # For shorts, we want Bid price to rise INTO the zone
            if candle["high"] >= entry_min:
                entered = True
                entry_idx = i
                result.entry_time = candle["time"]
                break

    if not entered:
        result.outcome = "no_entry"
        result.expired = True
        return result

    # --- Phase 2: Simulate trade from entry ---
    tp1_hit = False
    tp2_hit = False
    sl_hit = False
    tp1_be_sl = entry_price  # After TP1 hit, SL moves to breakeven
    current_sl = stop_loss
    max_adverse = 0.0
    max_favorable = 0.0

    for candle in m1_candles[entry_idx + 1:]:
        # Check kill zone expiry
        candle_mez_hour = _get_mez_hour(candle["time"], timezone_offset)
        if candle_mez_hour >= kill_zone_end_hour:
            # Close at current price
            close_price = candle["close"]
            if bias == "long":
                remaining_pips = (close_price - entry_price) / pip_size
            else:
                remaining_pips = (entry_price - close_price) / pip_size

            if tp1_hit:
                # TP1 already banked, close runner at market
                tp1_pips = abs(tp1 - entry_price) / pip_size
                result.tp1_hit = True
                result.pnl_pips = (tp1_pips * tp1_close_pct / 100.0) + (remaining_pips * (1.0 - tp1_close_pct / 100.0))
                result.outcome = "partial_win" if result.pnl_pips > 0 else "breakeven"
            else:
                result.pnl_pips = remaining_pips
                result.outcome = "expired"

            result.expired = True
            result.duration_minutes = _calc_duration(result.entry_time, candle["time"])
            break

        # Track excursions
        if bias == "long":
            adverse = (entry_price - candle["low"]) / pip_size
            favorable = (candle["high"] - entry_price) / pip_size
        else:
            adverse = (candle["high"] - entry_price) / pip_size
            favorable = (entry_price - candle["low"]) / pip_size

        max_adverse = max(max_adverse, adverse)
        max_favorable = max(max_favorable, favorable)

        # --- Check SL hit ---
        if not sl_hit:
            if bias == "long" and candle["low"] <= current_sl:
                sl_hit = True
                result.sl_hit = True
                result.sl_time = candle["time"]

                if tp1_hit:
                    # TP1 banked, runner stopped at breakeven
                    tp1_pips = abs(tp1 - entry_price) / pip_size
                    result.pnl_pips = tp1_pips * tp1_close_pct / 100.0  # Only TP1 profit, runner at BE
                    result.outcome = "partial_win"
                else:
                    # Full stop loss
                    result.pnl_pips = -sl_pips
                    result.outcome = "loss"

                result.duration_minutes = _calc_duration(result.entry_time, candle["time"])
                break

            elif bias == "short" and candle["high"] >= current_sl:
                sl_hit = True
                result.sl_hit = True
                result.sl_time = candle["time"]

                if tp1_hit:
                    tp1_pips = abs(entry_price - tp1) / pip_size
                    result.pnl_pips = tp1_pips * tp1_close_pct / 100.0
                    result.outcome = "partial_win"
                else:
                    result.pnl_pips = -sl_pips
                    result.outcome = "loss"

                result.duration_minutes = _calc_duration(result.entry_time, candle["time"])
                break

        # --- Check TP1 hit (if not already hit) ---
        if not tp1_hit:
            if bias == "long" and candle["high"] >= tp1:
                tp1_hit = True
                result.tp1_hit = True
                result.tp1_time = candle["time"]
                result.tp1_pips = abs(tp1 - entry_price) / pip_size
                # Move SL to breakeven for the runner
                current_sl = entry_price

            elif bias == "short" and candle["low"] <= tp1:
                tp1_hit = True
                result.tp1_hit = True
                result.tp1_time = candle["time"]
                result.tp1_pips = abs(entry_price - tp1) / pip_size
                current_sl = entry_price

        # --- Check TP2 hit (only after TP1) ---
        if tp1_hit and not tp2_hit:
            if bias == "long" and candle["high"] >= tp2:
                tp2_hit = True
                result.tp2_hit = True
                result.tp2_time = candle["time"]
                result.tp2_pips = abs(tp2 - entry_price) / pip_size

                # Full win: TP1 closed partial, TP2 closed runner
                tp1_pips = abs(tp1 - entry_price) / pip_size
                tp2_pips = abs(tp2 - entry_price) / pip_size
                result.pnl_pips = (tp1_pips * tp1_close_pct / 100.0) + (tp2_pips * (1.0 - tp1_close_pct / 100.0))
                result.outcome = "full_win"
                result.duration_minutes = _calc_duration(result.entry_time, candle["time"])
                break

            elif bias == "short" and candle["low"] <= tp2:
                tp2_hit = True
                result.tp2_hit = True
                result.tp2_time = candle["time"]
                result.tp2_pips = abs(entry_price - tp2) / pip_size

                tp1_pips = abs(entry_price - tp1) / pip_size
                tp2_pips = abs(entry_price - tp2) / pip_size
                result.pnl_pips = (tp1_pips * tp1_close_pct / 100.0) + (tp2_pips * (1.0 - tp1_close_pct / 100.0))
                result.outcome = "full_win"
                result.duration_minutes = _calc_duration(result.entry_time, candle["time"])
                break

    result.max_adverse_pips = max_adverse
    result.max_favorable_pips = max_favorable

    # If we ran out of candles without resolution
    if result.outcome == "pending":
        result.outcome = "expired"
        result.expired = True
        if m1_candles:
            result.duration_minutes = _calc_duration(result.entry_time, m1_candles[-1]["time"])

    return result


def simulate_batch(
    setups: list[dict],
    m1_candles: list[dict],
    **kwargs,
) -> list[SimulatedResult]:
    """Run multiple simulations against the same M1 candle data.

    Args:
        setups: List of setup dicts, each with keys:
            bias, entry_min, entry_max, stop_loss, tp1, tp2, sl_pips,
            and optionally: search_start, checklist_score, confidence
        m1_candles: Full day M1 candles
        **kwargs: Additional kwargs passed to simulate_trade()

    Returns:
        List of SimulatedResult objects.
    """
    results = []
    for setup in setups:
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
            checklist_score=setup.get("checklist_score", ""),
            confidence=setup.get("confidence", ""),
            **kwargs,
        )
        results.append(res)

    return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_mez_hour(time_str: str, tz_offset: int = 1) -> int:
    """Extract MEZ hour from a candle time string.
    Assumes candle times are in server time (UTC + tz_offset depends on broker).
    For simplicity, we add the offset directly.
    """
    try:
        dt = datetime.strptime(time_str[:16], "%Y-%m-%d %H:%M")
        mez_hour = dt.hour + tz_offset
        if mez_hour >= 24:
            mez_hour -= 24
        return mez_hour
    except ValueError:
        return 0


def _calc_duration(start: str, end: str) -> int:
    """Calculate duration in minutes between two time strings."""
    try:
        t1 = datetime.strptime(start[:16], "%Y-%m-%d %H:%M")
        t2 = datetime.strptime(end[:16], "%Y-%m-%d %H:%M")
        return max(0, int((t2 - t1).total_seconds() / 60))
    except ValueError:
        return 0

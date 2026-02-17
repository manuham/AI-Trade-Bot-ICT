# historical_data.py — OHLC data loader for backtesting
"""Load, import, and query historical OHLC candle data.
Supports CSV import from MT5 exports and SQLite storage for fast queries.
Can resample M1 data to any higher timeframe (M5, H1, H4, D1)."""

from __future__ import annotations

import csv
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.getenv("DATA_DIR", "/data"), "trades.db")

# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------
@contextmanager
def _get_db():
    conn = sqlite3.connect(DB_PATH)
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


def init_history_tables():
    """Create the historical_ohlc table if it doesn't exist."""
    with _get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS historical_ohlc (
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                time TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER DEFAULT 0,
                PRIMARY KEY (symbol, timeframe, time)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ohlc_symbol_tf_time
            ON historical_ohlc (symbol, timeframe, time)
        """)
    logger.info("Historical OHLC tables initialized.")


# ---------------------------------------------------------------------------
# CSV Import — MT5 exports tab-separated or comma-separated OHLC
# ---------------------------------------------------------------------------
def import_csv_to_db(filepath: str, symbol: str, timeframe: str = "M1") -> int:
    """Import MT5-exported CSV into the historical_ohlc table.

    MT5 CSV format (tab-separated):
        Date       Time     Open     High     Low      Close    TickVol  Vol  Spread
        2024.01.02 00:00:00 172.836  172.849  172.825  172.843  156      0    0

    Also supports comma-separated and header-less formats.

    Returns the number of rows imported.
    """
    rows = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        # Detect delimiter
        first_line = f.readline()
        f.seek(0)

        if "\t" in first_line:
            delimiter = "\t"
        elif ";" in first_line:
            delimiter = ";"
        else:
            delimiter = ","

        reader = csv.reader(f, delimiter=delimiter)

        for line_num, row in enumerate(reader, 1):
            # Skip header rows
            if line_num == 1 and any(h.lower() in ["date", "time", "open", "<date>"] for h in row):
                continue

            try:
                # Clean up row (strip whitespace)
                row = [c.strip() for c in row if c.strip()]

                if len(row) < 6:
                    continue

                # Parse date and time
                date_str = row[0].replace(".", "-")  # 2024.01.02 → 2024-01-02
                time_str = row[1] if len(row[1]) > 4 else row[1] + ":00"

                # Some formats combine date+time in one field
                if " " in date_str and len(row) >= 5:
                    dt_combined = date_str
                    open_p, high_p, low_p, close_p = float(row[1]), float(row[2]), float(row[3]), float(row[4])
                    volume = int(row[5]) if len(row) > 5 else 0
                    candle_time = dt_combined.replace(".", "-")
                else:
                    candle_time = f"{date_str} {time_str}"
                    open_p = float(row[2])
                    high_p = float(row[3])
                    low_p = float(row[4])
                    close_p = float(row[5])
                    volume = int(row[6]) if len(row) > 6 else 0

                rows.append((symbol, timeframe, candle_time, open_p, high_p, low_p, close_p, volume))

            except (ValueError, IndexError) as e:
                if line_num <= 3:
                    continue  # Skip malformed header lines
                logger.warning("Skipping line %d: %s — %s", line_num, row, e)

    if not rows:
        logger.error("No valid rows found in %s", filepath)
        return 0

    # Bulk insert with REPLACE to handle duplicates
    with _get_db() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO historical_ohlc (symbol, timeframe, time, open, high, low, close, volume) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )

    logger.info("Imported %d %s candles for %s from %s", len(rows), timeframe, symbol, filepath)
    return len(rows)


# ---------------------------------------------------------------------------
# Query functions
# ---------------------------------------------------------------------------
def get_candles(
    symbol: str,
    timeframe: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 0,
) -> list[dict]:
    """Return OHLC candles from the database.

    Args:
        symbol: Trading pair (e.g., "GBPJPY")
        timeframe: "M1", "M5", "H1", "H4", "D1"
        start_time: ISO-ish string "YYYY-MM-DD HH:MM:SS" (inclusive)
        end_time: ISO-ish string (inclusive)
        limit: Max rows (0 = unlimited)

    Returns:
        List of dicts: [{time, open, high, low, close, volume}, ...]
    """
    query = "SELECT time, open, high, low, close, volume FROM historical_ohlc WHERE symbol = ? AND timeframe = ?"
    params: list = [symbol, timeframe]

    if start_time:
        query += " AND time >= ?"
        params.append(start_time)
    if end_time:
        query += " AND time <= ?"
        params.append(end_time)

    query += " ORDER BY time ASC"

    if limit > 0:
        query += " LIMIT ?"
        params.append(limit)

    with _get_db() as conn:
        rows = conn.execute(query, params).fetchall()

    return [dict(r) for r in rows]


def get_candle_count(symbol: str, timeframe: str) -> int:
    """Return total number of candles stored for a symbol/timeframe."""
    with _get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM historical_ohlc WHERE symbol = ? AND timeframe = ?",
            (symbol, timeframe),
        ).fetchone()
    return row["cnt"] if row else 0


def get_date_range(symbol: str, timeframe: str) -> tuple[Optional[str], Optional[str]]:
    """Return (earliest, latest) candle times for a symbol/timeframe."""
    with _get_db() as conn:
        row = conn.execute(
            "SELECT MIN(time) as first_t, MAX(time) as last_t FROM historical_ohlc WHERE symbol = ? AND timeframe = ?",
            (symbol, timeframe),
        ).fetchone()
    if row and row["first_t"]:
        return (row["first_t"], row["last_t"])
    return (None, None)


def get_trading_dates(symbol: str, timeframe: str = "M1") -> list[str]:
    """Return a sorted list of unique trading dates (YYYY-MM-DD) that have data."""
    with _get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT SUBSTR(time, 1, 10) as trade_date FROM historical_ohlc "
            "WHERE symbol = ? AND timeframe = ? ORDER BY trade_date",
            (symbol, timeframe),
        ).fetchall()
    return [r["trade_date"] for r in rows]


# ---------------------------------------------------------------------------
# Resampling — convert M1 candles to higher timeframes
# ---------------------------------------------------------------------------
_TF_MINUTES = {
    "M1": 1, "M5": 5, "M15": 15, "M30": 30,
    "H1": 60, "H4": 240, "D1": 1440,
}


def resample(m1_candles: list[dict], target_tf: str) -> list[dict]:
    """Resample M1 candles to a higher timeframe.

    Args:
        m1_candles: List of M1 candles [{time, open, high, low, close, volume}, ...]
        target_tf: Target timeframe ("M5", "H1", "H4", "D1")

    Returns:
        List of resampled candles in the same format.
    """
    if target_tf not in _TF_MINUTES:
        raise ValueError(f"Unknown timeframe: {target_tf}")

    interval_min = _TF_MINUTES[target_tf]
    if interval_min <= 1:
        return m1_candles  # Already M1

    result = []
    bucket: list[dict] = []
    bucket_start: Optional[datetime] = None

    for candle in m1_candles:
        ct = _parse_time(candle["time"])

        if target_tf == "D1":
            # Group by calendar date
            bucket_key = ct.date()
            if bucket and _parse_time(bucket[0]["time"]).date() != bucket_key:
                result.append(_aggregate_bucket(bucket))
                bucket = []
        else:
            # Group by fixed intervals
            minutes_since_midnight = ct.hour * 60 + ct.minute
            bucket_idx = minutes_since_midnight // interval_min

            if bucket:
                prev_ct = _parse_time(bucket[0]["time"])
                prev_idx = (prev_ct.hour * 60 + prev_ct.minute) // interval_min
                if bucket_idx != prev_idx or ct.date() != prev_ct.date():
                    result.append(_aggregate_bucket(bucket))
                    bucket = []

        bucket.append(candle)

    # Don't forget the last bucket
    if bucket:
        result.append(_aggregate_bucket(bucket))

    return result


def _aggregate_bucket(candles: list[dict]) -> dict:
    """Aggregate a group of candles into one OHLC bar."""
    return {
        "time": candles[0]["time"],
        "open": candles[0]["open"],
        "high": max(c["high"] for c in candles),
        "low": min(c["low"] for c in candles),
        "close": candles[-1]["close"],
        "volume": sum(c.get("volume", 0) for c in candles),
    }


def _parse_time(t: str) -> datetime:
    """Parse a candle time string to datetime."""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(t, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse time: {t}")


# ---------------------------------------------------------------------------
# Resample and store — convenience for importing M1 then building all TFs
# ---------------------------------------------------------------------------
def resample_and_store(symbol: str) -> dict[str, int]:
    """Load all M1 candles for a symbol, resample to M5/H1/H4/D1, and store.

    Returns dict of {timeframe: count} for all resampled timeframes.
    """
    m1_candles = get_candles(symbol, "M1")
    if not m1_candles:
        logger.warning("No M1 data found for %s — cannot resample.", symbol)
        return {}

    counts = {}
    for tf in ["M5", "H1", "H4", "D1"]:
        resampled = resample(m1_candles, tf)
        if resampled:
            rows = [(symbol, tf, c["time"], c["open"], c["high"], c["low"], c["close"], c["volume"]) for c in resampled]
            with _get_db() as conn:
                conn.executemany(
                    "INSERT OR REPLACE INTO historical_ohlc (symbol, timeframe, time, open, high, low, close, volume) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    rows,
                )
            counts[tf] = len(resampled)
            logger.info("Resampled %d %s candles for %s", len(resampled), tf, symbol)

    return counts

"""FTMO-compliant news filter.

Fetches the ForexFactory economic calendar and blocks trade execution
within a configurable window around high-impact news events.

FTMO rule: no opening/closing positions 2 minutes before or after
high-impact news releases for the affected instrument.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

from pair_profiles import get_profile

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
BUFFER_MINUTES = 2          # FTMO minimum: 2 minutes before & after (fallback)
WARN_AHEAD_MINUTES = 60     # Show warning on setups if news within 60 min

# Tiered buffer by event importance — critical events get wider windows
# Title keywords that trigger the extended buffer (case-insensitive match)
_CRITICAL_KEYWORDS = {
    "federal funds rate", "fomc", "non-farm", "nonfarm", "nfp",
    "cpi ", "consumer price index",
    "official bank rate", "boe interest", "ecb interest", "boj interest",
    "monetary policy", "interest rate decision",
}
_CRITICAL_BUFFER_MINUTES = 15   # FOMC, NFP, CPI, central bank rate decisions
_HIGH_BUFFER_MINUTES = 5        # Other high-impact (PMI, GDP, employment, retail sales)


def _get_event_buffer(event_title: str) -> int:
    """Return the appropriate buffer in minutes based on event importance."""
    title_lower = event_title.lower()
    for keyword in _CRITICAL_KEYWORDS:
        if keyword in title_lower:
            return _CRITICAL_BUFFER_MINUTES
    return _HIGH_BUFFER_MINUTES
CACHE_TTL_HOURS = 6         # Re-fetch calendar every 6 hours

# ---------------------------------------------------------------------------
# In-memory cache
# ---------------------------------------------------------------------------
_calendar_cache: list[dict] = []
_last_fetch: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------
@dataclass
class NewsCheckResult:
    """Result of a news restriction check."""
    blocked: bool               # True if trade execution should be blocked
    warning: bool               # True if news is upcoming (within WARN_AHEAD_MINUTES)
    event_title: str = ""       # e.g. "Non-Farm Employment Change"
    event_currency: str = ""    # e.g. "USD"
    event_time: Optional[datetime] = None
    minutes_until: int = 0      # Minutes until the event (negative = already passed)
    message: str = ""           # Human-readable message
    block_ends_at: Optional[datetime] = None  # When the restriction window ends


# ---------------------------------------------------------------------------
# Calendar fetching
# ---------------------------------------------------------------------------
async def _fetch_calendar() -> list[dict]:
    """Fetch this week's economic calendar from ForexFactory."""
    global _calendar_cache, _last_fetch

    now = datetime.now(timezone.utc)

    # Return cache if still fresh
    if _last_fetch and (now - _last_fetch) < timedelta(hours=CACHE_TTL_HOURS) and _calendar_cache:
        return _calendar_cache

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(CALENDAR_URL)
            resp.raise_for_status()
            data = resp.json()

        _calendar_cache = data
        _last_fetch = now
        logger.info("Economic calendar fetched: %d events", len(data))
        return data

    except Exception as e:
        logger.error("Failed to fetch economic calendar: %s", e)
        # Return stale cache if available, empty list otherwise
        return _calendar_cache


def _parse_event_time(date_str: str) -> Optional[datetime]:
    """Parse ForexFactory date string (ISO 8601 with offset) to UTC datetime."""
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def _get_currencies(symbol: str) -> set[str]:
    """Get the set of currencies affected by a symbol."""
    profile = get_profile(symbol)
    return {profile["base_currency"], profile["quote_currency"]}


# ---------------------------------------------------------------------------
# Core check functions
# ---------------------------------------------------------------------------
async def check_news_restriction(
    symbol: str,
    buffer_minutes: int = BUFFER_MINUTES,
) -> NewsCheckResult:
    """Check if trading is restricted for a symbol due to upcoming news.

    Returns a NewsCheckResult indicating whether execution is blocked
    or if there's a warning about upcoming news.
    """
    calendar = await _fetch_calendar()
    if not calendar:
        # If we can't fetch the calendar, allow trading but warn
        return NewsCheckResult(
            blocked=False,
            warning=True,
            message="Could not fetch economic calendar. Proceed with caution.",
        )

    currencies = _get_currencies(symbol)
    now = datetime.now(timezone.utc)

    closest_event: Optional[dict] = None
    closest_delta: Optional[timedelta] = None

    for event in calendar:
        # Only care about High impact events
        if event.get("impact") != "High":
            continue

        # Check if event currency matches our pair
        event_currency = event.get("country", "")
        if event_currency not in currencies:
            continue

        event_time = _parse_event_time(event.get("date", ""))
        if not event_time:
            continue

        delta = event_time - now
        abs_delta = abs(delta)

        # Tiered buffer: critical events (FOMC, NFP, CPI) get wider windows
        event_title = event.get("title", "Unknown")
        effective_buffer = _get_event_buffer(event_title)
        buffer = timedelta(minutes=effective_buffer)

        if abs_delta <= buffer:
            minutes_until = int(delta.total_seconds() / 60)
            block_ends = event_time + timedelta(minutes=effective_buffer)
            block_ends_mez = block_ends + timedelta(hours=1)  # UTC → MEZ
            ends_in_min = max(1, int((block_ends - now).total_seconds() / 60))
            tier_label = "CRITICAL" if effective_buffer >= _CRITICAL_BUFFER_MINUTES else "HIGH"
            return NewsCheckResult(
                blocked=True,
                warning=True,
                event_title=event_title,
                event_currency=event_currency,
                event_time=event_time,
                minutes_until=minutes_until,
                block_ends_at=block_ends,
                message=(
                    f"BLOCKED [{tier_label}]: {event_currency} news "
                    f"\"{event_title}\" "
                    f"{'in ' + str(abs(minutes_until)) + ' min' if minutes_until > 0 else str(abs(minutes_until)) + ' min ago'}. "
                    f"Restriction: ±{effective_buffer} min. "
                    f"Ends at {block_ends_mez.strftime('%H:%M')} MEZ (~{ends_in_min} min)."
                ),
            )

        # Track closest upcoming event for warning
        if delta.total_seconds() > 0:  # Only future events
            warn_window = timedelta(minutes=WARN_AHEAD_MINUTES)
            if delta <= warn_window:
                if closest_delta is None or delta < closest_delta:
                    closest_event = event
                    closest_delta = delta

    # No blocking, but maybe a warning
    if closest_event and closest_delta:
        minutes_until = int(closest_delta.total_seconds() / 60)
        event_title = closest_event.get("title", "Unknown")
        effective_buffer = _get_event_buffer(event_title)
        return NewsCheckResult(
            blocked=False,
            warning=True,
            event_title=event_title,
            event_currency=closest_event.get("country", ""),
            event_time=_parse_event_time(closest_event.get("date", "")),
            minutes_until=minutes_until,
            message=(
                f"{'CRITICAL' if effective_buffer >= _CRITICAL_BUFFER_MINUTES else 'High-impact'} "
                f"{closest_event.get('country', '')} news "
                f"\"{event_title}\" in {minutes_until} min. "
                f"Trade will be blocked ±{effective_buffer} min of release."
            ),
        )

    return NewsCheckResult(blocked=False, warning=False)


async def get_upcoming_news(
    symbols: Optional[list[str]] = None,
    hours_ahead: int = 24,
) -> list[dict]:
    """Get upcoming high-impact news events for the given symbols.

    Returns a list of events sorted by time.
    """
    calendar = await _fetch_calendar()
    if not calendar:
        return []

    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(hours=hours_ahead)

    # Collect relevant currencies
    all_currencies: set[str] = set()
    if symbols:
        for sym in symbols:
            all_currencies.update(_get_currencies(sym))
    else:
        # Show all major currencies if no symbols specified
        all_currencies = {"USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD"}

    events = []
    for event in calendar:
        if event.get("impact") != "High":
            continue

        if event.get("country", "") not in all_currencies:
            continue

        event_time = _parse_event_time(event.get("date", ""))
        if not event_time:
            continue

        if now <= event_time <= cutoff:
            events.append({
                "title": event.get("title", ""),
                "currency": event.get("country", ""),
                "time": event_time,
                "forecast": event.get("forecast", ""),
                "previous": event.get("previous", ""),
            })

    events.sort(key=lambda e: e["time"])
    return events

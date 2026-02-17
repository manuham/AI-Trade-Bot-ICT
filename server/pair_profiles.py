"""Pair-specific configuration profiles for multi-pair support."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Session context templates — injected into Claude prompts per pair
# ---------------------------------------------------------------------------
_SESSION_CONTEXT_LONDON_KZ = """### Step 3b — London Kill Zone Context
You are analyzing during the London Kill Zone (08:00-11:00 MEZ), the most active period for {symbol}:
- **Asian Range Sweep**: London typically opens by sweeping one side of the Asian session range (00:00-08:00 MEZ):
  - Asian HIGH swept → institutional selling above, bias shifts BEARISH (expect reversal down)
  - Asian LOW swept → institutional buying below, bias shifts BULLISH (expect reversal up)
  - Neither swept yet → the sweep is coming, identify which side is more vulnerable
- **PDH/PDL** are the PRIMARY liquidity targets during this window
- Most institutional {symbol} moves happen in the first 90 minutes (08:00-09:30 MEZ)
- After 09:30, moves tend to consolidate — prefer entries before 09:30 if possible
- Check if the Asian range was tight (<30 pips) or wide (>60 pips) — tight ranges often lead to explosive London moves"""

_SESSION_CONTEXT_LONDON_NY = """### Step 3b — London & NY Overlap Session Context
You are analyzing during the London & NY Overlap (08:00-17:00 MEZ), the highest-volume period for {symbol}:
- **London Open (08:00-09:30 MEZ)**: Initial volatility spike — London often sweeps Asian range before establishing direction
  - Asian HIGH swept → institutional selling above, bias shifts BEARISH
  - Asian LOW swept → institutional buying below, bias shifts BULLISH
- **NY Pre-Market (13:00-14:30 MEZ)**: Second volatility spike — NY may continue or reverse London's move
- **Overlap Peak (14:30-16:00 MEZ)**: Highest liquidity — major moves often complete or reverse here
- **PDH/PDL** and **Weekly H/L** are primary institutional targets
- {symbol} tends to have cleaner price action than JPY crosses — tighter spreads reward precision entries
- After 16:00 MEZ, volume typically fades — prefer entries before 16:00
- Check if London and NY are aligned (trend continuation) or opposing (reversal risk)"""

_SESSION_RULES_LONDON_KZ = """IMPORTANT: Actively look for setups. The London Kill Zone (08:00-11:00 MEZ) almost always offers at least one high-probability {symbol} setup, especially around the Asian range sweep. A medium-confidence setup with clear risk management is still valuable — the system will wait for M1 confirmation before entering."""

_SESSION_RULES_LONDON_NY = """IMPORTANT: Actively look for setups. The London & NY Overlap (08:00-17:00 MEZ) provides the highest liquidity for {symbol}. Watch for setups at the London open (08:00-09:30 MEZ) and again at NY open (13:00-14:30 MEZ). A medium-confidence setup with clear risk management is still valuable — the system will wait for M1 confirmation before entering."""


PAIR_PROFILES: dict[str, dict] = {
    "GBPJPY": {
        "digits": 3,
        "typical_spread": "2-3 pips",
        "key_sessions": "London Kill Zone (08:00-11:00 MEZ)",
        "base_currency": "GBP",
        "quote_currency": "JPY",
        "specialization": "GBPJPY London Kill Zone — Asian range sweep patterns",
        "kill_zone_start_mez": 8,
        "kill_zone_end_mez": 20,
        "session_name": "London Kill Zone (08:00-11:00 MEZ)",
        "session_context": _SESSION_CONTEXT_LONDON_KZ,
        "session_rules": _SESSION_RULES_LONDON_KZ,
        "optimal_entry_window": "08:00-09:30 MEZ",
        "search_queries": [
            "GBPJPY forecast today",
            "GBP news today",
            "JPY news today",
            "forex economic calendar today GBP JPY",
        ],
        "fundamental_bias_options": '"bullish_gbp" or "bearish_gbp" or "neutral"',
    },
    "EURUSD": {
        "digits": 5,
        "typical_spread": "0.5-1.5 pips",
        "key_sessions": "London & NY Overlap (08:00-17:00 MEZ)",
        "base_currency": "EUR",
        "quote_currency": "USD",
        "specialization": "EURUSD London & NY Overlap — highest liquidity major pair",
        "kill_zone_start_mez": 8,
        "kill_zone_end_mez": 17,
        "session_name": "London & NY Overlap (08:00-17:00 MEZ)",
        "session_context": _SESSION_CONTEXT_LONDON_NY,
        "session_rules": _SESSION_RULES_LONDON_NY,
        "optimal_entry_window": "08:00-09:30 MEZ or 13:00-14:30 MEZ",
        "search_queries": [
            "EURUSD forecast today",
            "EUR news today",
            "USD news today",
            "forex economic calendar today EUR USD",
        ],
        "fundamental_bias_options": '"bullish_eur" or "bearish_eur" or "neutral"',
    },
    "GBPUSD": {
        "digits": 5,
        "typical_spread": "1-2 pips",
        "key_sessions": "London & NY Overlap (08:00-17:00 MEZ)",
        "base_currency": "GBP",
        "quote_currency": "USD",
        "specialization": "GBPUSD London & NY Overlap — GBP liquidity peaks at London open",
        "kill_zone_start_mez": 8,
        "kill_zone_end_mez": 17,
        "session_name": "London & NY Overlap (08:00-17:00 MEZ)",
        "session_context": _SESSION_CONTEXT_LONDON_NY,
        "session_rules": _SESSION_RULES_LONDON_NY,
        "optimal_entry_window": "08:00-09:30 MEZ or 13:00-14:30 MEZ",
        "search_queries": [
            "GBPUSD forecast today",
            "GBP news today",
            "USD news today",
            "forex economic calendar today GBP USD",
        ],
        "fundamental_bias_options": '"bullish_gbp" or "bearish_gbp" or "neutral"',
    },
    "XAUUSD": {
        "digits": 2,
        "typical_spread": "2-4 pips",
        "key_sessions": "London & NY overlap",
        "base_currency": "XAU",
        "quote_currency": "USD",
        "specialization": "gold / precious metals",
        "search_queries": [
            "XAUUSD gold forecast today",
            "gold price news today",
            "USD news today",
            "forex economic calendar today USD gold",
        ],
        "fundamental_bias_options": '"bullish_gold" or "bearish_gold" or "neutral"',
    },
    "USDJPY": {
        "digits": 3,
        "typical_spread": "1-2 pips",
        "key_sessions": "Tokyo & NY overlap",
        "base_currency": "USD",
        "quote_currency": "JPY",
        "specialization": "JPY crosses",
        "search_queries": [
            "USDJPY forecast today",
            "USD news today",
            "JPY news today",
            "forex economic calendar today USD JPY",
        ],
        "fundamental_bias_options": '"bullish_usd" or "bearish_usd" or "neutral"',
    },
    "EURJPY": {
        "digits": 3,
        "typical_spread": "2-3 pips",
        "key_sessions": "London & Tokyo overlap",
        "base_currency": "EUR",
        "quote_currency": "JPY",
        "specialization": "JPY crosses",
        "search_queries": [
            "EURJPY forecast today",
            "EUR news today",
            "JPY news today",
            "forex economic calendar today EUR JPY",
        ],
        "fundamental_bias_options": '"bullish_eur" or "bearish_eur" or "neutral"',
    },
}


def get_profile(symbol: str) -> dict:
    """Get pair profile. Returns sensible defaults for unknown pairs."""
    if symbol in PAIR_PROFILES:
        return PAIR_PROFILES[symbol]

    # Auto-detect defaults based on symbol name
    is_jpy = symbol.endswith("JPY")
    is_gold = symbol.startswith("XAU")

    # Try to extract base/quote currencies
    base = symbol[:3]
    quote = symbol[3:]

    return {
        "digits": 2 if is_gold else (3 if is_jpy else 5),
        "typical_spread": "2-4 pips" if is_gold else ("2-3 pips" if is_jpy else "1-2 pips"),
        "key_sessions": "London & NY overlap",
        "base_currency": base,
        "quote_currency": quote,
        "specialization": "forex pairs",
        "kill_zone_start_mez": 8,
        "kill_zone_end_mez": 17,
        "session_name": "London & NY Overlap (08:00-17:00 MEZ)",
        "session_context": _SESSION_CONTEXT_LONDON_NY,
        "session_rules": _SESSION_RULES_LONDON_NY,
        "optimal_entry_window": "08:00-16:00 MEZ",
        "search_queries": [
            f"{symbol} forecast today",
            f"{base} news today",
            f"{quote} news today",
            f"forex economic calendar today {base} {quote}",
        ],
        "fundamental_bias_options": f'"bullish_{base.lower()}" or "bearish_{base.lower()}" or "neutral"',
    }

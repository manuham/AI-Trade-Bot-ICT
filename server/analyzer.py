from __future__ import annotations

import base64
import json
import logging
from datetime import date
from typing import Optional

import anthropic

from config import ANTHROPIC_API_KEY
from models import AnalysisResult, MarketData, TradeSetup
from pair_profiles import get_profile

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Daily fundamentals cache  (one web-search per pair per day)
# ---------------------------------------------------------------------------
_fundamentals_cache: dict[str, dict] = {}  # key = "GBPJPY:2026-02-09"


def _cache_key(symbol: str) -> str:
    return f"{symbol}:{date.today().isoformat()}"


def get_cached_fundamentals(symbol: str) -> Optional[str]:
    """Return cached fundamentals text for today, or None."""
    entry = _fundamentals_cache.get(_cache_key(symbol))
    return entry["text"] if entry else None


def store_fundamentals(symbol: str, text: str):
    """Cache fundamentals text for today."""
    _fundamentals_cache[_cache_key(symbol)] = {"text": text, "date": date.today().isoformat()}
    logger.info("Fundamentals cached for %s (%d chars)", symbol, len(text))


# ---------------------------------------------------------------------------
# Image encoding
# ---------------------------------------------------------------------------
def _encode_image(image_bytes: bytes) -> str:
    return base64.standard_b64encode(image_bytes).decode("utf-8")


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------
def build_system_prompt(symbol: str, profile: dict, fundamentals: Optional[str] = None) -> str:
    """Build the full ICT analysis system prompt, parameterized by pair."""
    base = profile["base_currency"]
    quote = profile["quote_currency"]
    search_queries = ", ".join(f'"{q}"' for q in profile["search_queries"])

    # Fundamentals section: either inject cached text or instruct web search
    if fundamentals:
        fundamentals_section = f"""### Step 0 — Fundamentals (pre-loaded)
The following fundamental analysis was gathered earlier today. Use it as context — do NOT run web searches.

{fundamentals}"""
    else:
        fundamentals_section = f"""### Step 0 — Fundamentals (web search)
Use web search to check current {base} and {quote} drivers, breaking news, and the economic calendar for the next 24 hours. Search for {search_queries}."""

    return f"""You are a senior institutional FX analyst specializing in {profile['specialization']} using ICT (Inner Circle Trader) methodology. You are analyzing live {symbol} charts from MetaTrader 5.

## CONTEXT
- Pair: {symbol}
- Active sessions: {profile['key_sessions']}
- Risk per trade: 1%
- TP strategy: 50% closed at TP1, runner to TP2
- The chart includes horizontal swing-level lines drawn by a custom indicator

## YOUR TASK

{fundamentals_section}

### Step 1 — MANDATORY: Higher-Timeframe Trend (H1)
Before ANY setup, you MUST determine the H1 trend:
- Identify the last 4-6 swing highs and swing lows on H1
- Are they making higher highs + higher lows (BULLISH) or lower highs + lower lows (BEARISH)?
- If mixed/ranging, define the range boundaries (high and low)
- This H1 trend is the DOMINANT BIAS. All setups must respect it unless you explicitly label the setup as "counter-trend" with extra justification

### Step 2 — Premium/Discount Zone
- Define the current H1 range (recent swing high to recent swing low)
- Calculate the equilibrium (50% level)
- Determine if price is currently in:
  - DISCOUNT zone (below 50%) — favorable for longs
  - PREMIUM zone (above 50%) — favorable for shorts
  - EQUILIBRIUM (near 50%) — no-man's-land, avoid entries here
- Do NOT propose longs from premium zone or shorts from discount zone unless counter-trend with strong justification

### Step 3 — Multi-Timeframe Structure (H1 → M15 → M5)
- Market structure per timeframe: BOS, ChoCH locations with exact prices
- Are lower timeframes aligned with H1, or showing early reversal signs?
- Key swing highs/lows with exact price levels

### Step 4 — Key Levels (be precise with prices)
- Order blocks / supply & demand zones — specify if tested or untested
- Fair Value Gaps (FVGs) — specify if filled or open
- Institutional liquidity pools (equal highs/lows, stop clusters)
- Distinguish between: where price BOUNCED FROM vs where price IS NOW (these are different!)

### Step 5 — Setup Generation
ONLY propose setups that satisfy ALL of these:
1. H1 trend-aligned (or explicitly labeled "counter-trend" with 4+ confluence factors)
2. Entry in the correct zone (longs from discount, shorts from premium)
3. Minimum 1:2 R:R on TP1 (not just TP2)
4. At least 3 confluence factors
5. Clear invalidation level

For counter-trend setups, you MUST:
- Explicitly state "This is a COUNTER-TREND trade"
- Require 4+ confluence factors instead of 3
- Show a ChoCH or BOS on M15 confirming the reversal
- Only rate confidence as "medium" at most (never "high" for counter-trend)

### Step 6 — NO TRADE Decision
Return an EMPTY setups array if ANY of these apply:
- Price is in equilibrium / mid-range with no clear direction
- H1 trend is bearish but only long setups are visible (and vice versa)
- High-impact news within 2 hours
- No untested key levels nearby
- Confluence count is below 3
- TP1 R:R is below 1:2
- You are unsure — when in doubt, stay out

## OUTPUT FORMAT
Respond with ONLY valid JSON matching this structure:
{{
  "setups": [
    {{
      "bias": "long" or "short",
      "entry_min": price,
      "entry_max": price,
      "stop_loss": price,
      "sl_pips": number,
      "tp1": price,
      "tp1_pips": number,
      "tp2": price,
      "tp2_pips": number,
      "rr_tp1": number,
      "rr_tp2": number,
      "confluence": ["reason1", "reason2", "reason3"],
      "invalidation": "description",
      "timeframe_type": "scalp" or "intraday" or "swing",
      "confidence": "high" or "medium" or "low",
      "news_warning": "description or null",
      "counter_trend": true or false,
      "h1_trend": "bullish" or "bearish" or "ranging",
      "price_zone": "premium" or "discount" or "equilibrium"
    }}
  ],
  "h1_trend_analysis": "2-3 sentences describing the H1 swing structure and dominant trend",
  "market_summary": "2-3 sentence summary",
  "primary_scenario": "description",
  "alternative_scenario": "description",
  "fundamental_bias": {profile['fundamental_bias_options']},
  "upcoming_events": ["event1", "event2"]
}}

## RULES
- No setup is better than a bad setup — return empty setups array if no clear edge
- ALWAYS identify the H1 trend FIRST — this overrides everything
- Trade WITH the trend, not against it
- Consider {symbol} spread (~{profile['typical_spread']}) in SL/TP calculations
- Flag any setups near high-impact news events
- Be honest about uncertainty — "NO TRADE" is a valid and respectable output
- Always respond with valid JSON, nothing else"""


def _build_screening_prompt(symbol: str, profile: dict, fundamentals: Optional[str] = None) -> str:
    """Lightweight screening prompt for Sonnet — quick yes/no on trade viability."""
    fund_section = ""
    if fundamentals:
        fund_section = f"\n\nFundamental context (gathered earlier today):\n{fundamentals}"

    return f"""You are a quick-scan FX analyst. Look at these {symbol} charts (H1, M15, M5) and determine if there is a clear, high-probability ICT trade setup.{fund_section}

Check:
1. H1 trend direction (bullish / bearish / ranging)
2. Is price at a key level (order block, FVG, liquidity zone)?
3. Do multiple timeframes align?
4. Is there a clear entry with minimum 1:2 R:R on TP1?

Respond with ONLY this JSON:
{{
  "has_setup": true or false,
  "h1_trend": "bullish" or "bearish" or "ranging",
  "reasoning": "1-2 sentences explaining why trade or no trade",
  "market_summary": "1-2 sentence market overview"
}}"""


# ---------------------------------------------------------------------------
# User content builders
# ---------------------------------------------------------------------------
def _build_image_content(
    screenshot_h1: bytes,
    screenshot_m15: bytes,
    screenshot_m5: bytes,
    market_data: MarketData,
) -> list[dict]:
    """Build the multi-modal user message content for Claude."""
    content: list[dict] = []

    for label, img_bytes in [
        ("H1", screenshot_h1),
        ("M15", screenshot_m15),
        ("M5", screenshot_m5),
    ]:
        content.append({"type": "text", "text": f"--- {label} Chart ---"})
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": _encode_image(img_bytes),
                },
            }
        )

    market_dict = market_data.model_dump()
    ohlc_summary = {
        "h1_bars": len(market_dict.get("ohlc_h1", [])),
        "m15_bars": len(market_dict.get("ohlc_m15", [])),
        "m5_bars": len(market_dict.get("ohlc_m5", [])),
    }
    display_data = {k: v for k, v in market_dict.items() if not k.startswith("ohlc_")}
    display_data["ohlc_bar_counts"] = ohlc_summary

    content.append(
        {
            "type": "text",
            "text": (
                "--- Market Data ---\n"
                + json.dumps(display_data, indent=2)
                + "\n\n--- Full OHLC Data ---\n"
                + json.dumps(
                    {
                        "ohlc_h1": market_dict.get("ohlc_h1", []),
                        "ohlc_m15": market_dict.get("ohlc_m15", []),
                        "ohlc_m5": market_dict.get("ohlc_m5", []),
                    }
                )
            ),
        }
    )

    return content


# ---------------------------------------------------------------------------
# JSON parsing
# ---------------------------------------------------------------------------
def _parse_response(raw_text: str) -> Optional[dict]:
    """Extract JSON from Claude's response, handling markdown code blocks."""
    text = raw_text.strip()

    if "```" in text:
        parts = text.split("```")
        for part in parts:
            cleaned = part.strip()
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
            if cleaned.startswith("{"):
                try:
                    return json.loads(cleaned)
                except json.JSONDecodeError:
                    continue

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    return None


# ---------------------------------------------------------------------------
# Tier 0: Fetch fundamentals (Sonnet + web search, once per day per pair)
# ---------------------------------------------------------------------------
async def fetch_fundamentals(symbol: str, profile: dict) -> str:
    """Fetch fundamentals via Sonnet with web search. Cached daily."""
    cached = get_cached_fundamentals(symbol)
    if cached:
        logger.info("Using cached fundamentals for %s", symbol)
        return cached

    if not ANTHROPIC_API_KEY:
        return ""

    base = profile["base_currency"]
    quote = profile["quote_currency"]
    search_queries = ", ".join(f'"{q}"' for q in profile["search_queries"])

    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

    try:
        logger.info("Fetching fundamentals for %s via Sonnet + web search...", symbol)
        response = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1500,
            system=f"You are a forex news analyst. Search for current {base}/{quote} fundamentals and news. Be concise.",
            tools=[
                {
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 5,
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Search for {search_queries}. "
                        f"Summarize in bullet points:\n"
                        f"1. Current {base} drivers (max 3 bullets)\n"
                        f"2. Current {quote} drivers (max 3 bullets)\n"
                        f"3. Key upcoming events in next 24h\n"
                        f"4. Overall fundamental bias for {symbol}\n"
                        f"Keep it under 300 words."
                    ),
                }
            ],
        )

        raw_text = ""
        for block in response.content:
            if hasattr(block, "text") and block.text is not None:
                raw_text += block.text

        if raw_text:
            store_fundamentals(symbol, raw_text)
            logger.info("Fundamentals fetched for %s (%d chars)", symbol, len(raw_text))
        return raw_text

    except Exception as e:
        logger.error("Failed to fetch fundamentals for %s: %s", symbol, e)
        return ""


# ---------------------------------------------------------------------------
# Tier 1: Sonnet screening (cheap, every scan)
# ---------------------------------------------------------------------------
async def screen_charts(
    screenshot_h1: bytes,
    screenshot_m15: bytes,
    screenshot_m5: bytes,
    market_data: MarketData,
    profile: dict,
    fundamentals: Optional[str] = None,
) -> dict:
    """Quick Sonnet screen — is there a setup worth analyzing in detail?
    Returns dict with has_setup, h1_trend, reasoning, market_summary."""
    if not ANTHROPIC_API_KEY:
        return {"has_setup": True, "reasoning": "API key missing, skipping screen"}

    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    symbol = market_data.symbol

    user_content = _build_image_content(screenshot_h1, screenshot_m15, screenshot_m5, market_data)
    user_content.append({"type": "text", "text": "Screen these charts. Is there a valid ICT setup? Reply with JSON only."})

    try:
        logger.info("[%s] Sonnet screening...", symbol)
        response = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=500,
            system=_build_screening_prompt(symbol, profile, fundamentals),
            messages=[{"role": "user", "content": user_content}],
        )

        raw_text = ""
        for block in response.content:
            if hasattr(block, "text") and block.text is not None:
                raw_text += block.text

        parsed = _parse_response(raw_text)
        if parsed:
            has_setup = parsed.get("has_setup", False)
            logger.info("[%s] Sonnet screening result: has_setup=%s — %s",
                        symbol, has_setup, parsed.get("reasoning", ""))
            return parsed

        logger.warning("[%s] Sonnet screening: failed to parse, escalating to Opus", symbol)
        return {"has_setup": True, "reasoning": "Parse failed, escalating"}

    except Exception as e:
        logger.error("[%s] Sonnet screening error: %s — escalating to Opus", symbol, e)
        return {"has_setup": True, "reasoning": f"Screen error: {e}"}


# ---------------------------------------------------------------------------
# Tier 2: Opus full analysis (expensive, only when screening passes)
# ---------------------------------------------------------------------------
async def analyze_charts_full(
    screenshot_h1: bytes,
    screenshot_m15: bytes,
    screenshot_m5: bytes,
    market_data: MarketData,
    profile: dict,
    fundamentals: Optional[str] = None,
) -> AnalysisResult:
    """Full Opus analysis with detailed ICT methodology."""
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not configured")
        return AnalysisResult(market_summary="Error: API key not configured")

    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    symbol = market_data.symbol

    user_content = _build_image_content(screenshot_h1, screenshot_m15, screenshot_m5, market_data)

    # If we have cached fundamentals, no web search needed
    use_web_search = fundamentals is None
    system_prompt = build_system_prompt(symbol, profile, fundamentals)

    if use_web_search:
        user_content.append({
            "type": "text",
            "text": "Analyze the charts and market data above. First use web_search to check fundamentals and news, then provide your analysis as JSON.",
        })
    else:
        user_content.append({
            "type": "text",
            "text": "Analyze the charts and market data above using the pre-loaded fundamentals. Provide your analysis as JSON.",
        })

    tools = []
    if use_web_search:
        tools.append({
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 10,
        })

    try:
        logger.info("[%s] Opus full analysis (web_search=%s)...", symbol, use_web_search)
        response = await client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            tools=tools if tools else anthropic.NOT_GIVEN,
            messages=[{"role": "user", "content": user_content}],
        )

        raw_text = ""
        for block in response.content:
            if hasattr(block, "text") and block.text is not None:
                raw_text += block.text

        logger.info("[%s] Opus response received (%d chars)", symbol, len(raw_text))

        # If this was a web-search call, extract and cache fundamentals for next time
        if use_web_search and raw_text:
            # Store a summary of the response as fundamentals cache
            parsed_for_cache = _parse_response(raw_text)
            if parsed_for_cache:
                events = parsed_for_cache.get("upcoming_events", [])
                bias = parsed_for_cache.get("fundamental_bias", "neutral")
                cache_text = f"Fundamental bias: {bias}\nUpcoming events: {', '.join(events)}"
                store_fundamentals(symbol, cache_text)

        parsed = _parse_response(raw_text)
        if parsed is None:
            logger.warning("[%s] Failed to parse JSON from Opus response", symbol)
            return AnalysisResult(
                symbol=symbol,
                digits=profile["digits"],
                market_summary="Analysis received but JSON parsing failed.",
                raw_response=raw_text,
            )

        setups = []
        for s in parsed.get("setups", []):
            try:
                setups.append(TradeSetup(**s))
            except Exception as e:
                logger.warning("[%s] Failed to parse setup: %s", symbol, e)

        return AnalysisResult(
            symbol=symbol,
            digits=profile["digits"],
            setups=setups,
            h1_trend_analysis=parsed.get("h1_trend_analysis", ""),
            market_summary=parsed.get("market_summary", ""),
            primary_scenario=parsed.get("primary_scenario", ""),
            alternative_scenario=parsed.get("alternative_scenario", ""),
            fundamental_bias=parsed.get("fundamental_bias", "neutral"),
            upcoming_events=parsed.get("upcoming_events", []),
            raw_response=raw_text,
        )

    except anthropic.APIError as e:
        logger.error("[%s] Claude API error: %s", symbol, e)
        return AnalysisResult(symbol=symbol, digits=profile["digits"],
                              market_summary=f"Claude API error: {e}")
    except Exception as e:
        logger.error("[%s] Unexpected error during analysis: %s", symbol, e, exc_info=True)
        return AnalysisResult(symbol=symbol, digits=profile["digits"],
                              market_summary=f"Analysis error: {e}")


# ---------------------------------------------------------------------------
# Main entry point: two-tier analysis pipeline
# ---------------------------------------------------------------------------
async def analyze_charts(
    screenshot_h1: bytes,
    screenshot_m15: bytes,
    screenshot_m5: bytes,
    market_data: MarketData,
) -> AnalysisResult:
    """Two-tier analysis: Sonnet screens → Opus analyzes (if setup found).
    Fundamentals fetched once per day via Sonnet + web search."""
    symbol = market_data.symbol
    profile = get_profile(symbol)

    # Step 1: Fetch fundamentals (cached daily, cheap Sonnet + web search)
    fundamentals = await fetch_fundamentals(symbol, profile)

    # Step 2: Sonnet screening (cheap, every scan, no web search)
    screening = await screen_charts(
        screenshot_h1, screenshot_m15, screenshot_m5,
        market_data, profile, fundamentals,
    )

    if not screening.get("has_setup", False):
        # No setup — return Sonnet's summary without calling Opus
        logger.info("[%s] Sonnet says no setup — skipping Opus ($saved)", symbol)
        return AnalysisResult(
            symbol=symbol,
            digits=profile["digits"],
            h1_trend_analysis=f"H1 trend: {screening.get('h1_trend', 'unknown')}",
            market_summary=screening.get("market_summary", screening.get("reasoning", "No valid setup identified.")),
            primary_scenario=screening.get("reasoning", ""),
        )

    # Step 3: Opus full analysis (expensive, only when Sonnet found something)
    logger.info("[%s] Sonnet found potential setup — escalating to Opus", symbol)
    return await analyze_charts_full(
        screenshot_h1, screenshot_m15, screenshot_m5,
        market_data, profile, fundamentals,
    )

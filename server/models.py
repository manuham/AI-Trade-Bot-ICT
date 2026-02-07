from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class OHLCBar(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class MarketData(BaseModel):
    symbol: str = "GBPJPY"
    session: str = ""
    timestamp: str = ""
    bid: float = 0.0
    ask: float = 0.0
    spread_pips: float = 0.0
    atr_h1: float = 0.0
    atr_m15: float = 0.0
    atr_m5: float = 0.0
    daily_high: float = 0.0
    daily_low: float = 0.0
    daily_range_pips: float = 0.0
    account_balance: float = 0.0
    ohlc_h1: list[OHLCBar] = []
    ohlc_m15: list[OHLCBar] = []
    ohlc_m5: list[OHLCBar] = []


class TradeSetup(BaseModel):
    bias: str
    entry_min: float
    entry_max: float
    stop_loss: float
    sl_pips: float
    tp1: float
    tp1_pips: float
    tp2: float
    tp2_pips: float
    rr_tp1: float
    rr_tp2: float
    confluence: list[str]
    invalidation: str
    timeframe_type: str
    confidence: str
    news_warning: Optional[str] = None


class AnalysisResult(BaseModel):
    setups: list[TradeSetup] = []
    market_summary: str = ""
    primary_scenario: str = ""
    alternative_scenario: str = ""
    fundamental_bias: str = "neutral"
    upcoming_events: list[str] = []
    raw_response: str = ""

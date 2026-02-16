"""Shared mutable state accessed by both main.py and telegram_bot.py.

This module breaks the circular import between main.py and telegram_bot.py
by providing a neutral place for shared data that both modules can import.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import MarketData

# Latest market data per symbol — set by main.py, read by telegram_bot.py
last_market_data: dict[str, MarketData] = {}

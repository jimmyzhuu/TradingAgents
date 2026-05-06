from __future__ import annotations

from functools import lru_cache

import exchange_calendars as xcals
import pandas as pd

from tradingagents.markets.profiles import get_market_profile


@lru_cache(maxsize=None)
def get_market_calendar(market: str):
    profile = get_market_profile(market)
    return xcals.get_calendar(profile.calendar_code)


def is_trading_session(market: str, session_date: str) -> bool:
    calendar = get_market_calendar(market)
    return calendar.is_session(pd.Timestamp(session_date))

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class MarketProfile:
    market_id: str
    display_name: str
    timezone: str
    currency: str
    benchmark_symbol: str
    calendar_code: str
    default_output_language: str
    lot_size: int
    t_plus_one: bool
    supports_short: bool


MARKET_PROFILES = {
    "us_equity": MarketProfile(
        market_id="us_equity",
        display_name="US Equity",
        timezone="America/New_York",
        currency="USD",
        benchmark_symbol="SPY",
        calendar_code="XNYS",
        default_output_language="English",
        lot_size=1,
        t_plus_one=False,
        supports_short=True,
    ),
    "hk_equity": MarketProfile(
        market_id="hk_equity",
        display_name="Hong Kong Equity",
        timezone="Asia/Hong_Kong",
        currency="HKD",
        benchmark_symbol="^HSI",
        calendar_code="XHKG",
        default_output_language="English",
        lot_size=100,
        t_plus_one=False,
        supports_short=False,
    ),
    "cn_a": MarketProfile(
        market_id="cn_a",
        display_name="China A-Share",
        timezone="Asia/Shanghai",
        currency="CNY",
        benchmark_symbol="000300.SH",
        calendar_code="XSHG",
        default_output_language="Chinese",
        lot_size=100,
        t_plus_one=True,
        supports_short=False,
    ),
}


def get_market_profile(market: str) -> MarketProfile:
    try:
        return MARKET_PROFILES[market]
    except KeyError as exc:
        raise ValueError(f"Unsupported market: {market}") from exc


def canonicalize_ticker(ticker: str, market: str) -> str:
    get_market_profile(market)
    cleaned = ticker.strip().upper()
    if market != "cn_a":
        return cleaned

    code = cleaned
    if "." in cleaned:
        parts = cleaned.split(".")
        if len(parts) != 2:
            raise ValueError(f"Expected a mainland ticker in CODE.SUFFIX form, got {ticker!r}")
        code, suffix = parts
        if not re.fullmatch(r"\d{6}", code):
            raise ValueError(f"Expected a 6-digit mainland security code, got {ticker!r}")
        expected_suffix = _infer_cn_a_suffix(code, ticker)
        if suffix != expected_suffix:
            raise ValueError(
                f"Expected mainland code {ticker!r} to use .{expected_suffix} suffix"
            )
        return f"{code}.{suffix}"

    if not re.fullmatch(r"\d{6}", code):
        raise ValueError(f"Expected a 6-digit mainland security code, got {ticker!r}")
    return f"{code}.{_infer_cn_a_suffix(code, ticker)}"


def _infer_cn_a_suffix(code: str, original_ticker: str) -> str:
    if code.startswith(("6", "5")):
        return "SH"
    if code.startswith(("0", "1", "2", "3")):
        return "SZ"
    if code.startswith(("4", "8")) or code.startswith("92"):
        return "BJ"
    raise ValueError(f"Could not infer exchange suffix for mainland code {original_ticker!r}")

from __future__ import annotations

from datetime import datetime
import os

import akshare as ak
import pandas as pd

from tradingagents.markets.profiles import canonicalize_ticker

from .config import get_config
from .utils import safe_ticker_component


_SUPPORTED_SH_PREFIXES = ("600", "601", "603", "605", "688")
_SUPPORTED_SZ_PREFIXES = ("000", "001", "002", "003", "300")


def _canonicalize_supported_symbol(symbol: str) -> str:
    canonical = canonicalize_ticker(symbol, market="cn_a")
    code, suffix = canonical.split(".")

    if suffix == "SH" and code.startswith(_SUPPORTED_SH_PREFIXES):
        return canonical
    if suffix == "SZ" and code.startswith(_SUPPORTED_SZ_PREFIXES):
        return canonical
    if suffix == "BJ":
        return canonical

    raise ValueError(
        f"Unsupported cn_a instrument {symbol!r}. Only A-share equities on SH/SZ/BJ are supported"
    )


def _plain_code(symbol: str) -> str:
    return symbol.split(".")[0]


def _normalize_hist_frame(df: pd.DataFrame) -> pd.DataFrame:
    renamed = df.rename(
        columns={
            "日期": "Date",
            "开盘": "Open",
            "收盘": "Close",
            "最高": "High",
            "最低": "Low",
            "成交量": "Volume",
            "成交额": "Amount",
        }
    )[["Date", "Open", "High", "Low", "Close", "Volume", "Amount"]]
    renamed["Date"] = pd.to_datetime(renamed["Date"])
    return renamed


def get_stock(symbol: str, start_date: str, end_date: str, adjust: str = "qfq") -> str:
    canonical_symbol = _canonicalize_supported_symbol(symbol)
    normalized = fetch_ohlcv(
        canonical_symbol,
        start_date=start_date,
        end_date=end_date,
        adjust=adjust,
    )
    header = f"# Stock data for {canonical_symbol} from {start_date} to {end_date}\n"
    header += f"# Total records: {len(normalized)}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    return header + normalized.to_csv(index=False)


def fetch_ohlcv(
    symbol: str,
    start_date: str,
    end_date: str,
    adjust: str = "qfq",
    cache_dir: str | None = None,
) -> pd.DataFrame:
    canonical_symbol = _canonicalize_supported_symbol(symbol)
    config = get_config()
    resolved_cache_dir = cache_dir or config["data_cache_dir"]
    os.makedirs(resolved_cache_dir, exist_ok=True)

    safe_symbol = safe_ticker_component(canonical_symbol)
    data_file = os.path.join(
        resolved_cache_dir,
        f"{safe_symbol}-AShare-data-{adjust}-{start_date}-{end_date}.csv",
    )

    if os.path.exists(data_file):
        return pd.read_csv(data_file, parse_dates=["Date"], encoding="utf-8")

    df = ak.stock_zh_a_hist(
        symbol=_plain_code(canonical_symbol),
        period="daily",
        start_date=start_date.replace("-", ""),
        end_date=end_date.replace("-", ""),
        adjust=adjust,
    )
    normalized = _normalize_hist_frame(df)
    normalized.to_csv(data_file, index=False, encoding="utf-8")
    return normalized

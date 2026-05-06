from __future__ import annotations

from datetime import datetime

import akshare as ak
import pandas as pd


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
    df = ak.stock_zh_a_hist(
        symbol=_plain_code(symbol),
        period="daily",
        start_date=start_date.replace("-", ""),
        end_date=end_date.replace("-", ""),
        adjust=adjust,
    )
    normalized = _normalize_hist_frame(df)
    header = f"# Stock data for {symbol} from {start_date} to {end_date}\n"
    header += f"# Total records: {len(normalized)}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    return header + normalized.to_csv(index=False)


def fetch_ohlcv(symbol: str, start_date: str, end_date: str, adjust: str = "qfq") -> pd.DataFrame:
    df = ak.stock_zh_a_hist(
        symbol=_plain_code(symbol),
        period="daily",
        start_date=start_date.replace("-", ""),
        end_date=end_date.replace("-", ""),
        adjust=adjust,
    )
    return _normalize_hist_frame(df)

from __future__ import annotations

from datetime import datetime
from typing import Dict

import akshare as ak
import pandas as pd

from tradingagents.markets.profiles import canonicalize_ticker


STATEMENT_LABELS: Dict[str, str] = {
    "annual": "年报",
    "quarterly": "季报",
}


def _plain_code(ticker: str) -> str:
    normalized = canonicalize_ticker(ticker, market="cn_a")
    return normalized.split(".")[0]


def _format_frame(title: str, ticker: str, frame: pd.DataFrame) -> str:
    if frame is None or frame.empty:
        return f"No {title.lower()} data found for {ticker}"
    header = f"# {title} for {ticker}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    return header + frame.to_markdown(index=False)


def _statement_type(freq: str) -> str:
    return STATEMENT_LABELS.get((freq or "quarterly").lower(), "季报")


def get_a_share_fundamentals(ticker: str, curr_date: str) -> str:
    del curr_date
    code = _plain_code(ticker)
    profile = ak.stock_individual_info_em(symbol=code)
    return _format_frame("Company Fundamentals", ticker, profile)


def get_a_share_balance_sheet(
    ticker: str,
    freq: str = "quarterly",
    curr_date: str = None,
) -> str:
    del curr_date
    code = _plain_code(ticker)
    frame = ak.stock_financial_report_sina(stock=code, symbol="资产负债表")
    report_type = _statement_type(freq)
    if "报告期类型" in frame.columns:
        filtered = frame[frame["报告期类型"] == report_type]
        if not filtered.empty:
            frame = filtered
    return _format_frame(f"Balance Sheet ({freq})", ticker, frame)


def get_a_share_cashflow(
    ticker: str,
    freq: str = "quarterly",
    curr_date: str = None,
) -> str:
    del curr_date
    code = _plain_code(ticker)
    frame = ak.stock_financial_report_sina(stock=code, symbol="现金流量表")
    report_type = _statement_type(freq)
    if "报告期类型" in frame.columns:
        filtered = frame[frame["报告期类型"] == report_type]
        if not filtered.empty:
            frame = filtered
    return _format_frame(f"Cash Flow ({freq})", ticker, frame)


def get_a_share_income_statement(
    ticker: str,
    freq: str = "quarterly",
    curr_date: str = None,
) -> str:
    del curr_date
    code = _plain_code(ticker)
    frame = ak.stock_financial_report_sina(stock=code, symbol="利润表")
    report_type = _statement_type(freq)
    if "报告期类型" in frame.columns:
        filtered = frame[frame["报告期类型"] == report_type]
        if not filtered.empty:
            frame = filtered
    return _format_frame(f"Income Statement ({freq})", ticker, frame)


def get_fundamentals(ticker: str, curr_date: str = None) -> str:
    return get_a_share_fundamentals(ticker, curr_date)


def get_balance_sheet(ticker: str, freq: str = "quarterly", curr_date: str = None) -> str:
    return get_a_share_balance_sheet(ticker, freq, curr_date)


def get_cashflow(ticker: str, freq: str = "quarterly", curr_date: str = None) -> str:
    return get_a_share_cashflow(ticker, freq, curr_date)


def get_income_statement(ticker: str, freq: str = "quarterly", curr_date: str = None) -> str:
    return get_a_share_income_statement(ticker, freq, curr_date)

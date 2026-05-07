from __future__ import annotations

import akshare as ak
import pandas as pd

from tradingagents.markets.calendars import get_market_calendar
from tradingagents.markets.profiles import canonicalize_ticker


ANNOUNCEMENT_CATEGORIES = ("财务报告", "重大事项", "风险提示", "持股变动")


def _plain_code(ticker: str) -> str:
    normalized = canonicalize_ticker(ticker, market="cn_a")
    return normalized.split(".")[0]


def _format_frame(title: str, frame: pd.DataFrame) -> str:
    if frame is None or frame.empty:
        return "No data available."
    return f"{title}\n\n{frame.to_markdown(index=False)}"


def _date_range(start_date: str, end_date: str) -> list[str]:
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    if end < start:
        return []
    return [
        ts.strftime("%Y-%m-%d")
        for ts in pd.date_range(start=start, end=end, freq="D")
    ]


def trading_sessions(market: str, start_date: str, end_date: str):
    calendar = get_market_calendar(market)
    return calendar.sessions_in_range(pd.Timestamp(start_date), pd.Timestamp(end_date))


def get_a_share_news(ticker: str, start_date: str, end_date: str) -> str:
    code = _plain_code(ticker)
    frame = ak.stock_news_em(symbol=code)
    if frame is None or frame.empty:
        return "No data available."

    published_col = "发布时间" if "发布时间" in frame.columns else frame.columns[0]
    published = pd.to_datetime(frame[published_col], errors="coerce")
    mask = published.between(pd.Timestamp(start_date), pd.Timestamp(end_date) + pd.Timedelta(days=1), inclusive="left")
    filtered = frame.loc[mask].copy()
    return _format_frame(f"## {ticker} News, from {start_date} to {end_date}:", filtered)


def get_a_share_global_news(curr_date: str, look_back_days: int = 7, limit: int = 5) -> str:
    frame = ak.stock_news_main_cx()
    if frame is None or frame.empty:
        return "No data available."

    published_col = "发布时间" if "发布时间" in frame.columns else frame.columns[0]
    published = pd.to_datetime(frame[published_col], errors="coerce")
    lower = pd.Timestamp(curr_date) - pd.Timedelta(days=max(look_back_days, 0))
    upper = pd.Timestamp(curr_date) + pd.Timedelta(days=1)
    filtered = frame.loc[published.between(lower, upper, inclusive="left")].copy()
    if limit:
        filtered = filtered.head(limit)
    lower_str = lower.strftime("%Y-%m-%d")
    return _format_frame(f"## China Market News, from {lower_str} to {curr_date}:", filtered)


def get_a_share_company_announcements(ticker: str, start_date: str, end_date: str) -> str:
    code = _plain_code(ticker)
    frames = []

    for session in trading_sessions("cn_a", start_date, end_date):
        query_date = pd.Timestamp(session).strftime("%Y%m%d")
        for category in ANNOUNCEMENT_CATEGORIES:
            frame = ak.stock_notice_report(symbol=category, date=query_date)
            if frame is None or frame.empty or "代码" not in frame.columns:
                continue
            matched = frame.loc[frame["代码"].astype(str).str.zfill(6) == code].copy()
            if not matched.empty:
                matched.insert(0, "公告类别", category)
                frames.append(matched)

    if not frames:
        return f"No announcements found for {ticker} between {start_date} and {end_date}"

    combined = pd.concat(frames, ignore_index=True).drop_duplicates()
    return _format_frame(f"## {ticker} Announcements, from {start_date} to {end_date}:", combined)


def get_news(ticker: str, start_date: str, end_date: str) -> str:
    return get_a_share_news(ticker, start_date, end_date)


def get_global_news(curr_date: str, look_back_days: int = 7, limit: int = 5) -> str:
    return get_a_share_global_news(curr_date, look_back_days, limit)


def get_company_announcements(ticker: str, start_date: str, end_date: str) -> str:
    return get_a_share_company_announcements(ticker, start_date, end_date)

# A-Share Market Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a China A-share compatible TradingAgents workflow that can analyze `SH`/`SZ`/`BJ` instruments with mainland calendars, benchmarks, Chinese data vendors, announcement-aware research, and A-share rule-aware recommendations.

**Architecture:** Keep the existing LangGraph agent topology and tool surface as stable as possible, then add a market-profile layer plus a new `a_share` vendor behind the current dataflow router. Thread market metadata from CLI/config into ticker normalization, calendar handling, benchmark-aware reflection, vendor selection, and prompt instructions so the framework can support A shares without forking the graph.

**Tech Stack:** Python 3.10+, LangGraph, pandas, requests, stockstats, AkShare, exchange_calendars, pytest

---

### Task 1: Add Market Profiles And Canonical A-Share Ticker Handling

**Files:**
- Create: `tradingagents/markets/__init__.py`
- Create: `tradingagents/markets/profiles.py`
- Modify: `cli/utils.py`
- Test: `tests/test_market_profiles.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_market_profiles.py
import unittest

import pytest

from cli.utils import normalize_ticker_symbol
from tradingagents.markets.profiles import canonicalize_ticker, get_market_profile


@pytest.mark.unit
class MarketProfileTests(unittest.TestCase):
    def test_canonicalize_mainland_a_share_codes(self):
        self.assertEqual(canonicalize_ticker("600519", "cn_a"), "600519.SH")
        self.assertEqual(canonicalize_ticker("000001", "cn_a"), "000001.SZ")
        self.assertEqual(canonicalize_ticker("430047", "cn_a"), "430047.BJ")

    def test_cn_a_profile_contains_expected_defaults(self):
        profile = get_market_profile("cn_a")
        self.assertEqual(profile.benchmark_symbol, "000300.SH")
        self.assertEqual(profile.calendar_code, "XSHG")
        self.assertEqual(profile.currency, "CNY")
        self.assertTrue(profile.t_plus_one)

    def test_normalize_ticker_symbol_uses_market_rules(self):
        self.assertEqual(normalize_ticker_symbol(" 600519 ", market="cn_a"), "600519.SH")
        self.assertEqual(normalize_ticker_symbol(" 0700.hk ", market="hk_equity"), "0700.HK")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_market_profiles.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tradingagents.markets'` and `normalize_ticker_symbol() got an unexpected keyword argument 'market'`.

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/markets/profiles.py
from __future__ import annotations

from dataclasses import dataclass


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
    cleaned = ticker.strip().upper()
    if market != "cn_a":
        return cleaned
    if "." in cleaned:
        return cleaned
    if len(cleaned) != 6 or not cleaned.isdigit():
        raise ValueError(f"Expected a 6-digit mainland security code, got {ticker!r}")
    if cleaned.startswith(("6", "5")):
        return f"{cleaned}.SH"
    if cleaned.startswith(("0", "1", "2", "3")):
        return f"{cleaned}.SZ"
    if cleaned.startswith(("4", "8")) or cleaned.startswith("92"):
        return f"{cleaned}.BJ"
    raise ValueError(f"Could not infer exchange suffix for mainland code {ticker!r}")
```

```python
# tradingagents/markets/__init__.py
from .profiles import MarketProfile, MARKET_PROFILES, canonicalize_ticker, get_market_profile

__all__ = [
    "MarketProfile",
    "MARKET_PROFILES",
    "canonicalize_ticker",
    "get_market_profile",
]
```

```python
# cli/utils.py
from tradingagents.markets.profiles import canonicalize_ticker


def normalize_ticker_symbol(ticker: str, market: str = "us_equity") -> str:
    """Normalize ticker input while preserving exchange suffixes."""
    return canonicalize_ticker(ticker, market)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_market_profiles.py -v`
Expected: PASS with 3 passing tests.

- [ ] **Step 5: Commit**

```bash
git add tests/test_market_profiles.py tradingagents/markets/__init__.py tradingagents/markets/profiles.py cli/utils.py
git commit -m "feat: add market profiles and a-share ticker normalization"
```

### Task 2: Thread Market Selection Through Config And CLI

**Files:**
- Modify: `tradingagents/default_config.py`
- Modify: `cli/utils.py`
- Modify: `cli/main.py`
- Modify: `main.py`
- Modify: `tests/test_ticker_symbol_handling.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ticker_symbol_handling.py
import unittest

import pytest

from cli.utils import (
    get_default_output_language,
    get_ticker_input_examples,
    normalize_ticker_symbol,
)
from tradingagents.agents.utils.agent_utils import build_instrument_context
from tradingagents.default_config import DEFAULT_CONFIG


@pytest.mark.unit
class TickerSymbolHandlingTests(unittest.TestCase):
    def test_normalize_ticker_symbol_preserves_exchange_suffix(self):
        self.assertEqual(normalize_ticker_symbol(" cnc.to ", market="us_equity"), "CNC.TO")

    def test_build_instrument_context_mentions_exact_symbol(self):
        context = build_instrument_context("7203.T")
        self.assertIn("7203.T", context)
        self.assertIn("exchange suffix", context)

    def test_cn_a_examples_and_default_language(self):
        self.assertEqual(
            get_ticker_input_examples("cn_a"),
            "Examples: 600519.SH, 000001.SZ, 300750.SZ, 430047.BJ",
        )
        self.assertEqual(get_default_output_language("cn_a"), "Chinese")

    def test_default_config_keeps_backward_compatible_market_defaults(self):
        self.assertEqual(DEFAULT_CONFIG["market"], "us_equity")
        self.assertEqual(DEFAULT_CONFIG["benchmark_symbol"], "SPY")
        self.assertEqual(DEFAULT_CONFIG["price_adjustment"], "qfq")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ticker_symbol_handling.py -v`
Expected: FAIL with missing helper functions and missing config keys.

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/default_config.py
DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", os.path.join(_TRADINGAGENTS_HOME, "logs")),
    "data_cache_dir": os.getenv("TRADINGAGENTS_CACHE_DIR", os.path.join(_TRADINGAGENTS_HOME, "cache")),
    "memory_log_path": os.getenv("TRADINGAGENTS_MEMORY_LOG_PATH", os.path.join(_TRADINGAGENTS_HOME, "memory", "trading_memory.md")),
    "memory_log_max_entries": None,
    "market": "us_equity",
    "benchmark_symbol": "SPY",
    "calendar_code": "XNYS",
    "price_adjustment": "qfq",
    "llm_provider": "openai",
    "deep_think_llm": "gpt-5.4",
    "quick_think_llm": "gpt-5.4-mini",
    "backend_url": None,
    "google_thinking_level": None,
    "openai_reasoning_effort": None,
    "anthropic_effort": None,
    "checkpoint_enabled": False,
    "output_language": "English",
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    "data_vendors": {
        "core_stock_apis": "yfinance",
        "technical_indicators": "yfinance",
        "fundamental_data": "yfinance",
        "news_data": "yfinance",
    },
    "tool_vendors": {},
}
```

```python
# cli/utils.py
def get_ticker_input_examples(market: str) -> str:
    examples = {
        "us_equity": "Examples: SPY, NVDA, BRK.B, CNC.TO",
        "hk_equity": "Examples: 0700.HK, 9988.HK, 2318.HK",
        "cn_a": "Examples: 600519.SH, 000001.SZ, 300750.SZ, 430047.BJ",
    }
    return examples.get(market, examples["us_equity"])


def get_default_output_language(market: str) -> str:
    return "Chinese" if market == "cn_a" else "English"
```

```python
# cli/main.py
def collect_user_selections():
    console.print(
        create_question_box(
            "Step 1: Market",
            "Select the market to analyze",
            "US Equity",
        )
    )
    selected_market = select_market()

    console.print(
        create_question_box(
            "Step 2: Ticker Symbol",
            f"Enter the exact ticker symbol to analyze ({get_ticker_input_examples(selected_market)})",
        )
    )
    selected_ticker = normalize_ticker_symbol(get_ticker(), market=selected_market)

    default_output_language = get_default_output_language(selected_market)
    output_language = ask_output_language(default=default_output_language)

    return {
        "market": selected_market,
        "ticker": selected_ticker,
        "output_language": output_language,
        # keep existing fields unchanged below this line
    }
```

```python
# main.py
config = DEFAULT_CONFIG.copy()
config["market"] = "cn_a"
config["benchmark_symbol"] = "000300.SH"
config["calendar_code"] = "XSHG"
config["output_language"] = "Chinese"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_ticker_symbol_handling.py -v`
Expected: PASS with 4 passing tests.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/default_config.py cli/utils.py cli/main.py main.py tests/test_ticker_symbol_handling.py
git commit -m "feat: add market-aware config and cli defaults"
```

### Task 3: Add Mainland Trading Calendar Utilities And Benchmark-Aware Reflection

**Files:**
- Modify: `pyproject.toml`
- Create: `tradingagents/markets/calendars.py`
- Modify: `tradingagents/graph/reflection.py`
- Modify: `tradingagents/graph/trading_graph.py`
- Test: `tests/test_a_share_calendar.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_a_share_calendar.py
import unittest

import pytest

from tradingagents.graph.reflection import Reflector
from tradingagents.markets.calendars import get_market_calendar, is_trading_session


class DummyLLM:
    def __init__(self):
        self.messages = None

    def invoke(self, messages):
        self.messages = messages
        return type("Resp", (), {"content": "reflection"})()


@pytest.mark.unit
class AShareCalendarTests(unittest.TestCase):
    def test_cn_a_market_uses_shanghai_calendar(self):
        calendar = get_market_calendar("cn_a")
        self.assertEqual(calendar.name, "XSHG")

    def test_is_trading_session_rejects_public_holiday(self):
        self.assertFalse(is_trading_session("cn_a", "2026-05-01"))

    def test_reflector_uses_configured_benchmark_label(self):
        llm = DummyLLM()
        reflector = Reflector(llm, benchmark_label="000300.SH")
        reflector.reflect_on_final_decision("**Rating**: Buy", 0.03, 0.01)
        self.assertIn("Alpha vs 000300.SH", llm.messages[1][1])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_a_share_calendar.py -v`
Expected: FAIL with missing `tradingagents.markets.calendars` and `Reflector.__init__()` arity mismatch.

- [ ] **Step 3: Write minimal implementation**

```toml
# pyproject.toml
dependencies = [
    "langchain-core>=0.3.81",
    "backtrader>=1.9.78.123",
    "langchain-anthropic>=0.3.15",
    "langchain-experimental>=0.3.4",
    "langchain-google-genai>=4.0.0",
    "langchain-openai>=0.3.23",
    "langgraph>=0.4.8",
    "langgraph-checkpoint-sqlite>=2.0.0",
    "pandas>=2.3.0",
    "parsel>=1.10.0",
    "pytz>=2025.2",
    "questionary>=2.1.0",
    "redis>=6.2.0",
    "requests>=2.32.4",
    "rich>=14.0.0",
    "typer>=0.21.0",
    "setuptools>=80.9.0",
    "stockstats>=0.6.5",
    "tqdm>=4.67.1",
    "typing-extensions>=4.14.0",
    "yfinance>=0.2.63",
    "exchange_calendars>=4.13.1",
]
```

```python
# tradingagents/markets/calendars.py
from __future__ import annotations

from functools import lru_cache

import exchange_calendars as xcals
import pandas as pd

from tradingagents.markets.profiles import get_market_profile


@lru_cache(maxsize=None)
def get_market_calendar(market: str):
    profile = get_market_profile(market)
    return xcals.get_calendar(profile.calendar_code)


def is_trading_session(market: str, date_str: str) -> bool:
    calendar = get_market_calendar(market)
    session = pd.Timestamp(date_str)
    return calendar.is_session(session)


def trading_sessions(market: str, start_date: str, end_date: str) -> list[pd.Timestamp]:
    calendar = get_market_calendar(market)
    sessions = calendar.sessions_in_range(pd.Timestamp(start_date), pd.Timestamp(end_date))
    return [pd.Timestamp(session).tz_localize(None) for session in sessions]
```

```python
# tradingagents/graph/reflection.py
class Reflector:
    """Handles reflection on trading decisions."""

    def __init__(self, quick_thinking_llm: Any, benchmark_label: str = "SPY"):
        self.quick_thinking_llm = quick_thinking_llm
        self.benchmark_label = benchmark_label
        self.log_reflection_prompt = self._get_log_reflection_prompt()

    def reflect_on_final_decision(
        self,
        final_decision: str,
        raw_return: float,
        alpha_return: float,
    ) -> str:
        messages = [
            ("system", self.log_reflection_prompt),
            (
                "human",
                (
                    f"Raw return: {raw_return:+.1%}\n"
                    f"Alpha vs {self.benchmark_label}: {alpha_return:+.1%}\n\n"
                    f"Final Decision:\n{final_decision}"
                ),
            ),
        ]
        return self.quick_thinking_llm.invoke(messages).content
```

```python
# tradingagents/graph/trading_graph.py
self.reflector = Reflector(
    self.quick_thinking_llm,
    benchmark_label=self.config.get("benchmark_symbol", "SPY"),
)

benchmark = self.config.get("benchmark_symbol", "SPY")
benchmark_data = yf.Ticker(benchmark).history(start=trade_date, end=end_str)
if len(stock) < 2 or len(benchmark_data) < 2:
    return None, None, None
actual_days = min(holding_days, len(stock) - 1, len(benchmark_data) - 1)
benchmark_ret = float(
    (benchmark_data["Close"].iloc[actual_days] - benchmark_data["Close"].iloc[0])
    / benchmark_data["Close"].iloc[0]
)
alpha = raw - benchmark_ret
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_a_share_calendar.py -v`
Expected: PASS with 3 passing tests.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml tradingagents/markets/calendars.py tradingagents/graph/reflection.py tradingagents/graph/trading_graph.py tests/test_a_share_calendar.py
git commit -m "feat: add mainland calendar utilities and benchmark-aware reflection"
```

### Task 4: Add A-Share OHLCV Vendor And Indicator Support

**Files:**
- Modify: `pyproject.toml`
- Create: `tradingagents/dataflows/a_share_market.py`
- Modify: `tradingagents/dataflows/interface.py`
- Modify: `tradingagents/dataflows/stockstats_utils.py`
- Modify: `tradingagents/dataflows/y_finance.py`
- Test: `tests/test_a_share_dataflows.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_a_share_dataflows.py
import unittest
from unittest.mock import patch

import pandas as pd
import pytest

from tradingagents.dataflows.config import set_config
from tradingagents.dataflows.interface import route_to_vendor
from tradingagents.dataflows.stockstats_utils import load_ohlcv


def _ashare_hist_df():
    return pd.DataFrame(
        {
            "日期": ["2026-01-02", "2026-01-05"],
            "开盘": [100.0, 101.0],
            "收盘": [101.0, 102.0],
            "最高": [102.0, 103.0],
            "最低": [99.0, 100.0],
            "成交量": [100000, 110000],
            "成交额": [10000000, 11200000],
        }
    )


@pytest.mark.unit
class AShareMarketDataTests(unittest.TestCase):
    def setUp(self):
        set_config(
            {
                "market": "cn_a",
                "price_adjustment": "qfq",
                "data_vendors": {
                    "core_stock_apis": "a_share",
                    "technical_indicators": "a_share",
                    "fundamental_data": "yfinance",
                    "news_data": "yfinance",
                },
            }
        )

    @patch("tradingagents.dataflows.a_share_market.ak.stock_zh_a_hist")
    def test_get_stock_data_routes_to_a_share_vendor(self, mock_hist):
        mock_hist.return_value = _ashare_hist_df()
        text = route_to_vendor("get_stock_data", "600519.SH", "2026-01-01", "2026-01-10")
        self.assertIn("# Stock data for 600519.SH", text)
        self.assertIn("2026-01-02", text)

    @patch("tradingagents.dataflows.a_share_market.ak.stock_zh_a_hist")
    def test_load_ohlcv_uses_a_share_vendor_when_market_is_cn_a(self, mock_hist):
        mock_hist.return_value = _ashare_hist_df()
        df = load_ohlcv("600519.SH", "2026-01-10", market="cn_a")
        self.assertEqual(list(df.columns), ["Date", "Open", "High", "Low", "Close", "Volume", "Amount"])
        self.assertEqual(len(df), 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_a_share_dataflows.py::AShareMarketDataTests -v`
Expected: FAIL with missing `a_share` vendor route and `load_ohlcv()` missing `market`.

- [ ] **Step 3: Write minimal implementation**

```toml
# pyproject.toml
dependencies = [
    # keep existing entries unchanged
    "akshare>=1.18.40",
]
```

```python
# tradingagents/dataflows/a_share_market.py
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
```

```python
# tradingagents/dataflows/interface.py
from .a_share_market import get_stock as get_a_share_stock

VENDOR_LIST = [
    "yfinance",
    "alpha_vantage",
    "a_share",
]

VENDOR_METHODS["get_stock_data"]["a_share"] = get_a_share_stock
VENDOR_METHODS["get_indicators"]["a_share"] = get_stock_stats_indicators_window
```

```python
# tradingagents/dataflows/stockstats_utils.py
from .a_share_market import fetch_ohlcv as fetch_ohlcv_cn_a


def load_ohlcv(symbol: str, curr_date: str, market: str | None = None) -> pd.DataFrame:
    config = get_config()
    selected_market = market or config.get("market", "us_equity")
    curr_date_dt = pd.to_datetime(curr_date)

    if selected_market == "cn_a":
        start_date = (curr_date_dt - pd.DateOffset(years=5)).strftime("%Y-%m-%d")
        end_date = curr_date_dt.strftime("%Y-%m-%d")
        data = fetch_ohlcv_cn_a(
            symbol,
            start_date=start_date,
            end_date=end_date,
            adjust=config.get("price_adjustment", "qfq"),
        )
        return data[data["Date"] <= curr_date_dt]

    # keep the existing yfinance branch unchanged below this point
```

```python
# tradingagents/dataflows/y_finance.py
indicator_data = _get_stock_stats_bulk(
    symbol,
    indicator,
    curr_date,
)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_a_share_dataflows.py::AShareMarketDataTests -v`
Expected: PASS with 2 passing tests.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml tradingagents/dataflows/a_share_market.py tradingagents/dataflows/interface.py tradingagents/dataflows/stockstats_utils.py tradingagents/dataflows/y_finance.py tests/test_a_share_dataflows.py
git commit -m "feat: add a-share ohlcv vendor and indicator support"
```

### Task 5: Add A-Share Fundamentals, News, And Announcement Retrieval

**Files:**
- Create: `tradingagents/dataflows/a_share_fundamentals.py`
- Create: `tradingagents/dataflows/a_share_news.py`
- Modify: `tradingagents/dataflows/interface.py`
- Modify: `tradingagents/agents/utils/news_data_tools.py`
- Modify: `tradingagents/agents/utils/agent_utils.py`
- Modify: `tradingagents/graph/trading_graph.py`
- Modify: `tradingagents/agents/analysts/news_analyst.py`
- Modify: `tradingagents/agents/analysts/social_media_analyst.py`
- Modify: `tradingagents/agents/analysts/fundamentals_analyst.py`
- Test: `tests/test_a_share_research_data.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_a_share_research_data.py
import unittest
from unittest.mock import patch

import pandas as pd
import pytest

from tradingagents.dataflows.config import set_config
from tradingagents.dataflows.interface import route_to_vendor


@pytest.mark.unit
class AShareResearchDataTests(unittest.TestCase):
    def setUp(self):
        set_config(
            {
                "market": "cn_a",
                "data_vendors": {
                    "core_stock_apis": "a_share",
                    "technical_indicators": "a_share",
                    "fundamental_data": "a_share",
                    "news_data": "a_share",
                },
            }
        )

    @patch("tradingagents.dataflows.a_share_news.ak.stock_news_em")
    def test_company_news_routes_to_a_share_vendor(self, mock_news):
        mock_news.return_value = pd.DataFrame(
            {
                "新闻标题": ["贵州茅台渠道反馈回暖"],
                "新闻内容": ["春节动销数据改善。"],
                "发布时间": ["2026-01-05 09:30:00"],
                "文章来源": ["东方财富"],
                "新闻链接": ["https://example.com/news"],
            }
        )
        text = route_to_vendor("get_news", "600519.SH", "2026-01-01", "2026-01-10")
        self.assertIn("贵州茅台渠道反馈回暖", text)

    @patch("tradingagents.dataflows.a_share_news.ak.stock_notice_report")
    def test_company_announcements_filter_by_code(self, mock_notice):
        mock_notice.return_value = pd.DataFrame(
            {
                "代码": ["600519", "000001"],
                "名称": ["贵州茅台", "平安银行"],
                "公告标题": ["贵州茅台2025年年度报告", "平安银行公告"],
                "公告类型": ["财务报告", "财务报告"],
                "公告日期": ["2026-03-28", "2026-03-28"],
                "网址": ["https://example.com/moutai", "https://example.com/pab"],
            }
        )
        text = route_to_vendor("get_company_announcements", "600519.SH", "2026-03-28", "2026-03-28")
        self.assertIn("贵州茅台2025年年度报告", text)
        self.assertNotIn("平安银行公告", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_a_share_research_data.py -v`
Expected: FAIL with unsupported `a_share` mappings for fundamentals/news and missing `get_company_announcements`.

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/dataflows/a_share_fundamentals.py
from __future__ import annotations

import akshare as ak


def _plain_code(symbol: str) -> str:
    return symbol.split(".")[0]


def get_fundamentals(ticker: str, curr_date: str | None = None) -> str:
    code = _plain_code(ticker)
    abstract_df = ak.stock_financial_abstract(symbol=code)
    indicator_df = ak.stock_financial_analysis_indicator(symbol=code)
    return (
        f"# Company Fundamentals for {ticker}\n\n"
        "## Financial Abstract\n"
        f"{abstract_df.to_markdown(index=False)}\n\n"
        "## Analysis Indicators\n"
        f"{indicator_df.head(20).to_markdown(index=False)}"
    )


def get_balance_sheet(ticker: str, freq: str = "quarterly", curr_date: str | None = None) -> str:
    code = _plain_code(ticker)
    df = ak.stock_financial_report_sina(stock=code, symbol="资产负债表")
    return f"# Balance Sheet data for {ticker} ({freq})\n\n{df.to_markdown(index=False)}"


def get_cashflow(ticker: str, freq: str = "quarterly", curr_date: str | None = None) -> str:
    code = _plain_code(ticker)
    df = ak.stock_financial_report_sina(stock=code, symbol="现金流量表")
    return f"# Cash Flow data for {ticker} ({freq})\n\n{df.to_markdown(index=False)}"


def get_income_statement(ticker: str, freq: str = "quarterly", curr_date: str | None = None) -> str:
    code = _plain_code(ticker)
    df = ak.stock_financial_report_sina(stock=code, symbol="利润表")
    return f"# Income Statement data for {ticker} ({freq})\n\n{df.to_markdown(index=False)}"
```

```python
# tradingagents/dataflows/a_share_news.py
from __future__ import annotations

import akshare as ak

from tradingagents.markets.calendars import trading_sessions


def _plain_code(symbol: str) -> str:
    return symbol.split(".")[0]


def get_news(ticker: str, start_date: str, end_date: str) -> str:
    df = ak.stock_news_em(symbol=_plain_code(ticker))
    filtered = df[
        (df["发布时间"] >= start_date)
        & (df["发布时间"] <= f"{end_date} 23:59:59")
    ]
    return f"## {ticker} News, from {start_date} to {end_date}:\n\n{filtered.to_markdown(index=False)}"


def get_global_news(curr_date: str, look_back_days: int = 7, limit: int = 20) -> str:
    df = ak.stock_news_main_cx().head(limit)
    return f"## China Market News, up to {curr_date}:\n\n{df.to_markdown(index=False)}"


def get_company_announcements(ticker: str, start_date: str, end_date: str) -> str:
    code = _plain_code(ticker)
    frames = []
    for session in trading_sessions("cn_a", start_date, end_date):
        date_str = session.strftime("%Y%m%d")
        for category in ("财务报告", "重大事项", "风险提示", "持股变动"):
            df = ak.stock_notice_report(symbol=category, date=date_str)
            matched = df[df["代码"].astype(str).str.zfill(6) == code]
            if not matched.empty:
                matched = matched.assign(抓取分类=category)
                frames.append(matched)
    if not frames:
        return f"No announcements found for {ticker} between {start_date} and {end_date}"
    merged = frames[0] if len(frames) == 1 else __import__("pandas").concat(frames, ignore_index=True)
    return f"## {ticker} Announcements, from {start_date} to {end_date}:\n\n{merged.to_markdown(index=False)}"
```

```python
# tradingagents/dataflows/interface.py
from .a_share_fundamentals import (
    get_balance_sheet as get_a_share_balance_sheet,
    get_cashflow as get_a_share_cashflow,
    get_fundamentals as get_a_share_fundamentals,
    get_income_statement as get_a_share_income_statement,
)
from .a_share_news import (
    get_company_announcements as get_a_share_company_announcements,
    get_global_news as get_a_share_global_news,
    get_news as get_a_share_news,
)

TOOLS_CATEGORIES["news_data"]["tools"] = [
    "get_news",
    "get_global_news",
    "get_insider_transactions",
    "get_company_announcements",
]

VENDOR_METHODS["get_fundamentals"]["a_share"] = get_a_share_fundamentals
VENDOR_METHODS["get_balance_sheet"]["a_share"] = get_a_share_balance_sheet
VENDOR_METHODS["get_cashflow"]["a_share"] = get_a_share_cashflow
VENDOR_METHODS["get_income_statement"]["a_share"] = get_a_share_income_statement
VENDOR_METHODS["get_news"]["a_share"] = get_a_share_news
VENDOR_METHODS["get_global_news"]["a_share"] = get_a_share_global_news
VENDOR_METHODS["get_company_announcements"] = {"a_share": get_a_share_company_announcements}
```

```python
# tradingagents/agents/utils/news_data_tools.py
@tool
def get_company_announcements(
    ticker: Annotated[str, "ticker symbol"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve exchange-filed company announcements for a given ticker symbol.
    Uses the configured news_data vendor.
    """
    return route_to_vendor("get_company_announcements", ticker, start_date, end_date)
```

```python
# tradingagents/agents/utils/agent_utils.py
from tradingagents.agents.utils.news_data_tools import (
    get_company_announcements,
    get_global_news,
    get_insider_transactions,
    get_news,
)
```

```python
# tradingagents/graph/trading_graph.py
"news": ToolNode(
    [
        get_news,
        get_global_news,
        get_insider_transactions,
        get_company_announcements,
    ]
),
"fundamentals": ToolNode(
    [
        get_fundamentals,
        get_balance_sheet,
        get_cashflow,
        get_income_statement,
        get_company_announcements,
    ]
),
```

```python
# tradingagents/agents/analysts/news_analyst.py
tools = [
    get_news,
    get_global_news,
    get_company_announcements,
]
system_message = (
    "You are a news researcher tasked with analyzing recent news and trends over the past week. "
    "For mainland China securities, prioritize exchange-filed announcements and regulatory disclosures "
    "before summarizing media coverage. Use get_news for media coverage, get_global_news for macro context, "
    "and get_company_announcements for filed notices."
    + " Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."
    + get_language_instruction()
)
```

```python
# tradingagents/agents/analysts/social_media_analyst.py
system_message = (
    "You are a social sentiment and company news analyst. For mainland China securities, "
    "focus on Chinese-language news flow, exchange notices, and investor sentiment proxies rather than Reddit-style chatter."
    + " Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."
    + get_language_instruction()
)
```

```python
# tradingagents/agents/analysts/fundamentals_analyst.py
tools = [
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement,
    get_company_announcements,
]
system_message = (
    "You are a researcher tasked with analyzing fundamental information about a company. "
    "For mainland China securities, explicitly inspect annual reports, quarterly reports, earnings pre-announcements, "
    "risk warnings, shareholding changes, and board disclosures using get_company_announcements."
    + " Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."
    + " Use the available tools: get_fundamentals, get_balance_sheet, get_cashflow, get_income_statement, get_company_announcements."
    + get_language_instruction()
)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_a_share_research_data.py -v`
Expected: PASS with 2 passing tests.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/dataflows/a_share_fundamentals.py tradingagents/dataflows/a_share_news.py tradingagents/dataflows/interface.py tradingagents/agents/utils/news_data_tools.py tradingagents/agents/utils/agent_utils.py tradingagents/graph/trading_graph.py tradingagents/agents/analysts/news_analyst.py tradingagents/agents/analysts/social_media_analyst.py tradingagents/agents/analysts/fundamentals_analyst.py tests/test_a_share_research_data.py
git commit -m "feat: add a-share research data vendors and announcement tools"
```

### Task 6: Make Research, Trader, And Portfolio Prompts A-Share Rule-Aware

**Files:**
- Modify: `tradingagents/agents/utils/agent_utils.py`
- Modify: `tradingagents/agents/schemas.py`
- Modify: `tradingagents/agents/managers/research_manager.py`
- Modify: `tradingagents/agents/trader/trader.py`
- Modify: `tradingagents/agents/managers/portfolio_manager.py`
- Modify: `tests/test_structured_agents.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_structured_agents.py
def test_trader_markdown_renders_execution_constraints():
    proposal = TraderProposal(
        action=TraderAction.BUY,
        reasoning="Breakout confirmed with volume.",
        position_sizing="4% of portfolio",
        execution_constraints="A shares are T+1; avoid buying names already pinned near limit-up.",
    )
    md = render_trader_proposal(proposal)
    assert "**Execution Constraints**: A shares are T+1;" in md


def test_portfolio_manager_markdown_renders_market_constraints():
    decision = PortfolioDecision(
        rating=PortfolioRating.HOLD,
        executive_summary="Build only after a pullback.",
        investment_thesis="Valuation is reasonable but liquidity and policy risk remain elevated.",
        market_constraints="Do not assume same-day exit after entry; flag suspension and price-limit risk.",
    )
    md = render_pm_decision(decision)
    assert "**Market Constraints**: Do not assume same-day exit after entry;" in md
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_structured_agents.py -v`
Expected: FAIL because `TraderProposal` and `PortfolioDecision` do not yet expose the new fields.

- [ ] **Step 3: Write minimal implementation**

```python
# tradingagents/agents/utils/agent_utils.py
def get_market_rules_instruction() -> str:
    from tradingagents.dataflows.config import get_config

    market = get_config().get("market", "us_equity")
    if market != "cn_a":
        return ""
    return (
        "\nA-share execution constraints to respect in every recommendation:\n"
        "- Assume common shares are T+1 after a buy; do not rely on same-day exits.\n"
        "- Do not recommend default short selling.\n"
        "- Explicitly mention price-limit risk (10% main board, 20% ChiNext/STAR, 5% ST risk-warning names).\n"
        "- Flag suspension, low liquidity, and disclosure risk when they matter.\n"
        "- Prefer staged entries and explicit position sizing over all-in execution assumptions.\n"
    )
```

```python
# tradingagents/agents/schemas.py
class TraderProposal(BaseModel):
    action: TraderAction = Field(
        description="The transaction direction. Exactly one of Buy / Hold / Sell.",
    )
    reasoning: str = Field(
        description=(
            "The case for this action, anchored in the analysts' reports and "
            "the research plan. Two to four sentences."
        ),
    )
    entry_price: Optional[float] = Field(
        default=None,
        description="Optional entry price target in the instrument's quote currency.",
    )
    stop_loss: Optional[float] = Field(
        default=None,
        description="Optional stop-loss price in the instrument's quote currency.",
    )
    position_sizing: Optional[str] = Field(
        default=None,
        description="Optional sizing guidance, e.g. '5% of portfolio'.",
    )
    execution_constraints: Optional[str] = Field(
        default=None,
        description="Market-rule-aware execution notes such as T+1, price limits, lot size, or suspension risk.",
    )


def render_trader_proposal(proposal: TraderProposal) -> str:
    parts = [
        f"**Action**: {proposal.action.value}",
        "",
        f"**Reasoning**: {proposal.reasoning}",
    ]
    if proposal.entry_price is not None:
        parts.extend(["", f"**Entry Price**: {proposal.entry_price}"])
    if proposal.stop_loss is not None:
        parts.extend(["", f"**Stop Loss**: {proposal.stop_loss}"])
    if proposal.position_sizing:
        parts.extend(["", f"**Position Sizing**: {proposal.position_sizing}"])
    if proposal.execution_constraints:
        parts.extend(["", f"**Execution Constraints**: {proposal.execution_constraints}"])
    parts.extend(["", f"FINAL TRANSACTION PROPOSAL: **{proposal.action.value.upper()}**"])
    return "\n".join(parts)


class PortfolioDecision(BaseModel):
    rating: PortfolioRating = Field(
        description=(
            "The final position rating. Exactly one of Buy / Overweight / Hold / "
            "Underweight / Sell, picked based on the analysts' debate."
        ),
    )
    executive_summary: str = Field(
        description=(
            "A concise action plan covering entry strategy, position sizing, "
            "key risk levels, and time horizon. Two to four sentences."
        ),
    )
    investment_thesis: str = Field(
        description=(
            "Detailed reasoning anchored in specific evidence from the analysts' "
            "debate. If prior lessons are referenced in the prompt context, "
            "incorporate them; otherwise rely solely on the current analysis."
        ),
    )
    price_target: Optional[float] = Field(
        default=None,
        description="Optional target price in the instrument's quote currency.",
    )
    time_horizon: Optional[str] = Field(
        default=None,
        description="Optional recommended holding period, e.g. '3-6 months'.",
    )
    market_constraints: Optional[str] = Field(
        default=None,
        description="Explicit market-structure constraints such as T+1, price limits, suspension risk, or board-specific rules.",
    )


def render_pm_decision(decision: PortfolioDecision) -> str:
    parts = [
        f"**Rating**: {decision.rating.value}",
        "",
        f"**Executive Summary**: {decision.executive_summary}",
        "",
        f"**Investment Thesis**: {decision.investment_thesis}",
    ]
    if decision.price_target is not None:
        parts.extend(["", f"**Price Target**: {decision.price_target}"])
    if decision.time_horizon:
        parts.extend(["", f"**Time Horizon**: {decision.time_horizon}"])
    if decision.market_constraints:
        parts.extend(["", f"**Market Constraints**: {decision.market_constraints}"])
    return "\n".join(parts)
```

```python
# tradingagents/agents/managers/research_manager.py
from tradingagents.agents.utils.agent_utils import build_instrument_context, get_market_rules_instruction

prompt = f"""As the Research Manager and debate facilitator, your role is to critically evaluate this round of debate and deliver a clear, actionable investment plan for the trader.

{instrument_context}
{get_market_rules_instruction()}

---
...
"""
```

```python
# tradingagents/agents/trader/trader.py
from tradingagents.agents.utils.agent_utils import build_instrument_context, get_market_rules_instruction

messages = [
    {
        "role": "system",
        "content": (
            "You are a trading agent analyzing market data to make investment decisions. "
            "Based on your analysis, provide a specific recommendation to buy, sell, or hold. "
            "Anchor your reasoning in the analysts' reports and the research plan."
            + get_market_rules_instruction()
        ),
    },
    ...
]
```

```python
# tradingagents/agents/managers/portfolio_manager.py
from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_language_instruction,
    get_market_rules_instruction,
)

prompt = f"""As the Portfolio Manager, synthesize the risk analysts' debate and deliver the final trading decision.

{instrument_context}
{get_market_rules_instruction()}

---
...
"""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_structured_agents.py -v`
Expected: PASS with the existing structured-agent tests and the 2 new A-share rendering assertions.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/agents/utils/agent_utils.py tradingagents/agents/schemas.py tradingagents/agents/managers/research_manager.py tradingagents/agents/trader/trader.py tradingagents/agents/managers/portfolio_manager.py tests/test_structured_agents.py
git commit -m "feat: add a-share rule-aware structured decisions"
```

### Task 7: Add Graph Regression Tests And Update User-Facing Docs

**Files:**
- Create: `tests/test_a_share_graph.py`
- Modify: `tests/test_memory_log.py`
- Modify: `README.md`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_a_share_graph.py
import unittest
from unittest.mock import MagicMock, patch

import pytest

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph


@pytest.mark.unit
class AShareGraphTests(unittest.TestCase):
    @patch("tradingagents.graph.trading_graph.Reflector")
    def test_cn_a_graph_passes_benchmark_to_reflector(self, reflector_cls):
        reflector_cls.return_value = MagicMock()
        cfg = DEFAULT_CONFIG.copy()
        cfg.update(
            {
                "market": "cn_a",
                "benchmark_symbol": "000300.SH",
                "calendar_code": "XSHG",
                "output_language": "Chinese",
            }
        )
        TradingAgentsGraph(config=cfg)
        _, kwargs = reflector_cls.call_args
        self.assertEqual(kwargs["benchmark_label"], "000300.SH")


if __name__ == "__main__":
    unittest.main()
```

```python
# tests/test_memory_log.py
def test_reflector_prompt_uses_custom_benchmark_label():
    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="Reflection.")
    reflector = Reflector(llm, benchmark_label="000300.SH")
    reflector.reflect_on_final_decision("Rating: Buy", 0.04, 0.01)
    human_content = llm.invoke.call_args.args[0][1][1]
    assert "Alpha vs 000300.SH" in human_content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_a_share_graph.py tests/test_memory_log.py -v`
Expected: FAIL until the new graph wiring and reflection test cases are present.

- [ ] **Step 3: Write minimal implementation**

```markdown
# README.md
## China A-Share Usage

TradingAgents can be configured for mainland China A shares by enabling the `cn_a` market profile and the `a_share` data vendor.

### Example configuration

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

config = DEFAULT_CONFIG.copy()
config.update(
    {
        "market": "cn_a",
        "benchmark_symbol": "000300.SH",
        "calendar_code": "XSHG",
        "output_language": "Chinese",
        "price_adjustment": "qfq",
        "data_vendors": {
            "core_stock_apis": "a_share",
            "technical_indicators": "a_share",
            "fundamental_data": "a_share",
            "news_data": "a_share",
        },
    }
)

ta = TradingAgentsGraph(debug=True, config=config)
_, decision = ta.propagate("600519.SH", "2026-04-30")
print(decision)
```

### A-share-specific behavior

- Ticker normalization supports `SH`, `SZ`, and `BJ` suffixes.
- Reflections use the configured mainland benchmark instead of `SPY`.
- Research prompts prioritize Chinese-language news and exchange-filed announcements.
- Trader and portfolio outputs explicitly surface T+1, price-limit, and suspension risks.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_a_share_graph.py tests/test_memory_log.py tests/test_market_profiles.py tests/test_a_share_calendar.py tests/test_a_share_dataflows.py tests/test_a_share_research_data.py tests/test_structured_agents.py -v`
Expected: PASS with all new A-share regression coverage green.

- [ ] **Step 5: Commit**

```bash
git add tests/test_a_share_graph.py tests/test_memory_log.py README.md
git commit -m "docs: document a-share compatibility workflow"
```

### Task 8: Run The Final Regression Sweep And Sanity-Check CLI Flow

**Files:**
- Modify: `cli/main.py:502-612`
- Modify: `cli/utils.py`
- Test: `tests/test_market_profiles.py`
- Test: `tests/test_ticker_symbol_handling.py`
- Test: `tests/test_a_share_calendar.py`
- Test: `tests/test_a_share_dataflows.py`
- Test: `tests/test_a_share_research_data.py`
- Test: `tests/test_a_share_graph.py`
- Test: `tests/test_structured_agents.py`
- Test: `tests/test_memory_log.py`

- [ ] **Step 1: Write the failing smoke checklist**

```text
1. CLI first prompt must ask for market before ticker.
2. Choosing cn_a must show mainland ticker examples.
3. cn_a must default output language to Chinese.
4. cn_a graph config must route all four data categories to a_share when selected.
5. Post-trade reflection must label alpha versus 000300.SH instead of SPY.
```

- [ ] **Step 2: Run the targeted automated suite**

Run: `pytest tests/test_market_profiles.py tests/test_ticker_symbol_handling.py tests/test_a_share_calendar.py tests/test_a_share_dataflows.py tests/test_a_share_research_data.py tests/test_a_share_graph.py tests/test_structured_agents.py tests/test_memory_log.py -v`
Expected: PASS with all A-share compatibility tests green.

- [ ] **Step 3: Run one CLI-level sanity command**

```bash
python -m pytest tests/test_market_profiles.py tests/test_ticker_symbol_handling.py tests/test_a_share_calendar.py tests/test_a_share_dataflows.py tests/test_a_share_research_data.py tests/test_a_share_graph.py tests/test_structured_agents.py tests/test_memory_log.py -v
```

```text
Expected:
- no import errors for akshare or exchange_calendars
- no routing errors for get_company_announcements
- no schema/rendering regressions in structured-agent tests
```

- [ ] **Step 4: Capture final manual verification notes**

```text
Manual checks:
- Start the CLI and confirm the first prompt is market selection.
- Choose China A-Share and enter 600519; confirm the CLI canonicalizes it to 600519.SH.
- Run a dry analysis date such as 2026-04-30 and inspect saved logs for a Chinese report plus 000300.SH benchmark wording.
- Open the final portfolio report and verify it contains explicit execution constraints or market constraints when the recommendation is actionable.
```

- [ ] **Step 5: Commit**

```bash
git add cli/main.py cli/utils.py tests/test_market_profiles.py tests/test_ticker_symbol_handling.py tests/test_a_share_calendar.py tests/test_a_share_dataflows.py tests/test_a_share_research_data.py tests/test_a_share_graph.py tests/test_structured_agents.py tests/test_memory_log.py README.md
git commit -m "test: finalize a-share compatibility regression coverage"
```

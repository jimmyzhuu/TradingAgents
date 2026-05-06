import shutil
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
import pytest

from tradingagents.dataflows import a_share_market
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
        self.cache_dir = tempfile.mkdtemp(prefix="tradingagents-task4-a-share-cache-")
        set_config(
            {
                "market": "cn_a",
                "data_cache_dir": self.cache_dir,
                "price_adjustment": "qfq",
                "data_vendors": {
                    "core_stock_apis": "a_share",
                    "technical_indicators": "a_share",
                    "fundamental_data": "yfinance",
                    "news_data": "yfinance",
                },
            }
        )

    def tearDown(self):
        shutil.rmtree(self.cache_dir, ignore_errors=True)

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

    @patch("tradingagents.dataflows.y_finance._get_stock_stats_bulk")
    def test_get_indicators_route_explicitly_uses_cn_a_market_when_vendor_is_a_share(self, mock_bulk):
        set_config(
            {
                "market": "us_equity",
                "data_cache_dir": self.cache_dir,
                "price_adjustment": "qfq",
                "data_vendors": {
                    "core_stock_apis": "yfinance",
                    "technical_indicators": "a_share",
                    "fundamental_data": "yfinance",
                    "news_data": "yfinance",
                },
            }
        )
        mock_bulk.return_value = {"2026-01-10": "55.5"}

        text = route_to_vendor("get_indicators", "600519.SH", "rsi", "2026-01-10", 0)

        self.assertIn("2026-01-10: 55.5", text)
        self.assertEqual(mock_bulk.call_args.kwargs["market"], "cn_a")

    @patch("tradingagents.dataflows.y_finance.get_stockstats_indicator")
    @patch("tradingagents.dataflows.y_finance._get_stock_stats_bulk")
    def test_get_indicators_fallback_preserves_cn_a_market_override(self, mock_bulk, mock_single):
        set_config(
            {
                "market": "us_equity",
                "data_cache_dir": self.cache_dir,
                "price_adjustment": "qfq",
                "data_vendors": {
                    "core_stock_apis": "yfinance",
                    "technical_indicators": "a_share",
                    "fundamental_data": "yfinance",
                    "news_data": "yfinance",
                },
            }
        )
        mock_bulk.side_effect = RuntimeError("bulk unavailable")
        mock_single.return_value = "55.5"

        text = route_to_vendor("get_indicators", "600519.SH", "rsi", "2026-01-10", 0)

        self.assertIn("2026-01-10: 55.5", text)
        self.assertEqual(mock_single.call_args.kwargs["market"], "cn_a")

    @patch("tradingagents.dataflows.a_share_market.ak.stock_zh_a_hist")
    def test_load_ohlcv_cn_a_reuses_cache_for_same_symbol_and_window(self, mock_hist):
        mock_hist.return_value = _ashare_hist_df()

        first = load_ohlcv("600519.SH", "2026-01-10", market="cn_a")
        second = load_ohlcv("600519.SH", "2026-01-10", market="cn_a")

        self.assertEqual(mock_hist.call_count, 1)
        self.assertEqual(len(first), len(second))

    def test_fetch_ohlcv_reuses_canonicalize_validation_for_wrong_suffix(self):
        with self.assertRaisesRegex(ValueError, r"use \.SZ suffix"):
            a_share_market.fetch_ohlcv("000001.SH", "2026-01-01", "2026-01-10")

    def test_fetch_ohlcv_rejects_unsupported_mainland_symbol_category(self):
        with self.assertRaisesRegex(ValueError, "Unsupported cn_a instrument"):
            a_share_market.fetch_ohlcv("510300", "2026-01-01", "2026-01-10")


if __name__ == "__main__":
    unittest.main()

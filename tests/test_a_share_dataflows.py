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

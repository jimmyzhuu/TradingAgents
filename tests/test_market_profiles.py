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

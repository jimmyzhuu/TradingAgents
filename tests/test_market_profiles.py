import unittest
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cli import utils as cli_utils
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

    def test_cli_questionary_call_sites_use_helper_import(self):
        class _Prompt:
            def __init__(self, value):
                self._value = value

            def ask(self):
                return self._value

        class _FakeQuestionary:
            @staticmethod
            def Choice(title, value=None):
                return value if value is not None else title

            @staticmethod
            def Style(config):
                return config

            @staticmethod
            def select(*args, **kwargs):
                prompt = kwargs.get("choices", [None])[0]
                return _Prompt(prompt)

            @staticmethod
            def text(*args, **kwargs):
                return _Prompt("Thai")

        with patch.object(cli_utils, "_questionary", return_value=_FakeQuestionary):
            self.assertEqual(
                cli_utils.select_llm_provider(),
                ("openai", "https://api.openai.com/v1"),
            )
            self.assertEqual(cli_utils.ask_openai_reasoning_effort(), "medium")
            self.assertEqual(cli_utils.ask_anthropic_effort(), "high")
            self.assertEqual(cli_utils.ask_gemini_thinking_config(), "high")
            self.assertEqual(cli_utils.ask_output_language(), "English")


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import patch

import pytest

import cli.main as cli_main
from cli.utils import (
    get_default_output_language,
    get_ticker_input_examples,
    normalize_ticker_symbol,
)
from tradingagents.agents.utils.agent_utils import build_instrument_context
from tradingagents.default_config import DEFAULT_CONFIG


@pytest.mark.unit
class TickerSymbolHandlingTests(unittest.TestCase):
    def test_cli_main_get_ticker_uses_market_aware_helper(self):
        class FakeQuestionary:
            @staticmethod
            def text(*args, **kwargs):
                class Prompt:
                    @staticmethod
                    def ask():
                        return "600519"

                return Prompt()

            @staticmethod
            def Style(style_config):
                return style_config

        with patch("cli.utils._questionary", return_value=FakeQuestionary):
            self.assertEqual(cli_main.get_ticker("cn_a"), "600519.SH")

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

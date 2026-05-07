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

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

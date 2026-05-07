import unittest
from unittest.mock import patch

import pandas as pd
import pytest
from langchain_core.runnables import RunnableLambda

from tradingagents.agents.analysts.fundamentals_analyst import create_fundamentals_analyst
from tradingagents.agents.analysts.news_analyst import create_news_analyst
from tradingagents.agents.analysts.social_media_analyst import create_social_media_analyst
from tradingagents.agents.utils.news_data_tools import get_company_announcements
from tradingagents.dataflows.config import set_config
from tradingagents.dataflows.interface import TOOLS_CATEGORIES, route_to_vendor
from tradingagents.graph.trading_graph import TradingAgentsGraph


class _FakeLLM:
    def __init__(self):
        self.response = type("FakeResponse", (), {"tool_calls": [], "content": "ok"})()
        self.captured_tools = []
        self.captured_prompt = []

    def bind_tools(self, tools):
        self.captured_tools = tools
        return RunnableLambda(self._capture_prompt_and_respond)

    def _capture_prompt_and_respond(self, prompt_value):
        self.captured_prompt = prompt_value.to_messages()
        return self.response


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

    @patch("tradingagents.dataflows.a_share_fundamentals.ak.stock_individual_info_em")
    def test_fundamentals_route_to_a_share_vendor(self, mock_info):
        mock_info.return_value = pd.DataFrame(
            {
                "item": ["股票简称", "行业", "总市值"],
                "value": ["贵州茅台", "酿酒行业", "123456789"],
            }
        )

        text = route_to_vendor("get_fundamentals", "600519.SH", "2026-01-10")

        self.assertIn("贵州茅台", text)
        self.assertIn("酿酒行业", text)

    @patch("tradingagents.dataflows.a_share_news.trading_sessions")
    @patch("tradingagents.dataflows.a_share_news.ak.stock_notice_report")
    def test_company_announcements_filter_by_code(self, mock_notice, mock_sessions):
        mock_sessions.return_value = [pd.Timestamp("2026-03-28")]
        mock_notice.return_value = pd.DataFrame(
            {
                "代码": ["600519", "000001"],
                "名称": ["贵州茅台", "平安银行"],
                "公告标题": ["贵州茅台2025年年度报告", "平安银行公告"],
                "公告日期": ["2026-03-28", "2026-03-28"],
                "网址": ["https://example.com/moutai", "https://example.com/pab"],
            }
        )

        text = route_to_vendor("get_company_announcements", "600519.SH", "2026-03-28", "2026-03-28")

        self.assertIn("贵州茅台2025年年度报告", text)
        self.assertNotIn("平安银行公告", text)

    def test_news_tools_category_exposes_company_announcements(self):
        self.assertIn("get_company_announcements", TOOLS_CATEGORIES["news_data"]["tools"])

    def test_graph_tool_nodes_include_company_announcements_for_news_and_fundamentals(self):
        graph = TradingAgentsGraph.__new__(TradingAgentsGraph)
        graph.tool_nodes = TradingAgentsGraph._create_tool_nodes(graph)

        news_tools = set(graph.tool_nodes["news"].tools_by_name.keys())
        fundamentals_tools = set(graph.tool_nodes["fundamentals"].tools_by_name.keys())

        self.assertIn("get_company_announcements", news_tools)
        self.assertIn("get_company_announcements", fundamentals_tools)

    def test_get_company_announcements_tool_routes_through_vendor_interface(self):
        with patch("tradingagents.agents.utils.news_data_tools.route_to_vendor", return_value="announcements") as mock_route:
            result = get_company_announcements.invoke(
                {"ticker": "600519.SH", "start_date": "2026-03-28", "end_date": "2026-03-28"}
            )

        self.assertEqual(result, "announcements")
        mock_route.assert_called_once_with(
            "get_company_announcements", "600519.SH", "2026-03-28", "2026-03-28"
        )

    def test_analyst_prompts_prioritize_announcements_for_mainland_china(self):
        for factory, expected_tool_names, expected_text in [
            (
                create_news_analyst,
                {"get_news", "get_global_news", "get_company_announcements"},
                "prioritize exchange-filed announcements and regulatory disclosures",
            ),
            (
                create_social_media_analyst,
                {"get_news"},
                "exchange notices",
            ),
            (
                create_fundamentals_analyst,
                {
                    "get_fundamentals",
                    "get_balance_sheet",
                    "get_cashflow",
                    "get_income_statement",
                    "get_company_announcements",
                },
                "explicitly inspect annual reports, quarterly reports, earnings pre-announcements",
            ),
        ]:
            fake_llm = _FakeLLM()
            analyst = factory(fake_llm)
            analyst(
                {
                    "trade_date": "2026-03-28",
                    "company_of_interest": "600519.SH",
                    "messages": [],
                }
            )

            tool_names = {tool.name for tool in fake_llm.captured_tools}
            prompt_text = "\n".join(message.content for message in fake_llm.captured_prompt)

            self.assertTrue(expected_tool_names.issubset(tool_names))
            self.assertIn(expected_text, prompt_text)


if __name__ == "__main__":
    unittest.main()

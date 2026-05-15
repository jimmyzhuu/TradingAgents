import unittest
from pathlib import Path

import pytest

from tradingagents.default_config import DEFAULT_CONFIG, build_cn_a_runtime_config


@pytest.mark.unit
class RuntimePresetTests(unittest.TestCase):
    def test_build_cn_a_runtime_config_sets_formal_a_share_defaults(self):
        config = build_cn_a_runtime_config()

        self.assertEqual(config["market"], "cn_a")
        self.assertEqual(config["benchmark_symbol"], "000300.SH")
        self.assertEqual(config["calendar_code"], "XSHG")
        self.assertEqual(config["output_language"], "Chinese")
        self.assertEqual(config["deep_think_llm"], "gpt-5.4")
        self.assertEqual(config["quick_think_llm"], "gpt-5.4-mini")
        self.assertEqual(config["openai_reasoning_effort"], "high")
        self.assertEqual(
            config["data_vendors"],
            {
                "core_stock_apis": "a_share",
                "technical_indicators": "a_share",
                "fundamental_data": "a_share",
                "news_data": "a_share",
            },
        )

    def test_build_cn_a_runtime_config_applies_overrides_last(self):
        config = build_cn_a_runtime_config(
            {
                "benchmark_symbol": "000905.SH",
                "quick_think_llm": "gpt-5.4",
                "output_language": "English",
            }
        )

        self.assertEqual(config["benchmark_symbol"], "000905.SH")
        self.assertEqual(config["quick_think_llm"], "gpt-5.4")
        self.assertEqual(config["output_language"], "English")

    def test_build_cn_a_runtime_config_does_not_mutate_default_config(self):
        _ = build_cn_a_runtime_config()

        self.assertEqual(DEFAULT_CONFIG["market"], "us_equity")
        self.assertEqual(DEFAULT_CONFIG["benchmark_symbol"], "SPY")
        self.assertEqual(DEFAULT_CONFIG["calendar_code"], "XNYS")
        self.assertEqual(DEFAULT_CONFIG["output_language"], "English")
        self.assertEqual(DEFAULT_CONFIG["data_vendors"]["core_stock_apis"], "yfinance")

    def test_build_cn_a_runtime_config_reads_backend_url_from_env(self):
        with pytest.MonkeyPatch.context() as monkeypatch:
            monkeypatch.setenv(
                "TRADINGAGENTS_OPENAI_BASE_URL",
                "https://sub2api.sunnyrae.cn",
            )
            config = build_cn_a_runtime_config()

        self.assertEqual(config["backend_url"], "https://sub2api.sunnyrae.cn")

    def test_build_cn_a_runtime_config_reads_standard_openai_base_url_alias(self):
        with pytest.MonkeyPatch.context() as monkeypatch:
            monkeypatch.delenv("TRADINGAGENTS_OPENAI_BASE_URL", raising=False)
            monkeypatch.setenv(
                "OPENAI_BASE_URL",
                "https://standard-gateway.example/v1",
            )
            config = build_cn_a_runtime_config()

        self.assertEqual(config["backend_url"], "https://standard-gateway.example/v1")

    def test_build_cn_a_runtime_config_prefers_project_openai_base_url_alias(self):
        with pytest.MonkeyPatch.context() as monkeypatch:
            monkeypatch.setenv(
                "TRADINGAGENTS_OPENAI_BASE_URL",
                "https://project-gateway.example/v1",
            )
            monkeypatch.setenv(
                "OPENAI_BASE_URL",
                "https://standard-gateway.example/v1",
            )
            config = build_cn_a_runtime_config()

        self.assertEqual(config["backend_url"], "https://project-gateway.example/v1")

    def test_main_py_uses_cn_a_runtime_preset(self):
        main_py = Path("main.py").read_text()

        self.assertIn("build_cn_a_runtime_config", main_py)
        self.assertNotIn('config["market"] = "cn_a"', main_py)
        self.assertNotIn('config["benchmark_symbol"] = "000300.SH"', main_py)

    def test_readme_references_formal_cn_a_runtime_preset(self):
        readme = Path("README.md").read_text()

        self.assertIn("build_cn_a_runtime_config", readme)
        self.assertNotIn('config["market"] = "cn_a"', readme)


if __name__ == "__main__":
    unittest.main()

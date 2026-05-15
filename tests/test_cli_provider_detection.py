from unittest.mock import patch

import pytest

from cli import utils as cli_utils


@pytest.mark.unit
def test_get_configured_llm_providers_filters_to_present_env_keys():
    with patch.dict(
        "os.environ",
        {
            "OPENAI_API_KEY": "openai-key",
            "DEEPSEEK_API_KEY": "deepseek-key",
            "TRADINGAGENTS_ENABLE_OLLAMA": "1",
        },
        clear=True,
    ):
        providers = cli_utils.get_configured_llm_providers()

    assert [provider["key"] for provider in providers] == [
        "openai",
        "deepseek",
        "ollama",
    ]


@pytest.mark.unit
def test_select_llm_provider_auto_selects_single_configured_provider():
    with patch.dict("os.environ", {"OPENAI_API_KEY": "openai-key"}, clear=True):
        with patch.object(cli_utils, "_questionary", side_effect=AssertionError("should not prompt")):
            provider = cli_utils.select_llm_provider()

    assert provider == ("openai", "https://api.openai.com/v1")


@pytest.mark.unit
def test_select_llm_provider_uses_openai_gateway_base_url_from_env():
    with patch.dict(
        "os.environ",
        {
            "OPENAI_API_KEY": "openai-key",
            "TRADINGAGENTS_OPENAI_BASE_URL": "https://gateway.example/v1",
        },
        clear=True,
    ):
        with patch.object(cli_utils, "_questionary", side_effect=AssertionError("should not prompt")):
            provider = cli_utils.select_llm_provider()

    assert provider == ("openai", "https://gateway.example/v1")


@pytest.mark.unit
def test_select_llm_provider_uses_standard_openai_base_url_alias():
    with patch.dict(
        "os.environ",
        {
            "OPENAI_API_KEY": "openai-key",
            "OPENAI_BASE_URL": "https://standard-gateway.example/v1",
        },
        clear=True,
    ):
        with patch.object(cli_utils, "_questionary", side_effect=AssertionError("should not prompt")):
            provider = cli_utils.select_llm_provider()

    assert provider == ("openai", "https://standard-gateway.example/v1")


@pytest.mark.unit
def test_select_llm_provider_prefers_tradingagents_openai_base_url_alias():
    with patch.dict(
        "os.environ",
        {
            "OPENAI_API_KEY": "openai-key",
            "TRADINGAGENTS_OPENAI_BASE_URL": "https://project-gateway.example/v1",
            "OPENAI_BASE_URL": "https://standard-gateway.example/v1",
        },
        clear=True,
    ):
        with patch.object(cli_utils, "_questionary", side_effect=AssertionError("should not prompt")):
            provider = cli_utils.select_llm_provider()

    assert provider == ("openai", "https://project-gateway.example/v1")


@pytest.mark.unit
def test_select_llm_provider_falls_back_to_full_list_when_none_configured():
    seen = {}

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
            seen["choices"] = kwargs["choices"]
            return _Prompt(kwargs["choices"][0])

    with patch.dict("os.environ", {}, clear=True):
        with patch.object(cli_utils, "_questionary", return_value=_FakeQuestionary):
            provider = cli_utils.select_llm_provider()

    assert len(seen["choices"]) == len(cli_utils.LLM_PROVIDERS)
    assert provider == ("openai", "https://api.openai.com/v1")

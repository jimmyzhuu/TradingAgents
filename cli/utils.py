import os
from typing import List, Optional, Tuple, Dict

from rich.console import Console

from cli.models import AnalystType
from tradingagents.llm_clients.openai_base_url import get_openai_base_url_from_env
from tradingagents.llm_clients.model_catalog import get_model_options
from tradingagents.markets.profiles import MARKET_PROFILES, canonicalize_ticker

console = Console()

TICKER_INPUT_EXAMPLES = "Examples: SPY, CNC.TO, 7203.T, 0700.HK"

ANALYST_ORDER = [
    ("Market Analyst", AnalystType.MARKET),
    ("Social Media Analyst", AnalystType.SOCIAL),
    ("News Analyst", AnalystType.NEWS),
    ("Fundamentals Analyst", AnalystType.FUNDAMENTALS),
]

LLM_PROVIDERS = [
    {
        "display": "OpenAI",
        "key": "openai",
        "base_url": "https://api.openai.com/v1",
        "env_keys": ("OPENAI_API_KEY",),
    },
    {
        "display": "Google",
        "key": "google",
        "base_url": None,
        "env_keys": ("GOOGLE_API_KEY",),
    },
    {
        "display": "Anthropic",
        "key": "anthropic",
        "base_url": "https://api.anthropic.com/",
        "env_keys": ("ANTHROPIC_API_KEY",),
    },
    {
        "display": "xAI",
        "key": "xai",
        "base_url": "https://api.x.ai/v1",
        "env_keys": ("XAI_API_KEY",),
    },
    {
        "display": "DeepSeek",
        "key": "deepseek",
        "base_url": "https://api.deepseek.com",
        "env_keys": ("DEEPSEEK_API_KEY",),
    },
    {
        "display": "Qwen",
        "key": "qwen",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "env_keys": ("DASHSCOPE_API_KEY",),
    },
    {
        "display": "GLM",
        "key": "glm",
        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        "env_keys": ("ZHIPU_API_KEY",),
    },
    {
        "display": "OpenRouter",
        "key": "openrouter",
        "base_url": "https://openrouter.ai/api/v1",
        "env_keys": ("OPENROUTER_API_KEY",),
    },
    {
        "display": "Azure OpenAI",
        "key": "azure",
        "base_url": None,
        "env_keys": ("AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"),
    },
    {
        "display": "Ollama",
        "key": "ollama",
        "base_url": "http://localhost:11434/v1",
        "env_keys": (),
    },
]


def _questionary():
    try:
        import questionary
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Optional CLI dependency 'questionary' is not installed. "
            "Install the CLI extras or add 'questionary' to use interactive prompts."
        ) from exc

    return questionary


def _has_required_env_keys(env_keys: Tuple[str, ...]) -> bool:
    return all(os.getenv(env_key, "").strip() for env_key in env_keys)


def _ollama_enabled() -> bool:
    return os.getenv("TRADINGAGENTS_ENABLE_OLLAMA", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def get_configured_llm_providers() -> List[Dict[str, object]]:
    configured = []
    for provider in LLM_PROVIDERS:
        if provider["key"] == "ollama":
            if _ollama_enabled():
                configured.append(provider)
            continue

        if _has_required_env_keys(provider["env_keys"]):
            configured.append(_provider_with_runtime_overrides(provider))

    return configured


def _provider_with_runtime_overrides(provider: Dict[str, object]) -> Dict[str, object]:
    if provider["key"] == "openai":
        gateway_url = get_openai_base_url_from_env()
        if gateway_url:
            overridden = provider.copy()
            overridden["base_url"] = gateway_url
            return overridden
    return provider


def get_ticker_input_examples(market: str) -> str:
    examples = {
        "us_equity": "Examples: SPY, NVDA, BRK.B, CNC.TO",
        "hk_equity": "Examples: 0700.HK, 9988.HK, 2318.HK",
        "cn_a": "Examples: 600519.SH, 000001.SZ, 300750.SZ, 430047.BJ",
    }
    return examples.get(market, examples["us_equity"])


def get_default_output_language(market: str) -> str:
    return "Chinese" if market == "cn_a" else "English"


def select_market() -> str:
    """Select the market to analyze."""
    questionary = _questionary()
    choice = questionary.select(
        "Select Market:",
        choices=[
            questionary.Choice(profile.display_name, value=market)
            for market, profile in MARKET_PROFILES.items()
        ],
        style=questionary.Style(
            [
                ("selected", "fg:green noinherit"),
                ("highlighted", "fg:green noinherit"),
                ("pointer", "fg:green noinherit"),
            ]
        ),
    ).ask()

    if choice is None:
        console.print("\n[red]No market selected. Exiting...[/red]")
        exit(1)

    return choice


def get_ticker(market: str = "us_equity") -> str:
    """Prompt the user to enter a ticker symbol."""
    questionary = _questionary()
    ticker = questionary.text(
        f"Enter the exact ticker symbol to analyze ({get_ticker_input_examples(market)}):",
        validate=lambda x: len(x.strip()) > 0 or "Please enter a valid ticker symbol.",
        style=questionary.Style(
            [
                ("text", "fg:green"),
                ("highlighted", "noinherit"),
            ]
        ),
    ).ask()

    if not ticker:
        console.print("\n[red]No ticker symbol provided. Exiting...[/red]")
        exit(1)

    return normalize_ticker_symbol(ticker, market=market)


def normalize_ticker_symbol(ticker: str, market: str = "us_equity") -> str:
    """Normalize ticker input while preserving exchange suffixes."""
    return canonicalize_ticker(ticker, market)


def get_analysis_date() -> str:
    """Prompt the user to enter a date in YYYY-MM-DD format."""
    import re
    from datetime import datetime
    questionary = _questionary()

    def validate_date(date_str: str) -> bool:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            return False
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    date = questionary.text(
        "Enter the analysis date (YYYY-MM-DD):",
        validate=lambda x: validate_date(x.strip())
        or "Please enter a valid date in YYYY-MM-DD format.",
        style=questionary.Style(
            [
                ("text", "fg:green"),
                ("highlighted", "noinherit"),
            ]
        ),
    ).ask()

    if not date:
        console.print("\n[red]No date provided. Exiting...[/red]")
        exit(1)

    return date.strip()


def select_analysts() -> List[AnalystType]:
    """Select analysts using an interactive checkbox."""
    questionary = _questionary()
    choices = questionary.checkbox(
        "Select Your [Analysts Team]:",
        choices=[
            questionary.Choice(display, value=value) for display, value in ANALYST_ORDER
        ],
        instruction="\n- Press Space to select/unselect analysts\n- Press 'a' to select/unselect all\n- Press Enter when done",
        validate=lambda x: len(x) > 0 or "You must select at least one analyst.",
        style=questionary.Style(
            [
                ("checkbox-selected", "fg:green"),
                ("selected", "fg:green noinherit"),
                ("highlighted", "noinherit"),
                ("pointer", "noinherit"),
            ]
        ),
    ).ask()

    if not choices:
        console.print("\n[red]No analysts selected. Exiting...[/red]")
        exit(1)

    return choices


def select_research_depth() -> int:
    """Select research depth using an interactive selection."""
    questionary = _questionary()

    # Define research depth options with their corresponding values
    DEPTH_OPTIONS = [
        ("Shallow - Quick research, few debate and strategy discussion rounds", 1),
        ("Medium - Middle ground, moderate debate rounds and strategy discussion", 3),
        ("Deep - Comprehensive research, in depth debate and strategy discussion", 5),
    ]

    choice = questionary.select(
        "Select Your [Research Depth]:",
        choices=[
            questionary.Choice(display, value=value) for display, value in DEPTH_OPTIONS
        ],
        instruction="\n- Use arrow keys to navigate\n- Press Enter to select",
        style=questionary.Style(
            [
                ("selected", "fg:yellow noinherit"),
                ("highlighted", "fg:yellow noinherit"),
                ("pointer", "fg:yellow noinherit"),
            ]
        ),
    ).ask()

    if choice is None:
        console.print("\n[red]No research depth selected. Exiting...[/red]")
        exit(1)

    return choice


def _fetch_openrouter_models() -> List[Tuple[str, str]]:
    """Fetch available models from the OpenRouter API."""
    import requests
    try:
        resp = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
        resp.raise_for_status()
        models = resp.json().get("data", [])
        return [(m.get("name") or m["id"], m["id"]) for m in models]
    except Exception as e:
        console.print(f"\n[yellow]Could not fetch OpenRouter models: {e}[/yellow]")
        return []


def select_openrouter_model() -> str:
    """Select an OpenRouter model from the newest available, or enter a custom ID."""
    questionary = _questionary()
    models = _fetch_openrouter_models()

    choices = [questionary.Choice(name, value=mid) for name, mid in models[:5]]
    choices.append(questionary.Choice("Custom model ID", value="custom"))

    choice = questionary.select(
        "Select OpenRouter Model (latest available):",
        choices=choices,
        instruction="\n- Use arrow keys to navigate\n- Press Enter to select",
        style=questionary.Style([
            ("selected", "fg:magenta noinherit"),
            ("highlighted", "fg:magenta noinherit"),
            ("pointer", "fg:magenta noinherit"),
        ]),
    ).ask()

    if choice is None or choice == "custom":
        return questionary.text(
            "Enter OpenRouter model ID (e.g. google/gemma-4-26b-a4b-it):",
            validate=lambda x: len(x.strip()) > 0 or "Please enter a model ID.",
        ).ask().strip()

    return choice


def _prompt_custom_model_id() -> str:
    """Prompt user to type a custom model ID."""
    questionary = _questionary()
    return questionary.text(
        "Enter model ID:",
        validate=lambda x: len(x.strip()) > 0 or "Please enter a model ID.",
    ).ask().strip()


def _select_model(provider: str, mode: str) -> str:
    """Select a model for the given provider and mode (quick/deep)."""
    questionary = _questionary()
    if provider.lower() == "openrouter":
        return select_openrouter_model()

    if provider.lower() == "azure":
        return questionary.text(
            f"Enter Azure deployment name ({mode}-thinking):",
            validate=lambda x: len(x.strip()) > 0 or "Please enter a deployment name.",
        ).ask().strip()

    choice = questionary.select(
        f"Select Your [{mode.title()}-Thinking LLM Engine]:",
        choices=[
            questionary.Choice(display, value=value)
            for display, value in get_model_options(provider, mode)
        ],
        instruction="\n- Use arrow keys to navigate\n- Press Enter to select",
        style=questionary.Style(
            [
                ("selected", "fg:magenta noinherit"),
                ("highlighted", "fg:magenta noinherit"),
                ("pointer", "fg:magenta noinherit"),
            ]
        ),
    ).ask()

    if choice is None:
        console.print(f"\n[red]No {mode} thinking llm engine selected. Exiting...[/red]")
        exit(1)

    if choice == "custom":
        return _prompt_custom_model_id()

    return choice


def select_shallow_thinking_agent(provider) -> str:
    """Select shallow thinking llm engine using an interactive selection."""
    return _select_model(provider, "quick")


def select_deep_thinking_agent(provider) -> str:
    """Select deep thinking llm engine using an interactive selection."""
    return _select_model(provider, "deep")


def select_llm_provider() -> tuple[str, str | None]:
    """Select the LLM provider and its API endpoint."""
    available_providers = get_configured_llm_providers()

    if len(available_providers) == 1:
        provider = available_providers[0]
        return provider["key"], provider["base_url"]

    if not available_providers:
        console.print(
            "\n[yellow]No configured provider detected from environment variables. "
            "Showing the full provider list.[/yellow]"
        )
        available_providers = [
            _provider_with_runtime_overrides(provider) for provider in LLM_PROVIDERS
        ]

    questionary = _questionary()

    choice = questionary.select(
        "Select your LLM Provider:",
        choices=[
            questionary.Choice(
                provider["display"],
                value=(provider["key"], provider["base_url"]),
            )
            for provider in available_providers
        ],
        instruction="\n- Use arrow keys to navigate\n- Press Enter to select",
        style=questionary.Style(
            [
                ("selected", "fg:magenta noinherit"),
                ("highlighted", "fg:magenta noinherit"),
                ("pointer", "fg:magenta noinherit"),
            ]
        ),
    ).ask()
    
    if choice is None:
        console.print("\n[red]No LLM provider selected. Exiting...[/red]")
        exit(1)

    provider, url = choice
    return provider, url


def ask_openai_reasoning_effort() -> str:
    """Ask for OpenAI reasoning effort level."""
    questionary = _questionary()
    choices = [
        questionary.Choice("Medium (Default)", "medium"),
        questionary.Choice("High (More thorough)", "high"),
        questionary.Choice("Low (Faster)", "low"),
    ]
    return questionary.select(
        "Select Reasoning Effort:",
        choices=choices,
        style=questionary.Style([
            ("selected", "fg:cyan noinherit"),
            ("highlighted", "fg:cyan noinherit"),
            ("pointer", "fg:cyan noinherit"),
        ]),
    ).ask()


def ask_anthropic_effort() -> str | None:
    """Ask for Anthropic effort level.

    Controls token usage and response thoroughness on Claude 4.5+ and 4.6 models.
    """
    questionary = _questionary()
    return questionary.select(
        "Select Effort Level:",
        choices=[
            questionary.Choice("High (recommended)", "high"),
            questionary.Choice("Medium (balanced)", "medium"),
            questionary.Choice("Low (faster, cheaper)", "low"),
        ],
        style=questionary.Style([
            ("selected", "fg:cyan noinherit"),
            ("highlighted", "fg:cyan noinherit"),
            ("pointer", "fg:cyan noinherit"),
        ]),
    ).ask()


def ask_gemini_thinking_config() -> str | None:
    """Ask for Gemini thinking configuration.

    Returns thinking_level: "high" or "minimal".
    Client maps to appropriate API param based on model series.
    """
    questionary = _questionary()
    return questionary.select(
        "Select Thinking Mode:",
        choices=[
            questionary.Choice("Enable Thinking (recommended)", "high"),
            questionary.Choice("Minimal/Disable Thinking", "minimal"),
        ],
        style=questionary.Style([
            ("selected", "fg:green noinherit"),
            ("highlighted", "fg:green noinherit"),
            ("pointer", "fg:green noinherit"),
        ]),
    ).ask()


def ask_output_language(default: str = "English") -> str:
    """Ask for report output language."""
    questionary = _questionary()
    default_choice = default if default in {
        "English",
        "Chinese",
        "Japanese",
        "Korean",
        "Hindi",
        "Spanish",
        "Portuguese",
        "French",
        "German",
        "Arabic",
        "Russian",
    } else "English"
    choice = questionary.select(
        "Select Output Language:",
        choices=[
            questionary.Choice(
                "English (default)" if default_choice == "English" else "English",
                "English",
            ),
            questionary.Choice(
                "Chinese (中文, default)" if default_choice == "Chinese" else "Chinese (中文)",
                "Chinese",
            ),
            questionary.Choice("Japanese (日本語)", "Japanese"),
            questionary.Choice("Korean (한국어)", "Korean"),
            questionary.Choice("Hindi (हिन्दी)", "Hindi"),
            questionary.Choice("Spanish (Español)", "Spanish"),
            questionary.Choice("Portuguese (Português)", "Portuguese"),
            questionary.Choice("French (Français)", "French"),
            questionary.Choice("German (Deutsch)", "German"),
            questionary.Choice("Arabic (العربية)", "Arabic"),
            questionary.Choice("Russian (Русский)", "Russian"),
            questionary.Choice("Custom language", "custom"),
        ],
        style=questionary.Style([
            ("selected", "fg:yellow noinherit"),
            ("highlighted", "fg:yellow noinherit"),
            ("pointer", "fg:yellow noinherit"),
        ]),
        default=default_choice,
    ).ask()

    if choice == "custom":
        return questionary.text(
            "Enter language name (e.g. Turkish, Vietnamese, Thai, Indonesian):",
            validate=lambda x: len(x.strip()) > 0 or "Please enter a language name.",
        ).ask().strip()

    return choice

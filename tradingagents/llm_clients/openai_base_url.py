import os


OPENAI_BASE_URL_ENV_KEYS = (
    "TRADINGAGENTS_OPENAI_BASE_URL",
    "OPENAI_BASE_URL",
    "OPENAI_API_BASE",
)


def get_openai_base_url_from_env() -> str | None:
    """Return the first configured OpenAI-compatible base URL."""

    for env_key in OPENAI_BASE_URL_ENV_KEYS:
        value = os.getenv(env_key, "").strip()
        if value:
            return value
    return None

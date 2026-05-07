from langchain_core.messages import HumanMessage, RemoveMessage

# Import tools from separate utility files
from tradingagents.agents.utils.core_stock_tools import (
    get_stock_data
)
from tradingagents.agents.utils.technical_indicators_tools import (
    get_indicators
)
from tradingagents.agents.utils.fundamental_data_tools import (
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement
)
from tradingagents.agents.utils.news_data_tools import (
    get_news,
    get_insider_transactions,
    get_global_news,
    get_company_announcements,
)


def get_language_instruction() -> str:
    """Return a prompt instruction for the configured output language.

    Returns empty string when English (default), so no extra tokens are used.
    Only applied to user-facing agents (analysts, portfolio manager).
    Internal debate agents stay in English for reasoning quality.
    """
    from tradingagents.dataflows.config import get_config
    lang = get_config().get("output_language", "English")
    if lang.strip().lower() == "english":
        return ""
    return f" Write your entire response in {lang}."


def get_market_rules_instruction() -> str:
    """Return market-structure constraints the decision agents must respect."""
    from tradingagents.dataflows.config import get_config

    market = get_config().get("market", "us_equity")
    if market != "cn_a":
        return ""
    return (
        "\nA-share execution constraints to respect in every recommendation:\n"
        "- Assume common shares are T+1 after a buy; do not rely on same-day exits.\n"
        "- Do not recommend default short selling.\n"
        "- Explicitly mention price-limit risk (10% main board, 20% ChiNext/STAR, 5% ST risk-warning names).\n"
        "- Flag suspension, low liquidity, and disclosure risk when they matter.\n"
        "- Prefer staged entries and explicit position sizing over all-in execution assumptions.\n"
    )


def build_instrument_context(ticker: str) -> str:
    """Describe the exact instrument so agents preserve exchange-qualified tickers."""
    return (
        f"The instrument to analyze is `{ticker}`. "
        "Use this exact ticker in every tool call, report, and recommendation, "
        "preserving any exchange suffix (e.g. `.SH`, `.SZ`, `.BJ`, `.HK`, `.TO`, `.L`, `.T`)."
    )

def create_msg_delete():
    def delete_messages(state):
        """Clear messages and add placeholder for Anthropic compatibility"""
        messages = state["messages"]

        # Remove all messages
        removal_operations = [RemoveMessage(id=m.id) for m in messages]

        # Add a minimal placeholder message
        placeholder = HumanMessage(content="Continue")

        return {"messages": removal_operations + [placeholder]}

    return delete_messages


        

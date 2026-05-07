from __future__ import annotations

from importlib import import_module
from typing import Annotated

import tradingagents.dataflows.a_share_fundamentals
import tradingagents.dataflows.a_share_news

from .alpha_vantage_common import AlphaVantageRateLimitError
from .config import get_config

# Tools organized by category
TOOLS_CATEGORIES = {
    "core_stock_apis": {
        "description": "OHLCV stock price data",
        "tools": [
            "get_stock_data"
        ]
    },
    "technical_indicators": {
        "description": "Technical analysis indicators",
        "tools": [
            "get_indicators"
        ]
    },
    "fundamental_data": {
        "description": "Company fundamentals",
        "tools": [
            "get_fundamentals",
            "get_balance_sheet",
            "get_cashflow",
            "get_income_statement"
        ]
    },
    "news_data": {
        "description": "News and insider data",
        "tools": [
            "get_news",
            "get_global_news",
            "get_insider_transactions",
            "get_company_announcements",
        ]
    }
}

VENDOR_LIST = [
    "yfinance",
    "alpha_vantage",
    "a_share",
]


def _load_yfinance_module():
    return import_module("tradingagents.dataflows.y_finance")


def _load_yfinance_news_module():
    return import_module("tradingagents.dataflows.yfinance_news")


def _load_alpha_vantage_module():
    return import_module("tradingagents.dataflows.alpha_vantage")


def _load_a_share_market_module():
    return import_module("tradingagents.dataflows.a_share_market")


def _load_a_share_fundamentals_module():
    return import_module("tradingagents.dataflows.a_share_fundamentals")


def _load_a_share_news_module():
    return import_module("tradingagents.dataflows.a_share_news")


def _call_module_func(loader, func_name: str, *args, **kwargs):
    module = loader()
    return getattr(module, func_name)(*args, **kwargs)


def _get_yfinance_stock_data(*args, **kwargs):
    return _call_module_func(_load_yfinance_module, "get_YFin_data_online", *args, **kwargs)


def _get_yfinance_indicators(*args, **kwargs):
    return _call_module_func(_load_yfinance_module, "get_stock_stats_indicators_window", *args, **kwargs)


def _get_a_share_stock(*args, **kwargs):
    return _call_module_func(_load_a_share_market_module, "get_stock", *args, **kwargs)


def _get_a_share_indicators(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[str, "The current trading date you are trading on, YYYY-mm-dd"],
    look_back_days: Annotated[int, "how many days to look back"],
):
    return _call_module_func(
        _load_yfinance_module,
        "get_stock_stats_indicators_window",
        symbol,
        indicator,
        curr_date,
        look_back_days,
        market="cn_a",
    )


def _get_yfinance_fundamentals(*args, **kwargs):
    return _call_module_func(_load_yfinance_module, "get_fundamentals", *args, **kwargs)


def _get_yfinance_balance_sheet(*args, **kwargs):
    return _call_module_func(_load_yfinance_module, "get_balance_sheet", *args, **kwargs)


def _get_yfinance_cashflow(*args, **kwargs):
    return _call_module_func(_load_yfinance_module, "get_cashflow", *args, **kwargs)


def _get_yfinance_income_statement(*args, **kwargs):
    return _call_module_func(_load_yfinance_module, "get_income_statement", *args, **kwargs)


def _get_a_share_fundamentals(*args, **kwargs):
    return _call_module_func(_load_a_share_fundamentals_module, "get_a_share_fundamentals", *args, **kwargs)


def _get_a_share_balance_sheet(*args, **kwargs):
    return _call_module_func(_load_a_share_fundamentals_module, "get_a_share_balance_sheet", *args, **kwargs)


def _get_a_share_cashflow(*args, **kwargs):
    return _call_module_func(_load_a_share_fundamentals_module, "get_a_share_cashflow", *args, **kwargs)


def _get_a_share_income_statement(*args, **kwargs):
    return _call_module_func(_load_a_share_fundamentals_module, "get_a_share_income_statement", *args, **kwargs)


def _get_yfinance_insider_transactions(*args, **kwargs):
    return _call_module_func(_load_yfinance_module, "get_insider_transactions", *args, **kwargs)


def _get_alpha_vantage_stock(*args, **kwargs):
    return _call_module_func(_load_alpha_vantage_module, "get_stock", *args, **kwargs)


def _get_alpha_vantage_indicator(*args, **kwargs):
    return _call_module_func(_load_alpha_vantage_module, "get_indicator", *args, **kwargs)


def _get_alpha_vantage_fundamentals(*args, **kwargs):
    return _call_module_func(_load_alpha_vantage_module, "get_fundamentals", *args, **kwargs)


def _get_alpha_vantage_balance_sheet(*args, **kwargs):
    return _call_module_func(_load_alpha_vantage_module, "get_balance_sheet", *args, **kwargs)


def _get_alpha_vantage_cashflow(*args, **kwargs):
    return _call_module_func(_load_alpha_vantage_module, "get_cashflow", *args, **kwargs)


def _get_alpha_vantage_income_statement(*args, **kwargs):
    return _call_module_func(_load_alpha_vantage_module, "get_income_statement", *args, **kwargs)


def _get_alpha_vantage_news(*args, **kwargs):
    return _call_module_func(_load_alpha_vantage_module, "get_news", *args, **kwargs)


def _get_alpha_vantage_global_news(*args, **kwargs):
    return _call_module_func(_load_alpha_vantage_module, "get_global_news", *args, **kwargs)


def _get_alpha_vantage_insider_transactions(*args, **kwargs):
    return _call_module_func(_load_alpha_vantage_module, "get_insider_transactions", *args, **kwargs)


def _get_yfinance_news(*args, **kwargs):
    return _call_module_func(_load_yfinance_news_module, "get_news_yfinance", *args, **kwargs)


def _get_yfinance_global_news(*args, **kwargs):
    return _call_module_func(_load_yfinance_news_module, "get_global_news_yfinance", *args, **kwargs)


def _get_a_share_news(*args, **kwargs):
    return _call_module_func(_load_a_share_news_module, "get_a_share_news", *args, **kwargs)


def _get_a_share_global_news(*args, **kwargs):
    return _call_module_func(_load_a_share_news_module, "get_a_share_global_news", *args, **kwargs)


def _get_a_share_company_announcements(*args, **kwargs):
    return _call_module_func(_load_a_share_news_module, "get_a_share_company_announcements", *args, **kwargs)


# Mapping of methods to their vendor-specific implementations
VENDOR_METHODS = {
    # core_stock_apis
    "get_stock_data": {
        "alpha_vantage": _get_alpha_vantage_stock,
        "yfinance": _get_yfinance_stock_data,
        "a_share": _get_a_share_stock,
    },
    # technical_indicators
    "get_indicators": {
        "alpha_vantage": _get_alpha_vantage_indicator,
        "yfinance": _get_yfinance_indicators,
        "a_share": _get_a_share_indicators,
    },
    # fundamental_data
    "get_fundamentals": {
        "alpha_vantage": _get_alpha_vantage_fundamentals,
        "yfinance": _get_yfinance_fundamentals,
        "a_share": _get_a_share_fundamentals,
    },
    "get_balance_sheet": {
        "alpha_vantage": _get_alpha_vantage_balance_sheet,
        "yfinance": _get_yfinance_balance_sheet,
        "a_share": _get_a_share_balance_sheet,
    },
    "get_cashflow": {
        "alpha_vantage": _get_alpha_vantage_cashflow,
        "yfinance": _get_yfinance_cashflow,
        "a_share": _get_a_share_cashflow,
    },
    "get_income_statement": {
        "alpha_vantage": _get_alpha_vantage_income_statement,
        "yfinance": _get_yfinance_income_statement,
        "a_share": _get_a_share_income_statement,
    },
    # news_data
    "get_news": {
        "alpha_vantage": _get_alpha_vantage_news,
        "yfinance": _get_yfinance_news,
        "a_share": _get_a_share_news,
    },
    "get_global_news": {
        "yfinance": _get_yfinance_global_news,
        "alpha_vantage": _get_alpha_vantage_global_news,
        "a_share": _get_a_share_global_news,
    },
    "get_insider_transactions": {
        "alpha_vantage": _get_alpha_vantage_insider_transactions,
        "yfinance": _get_yfinance_insider_transactions,
    },
    "get_company_announcements": {
        "a_share": _get_a_share_company_announcements,
    },
}


def get_category_for_method(method: str) -> str:
    """Get the category that contains the specified method."""
    for category, info in TOOLS_CATEGORIES.items():
        if method in info["tools"]:
            return category
    raise ValueError(f"Method '{method}' not found in any category")


def get_vendor(category: str, method: str = None) -> str:
    """Get the configured vendor for a data category or specific tool method.
    Tool-level configuration takes precedence over category-level.
    """
    config = get_config()

    # Check tool-level configuration first (if method provided)
    if method:
        tool_vendors = config.get("tool_vendors", {})
        if method in tool_vendors:
            return tool_vendors[method]

    # Fall back to category-level configuration
    return config.get("data_vendors", {}).get(category, "default")


def route_to_vendor(method: str, *args, **kwargs):
    """Route method calls to appropriate vendor implementation with fallback support."""
    category = get_category_for_method(method)
    vendor_config = get_vendor(category, method)
    primary_vendors = [v.strip() for v in vendor_config.split(',')]

    if method not in VENDOR_METHODS:
        raise ValueError(f"Method '{method}' not supported")

    # Build fallback chain: primary vendors first, then remaining available vendors
    all_available_vendors = list(VENDOR_METHODS[method].keys())
    fallback_vendors = primary_vendors.copy()
    for vendor in all_available_vendors:
        if vendor not in fallback_vendors:
            fallback_vendors.append(vendor)

    for vendor in fallback_vendors:
        if vendor not in VENDOR_METHODS[method]:
            continue

        vendor_impl = VENDOR_METHODS[method][vendor]
        impl_func = vendor_impl[0] if isinstance(vendor_impl, list) else vendor_impl

        try:
            return impl_func(*args, **kwargs)
        except AlphaVantageRateLimitError:
            continue  # Only rate limits trigger fallback

    raise RuntimeError(f"No available vendor for '{method}'")

"""
货币 / 日期 / 数字格式化工具。

优先使用手动格式化（可靠，无全局状态副作用）；
当 locale 模块可用时尝试 locale-aware 格式化。
"""

from __future__ import annotations

from datetime import date, datetime

# ── 语言代码 → locale 映射表 ────────────────────────────────────────────

LOCALE_MAP: dict[str, str] = {
    "zh": "zh_CN",
    "zh-cn": "zh_CN",
    "zh-CN": "zh_CN",
    "zh-tw": "zh_TW",
    "zh-TW": "zh_TW",
    "en": "en_US",
    "en-us": "en_US",
    "en-US": "en_US",
    "ja": "ja_JP",
    "ja-jp": "ja_JP",
    "ja-JP": "ja_JP",
    "ko": "ko_KR",
    "ko-kr": "ko_KR",
    "ko-KR": "ko_KR",
}

# ── 货币符号表 ─────────────────────────────────────────────────────────

CURRENCY_SYMBOLS: dict[str, str] = {
    "CNY": "¥",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "KRW": "₩",
    "HKD": "HK$",
    "TWD": "NT$",
    "SGD": "S$",
    "AUD": "A$",
    "CAD": "C$",
    "INR": "₹",
    "RUB": "₽",
    "BRL": "R$",
}


def detect_locale(lang: str) -> str:
    """语言代码到 locale 字符串的转换。

    Args:
        lang: 语言代码，如 ``"zh"``, ``"zh-CN"``, ``"en"``。

    Returns:
        对应的 locale 字符串，如 ``"zh_CN"``, ``"en_US"``。
        若无匹配则返回 ``"en_US"``。
    """
    return LOCALE_MAP.get(lang, "en_US")


# ── 货币格式化 ─────────────────────────────────────────────────────────


def format_currency(
    amount: float | int,
    currency: str = "CNY",
    locale: str = "zh-CN",
) -> str:
    """格式化货币金额（千分位 + 货币符号）。

    Args:
        amount:   金额数值（元，非分）。
        currency: 货币代码，如 ``"CNY"``, ``"USD"``。
        locale:   locale 字符串，如 ``"zh-CN"``, ``"en-US"``。

    Returns:
        格式化后的货币字符串，如 ``"¥12,345.67"``。
    """
    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    if currency in ("JPY", "KRW"):
        return f"{symbol}{int(round(amount)):,}"
    return f"{symbol}{amount:,.2f}"


# ── 日期格式化 ─────────────────────────────────────────────────────────


def format_date(
    dt: datetime | date | None,
    locale: str = "zh-CN",
) -> str:
    """格式化日期。

    Args:
        dt:     日期时间对象。若为 ``None`` 返回空字符串。
        locale: 语言 locale，如 ``"zh-CN"`` 或 ``"en-US"``。

    Returns:
        格式化后的日期字符串，格式为 ``"YYYY-MM-DD"``。
    """
    if dt is None:
        return ""
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d")
    return dt.strftime("%Y-%m-%d")


# ── 数字格式化 ─────────────────────────────────────────────────────────


def format_number(num: float | int, locale: str = "zh-CN") -> str:
    """格式化数字（千分位）。

    Args:
        num:    待格式化的数字。
        locale: locale 字符串。

    Returns:
        千分位格式的字符串，如 ``"12,345,678"``。
    """
    return f"{num:,}"

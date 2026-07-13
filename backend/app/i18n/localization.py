"""
日期 / 货币 / 数字本地化格式化模块
====================================

支持三种 locale 的格式化:
  - zh-CN: YYYY年MM月DD日, ¥1,234.56, 1,234.56
  - en-US: MM/DD/YYYY, $1,234.56, 1,234.56
  - ja-JP: YYYY年MM月DD日, ¥1,234.56, 1,234.56
  - de-DE: DD.MM.YYYY, €1.234,56, 1.234,56

用法:
    from app.i18n.localization import format_date, format_currency, format_number, get_locale_config

    formatter = get_locale_config("zh-CN")
    formatter.format_date(datetime.now())       # "2026年07月02日"
    formatter.format_currency(12345.67)         # "¥12,345.67"
    formatter.format_number(1234.56)            # "1,234.56"
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


# ═══════════════════════════════════════════════════════════════
# locale 配置定义
# ═══════════════════════════════════════════════════════════════

LOCALE_DATE_FORMATS: dict[str, str] = {
    "zh-CN": "%Y年%m月%d日",
    "en-US": "%m/%d/%Y",
    "ja-JP": "%Y年%m月%d日",
    "de-DE": "%d.%m.%Y",
    "fr-FR": "%d/%m/%Y",
    "ko-KR": "%Y년 %m월 %d일",
    "zh-TW": "%Y年%m月%d日",
}

LOCALE_CURRENCY_SYMBOLS: dict[str, str] = {
    "zh-CN": "¥",
    "en-US": "$",
    "ja-JP": "¥",
    "de-DE": "€",
    "fr-FR": "€",
    "ko-KR": "₩",
    "zh-TW": "NT$",
}

LOCALE_CURRENCY_CODES: dict[str, str] = {
    "zh-CN": "CNY",
    "en-US": "USD",
    "ja-JP": "JPY",
    "de-DE": "EUR",
    "fr-FR": "EUR",
    "ko-KR": "KRW",
    "zh-TW": "TWD",
}

# 数字格式: (千分位分隔符, 小数点)
# 欧洲使用逗号作小数点、句点作千分位
LOCALE_NUMBER_FORMATS: dict[str, tuple[str, str]] = {
    "zh-CN": (",", "."),   # 1,234.56
    "en-US": (",", "."),   # 1,234.56
    "ja-JP": (",", "."),   # 1,234.56
    "de-DE": (".", ","),   # 1.234,56
    "fr-FR": (" ", ","),   # 1 234,56
    "ko-KR": (",", "."),   # 1,234.56
    "zh-TW": (",", "."),   # 1,234.56
}

# 零金额特殊处理 (JPY/KRW 无小数位)
LOCALE_NO_DECIMAL: set[str] = {
    "ja-JP",
    "ko-KR",
}

# locale 显示名称
LOCALE_LABELS: dict[str, str] = {
    "zh-CN": "中文（中国）",
    "en-US": "English (US)",
    "ja-JP": "日本語（日本）",
    "de-DE": "Deutsch (Deutschland)",
    "fr-FR": "Français (France)",
    "ko-KR": "한국어 (대한민국)",
    "zh-TW": "中文（台灣）",
}

# locale → 关联的语言代码 (用于 i18n 翻译)
LOCALE_TO_LANG: dict[str, str] = {
    "zh-CN": "zh",
    "en-US": "en",
    "ja-JP": "ja",
    "de-DE": "de",
    "fr-FR": "fr",
    "ko-KR": "ko",
    "zh-TW": "zh",
}


# ═══════════════════════════════════════════════════════════════
# LocaleFormatter — 单个 locale 的格式化器
# ═══════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class LocaleFormatter:
    """针对单个 locale 的格式化配置"""

    locale: str
    label: str
    lang: str

    date_format: str = "%Y-%m-%d"
    currency_symbol: str = "¥"
    currency_code: str = "CNY"
    thousands_sep: str = ","
    decimal_sep: str = "."
    no_decimals: bool = False

    def format_date(self, dt: datetime | date | None) -> str:
        """格式化日期

        Args:
            dt: 日期/时间对象。None 返回空字符串。

        Returns:
            按 locale 格式化的日期字符串
        """
        if dt is None:
            return ""
        if isinstance(dt, datetime):
            return dt.strftime(self.date_format)
        return dt.strftime(self.date_format)

    def format_datetime(self, dt: datetime | None, include_time: bool = True) -> str:
        """格式化日期时间

        Args:
            dt: datetime 对象。None 返回空字符串。
            include_time: 是否包含时间部分

        Returns:
            按 locale 格式化的日期时间字符串
        """
        if dt is None:
            return ""
        date_part = dt.strftime(self.date_format)
        if include_time:
            time_part = dt.strftime(" %H:%M:%S")
            return date_part + time_part
        return date_part

    def format_currency(self, amount: float | int) -> str:
        """格式化货币金额

        Args:
            amount: 金额数值（元，非分）

        Returns:
            带货币符号和千分位的字符串，如 "¥12,345.67"
        """
        if self.no_decimals:
            amount_int = int(round(amount))
            formatted = self._format_number(amount_int, decimals=0)
        else:
            formatted = self._format_number(amount, decimals=2)
        return f"{self.currency_symbol}{formatted}"

    def format_number(self, num: float | int, decimals: Optional[int] = None) -> str:
        """格式化数字

        Args:
            num: 待格式化数字
            decimals: 小数位数，None 则智能保留

        Returns:
            按 locale 格式化的数字字符串
        """
        if decimals is not None:
            return self._format_number(num, decimals=decimals)
        if isinstance(num, int):
            return self._format_number(num, decimals=0)
        return self._format_number(num, decimals=2)

    def _format_number(self, num: float | int, decimals: int = 0) -> str:
        """内部数字格式化 — 处理千分位与小数点"""
        # 分离整数部分和小数部分
        if decimals > 0:
            formatted_float = f"{num:.{decimals}f}"
            int_part_str, dec_part_str = formatted_float.split(".")
        else:
            int_part_str = str(int(round(num)))
            dec_part_str = ""

        # 千分位格式化整数部分
        neg = False
        if int_part_str.startswith("-"):
            neg = True
            int_part_str = int_part_str[1:]

        # 从右往左每三位加分隔符
        groups = []
        for i in range(len(int_part_str), 0, -3):
            start = max(0, i - 3)
            groups.insert(0, int_part_str[start:i])
        int_part_grouped = self.thousands_sep.join(groups)

        if neg:
            int_part_grouped = "-" + int_part_grouped

        if dec_part_str:
            return f"{int_part_grouped}{self.decimal_sep}{dec_part_str}"
        return int_part_grouped


# ═══════════════════════════════════════════════════════════════
# 格式化器注册表
# ═══════════════════════════════════════════════════════════════

# 缓存已创建的 LocaleFormatter 实例
_formatters: dict[str, LocaleFormatter] = {}


def get_locale_formatter(locale: str = "zh-CN") -> LocaleFormatter:
    """获取指定 locale 的格式化器

    Args:
        locale: 完整的 locale 代码，如 "zh-CN", "en-US", "ja-JP"

    Returns:
        LocaleFormatter 实例

    Raises:
        ValueError: 不支持的 locale
    """
    if locale in _formatters:
        return _formatters[locale]

    # 查找或兜底
    date_fmt = LOCALE_DATE_FORMATS.get(locale)
    if date_fmt is None:
        # 尝试只匹配语言部分 (如 "zh" → "zh-CN")
        for key in LOCALE_DATE_FORMATS:
            if key.startswith(locale.split("-")[0]):
                locale = key
                date_fmt = LOCALE_DATE_FORMATS[key]
                break
        else:
            raise ValueError(
                f"Unsupported locale '{locale}'. "
                f"Supported: {', '.join(sorted(LOCALE_DATE_FORMATS.keys()))}"
            )

    currency_symbol = LOCALE_CURRENCY_SYMBOLS.get(locale, "¥")
    currency_code = LOCALE_CURRENCY_CODES.get(locale, "CNY")
    thousands_sep, decimal_sep = LOCALE_NUMBER_FORMATS.get(locale, (",", "."))
    no_decimals = locale in LOCALE_NO_DECIMAL
    label = LOCALE_LABELS.get(locale, locale)
    lang = LOCALE_TO_LANG.get(locale, locale.split("-")[0])

    formatter = LocaleFormatter(
        locale=locale,
        label=label,
        lang=lang,
        date_format=date_fmt,
        currency_symbol=currency_symbol,
        currency_code=currency_code,
        thousands_sep=thousands_sep,
        decimal_sep=decimal_sep,
        no_decimals=no_decimals,
    )
    _formatters[locale] = formatter
    return formatter


# ═══════════════════════════════════════════════════════════════
# 快捷函数
# ═══════════════════════════════════════════════════════════════


def format_date(dt: datetime | date | None, locale: str = "zh-CN") -> str:
    """快捷：日期格式化"""
    return get_locale_formatter(locale).format_date(dt)


def format_datetime(dt: datetime | None, locale: str = "zh-CN", include_time: bool = True) -> str:
    """快捷：日期时间格式化"""
    return get_locale_formatter(locale).format_datetime(dt, include_time=include_time)


def format_currency(amount: float | int, locale: str = "zh-CN") -> str:
    """快捷：货币格式化"""
    return get_locale_formatter(locale).format_currency(amount)


def format_number(num: float | int, locale: str = "zh-CN", decimals: Optional[int] = None) -> str:
    """快捷：数字格式化"""
    return get_locale_formatter(locale).format_number(num, decimals)


def get_locale_config(locale: str) -> LocaleFormatter:
    """获取 locale 完整配置（与 get_locale_formatter 同义）"""
    return get_locale_formatter(locale)


def get_supported_locales() -> list[dict[str, str]]:
    """获取所有支持的 locale 列表"""
    locales = []
    for code in sorted(LOCALE_DATE_FORMATS.keys()):
        locales.append({
            "code": code,
            "label": LOCALE_LABELS.get(code, code),
            "lang": LOCALE_TO_LANG.get(code, code.split("-")[0]),
            "date_format": LOCALE_DATE_FORMATS[code],
            "currency_symbol": LOCALE_CURRENCY_SYMBOLS.get(code, "¥"),
            "currency_code": LOCALE_CURRENCY_CODES.get(code, ""),
        })
    return locales

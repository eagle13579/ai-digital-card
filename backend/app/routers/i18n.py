"""
AI数字名片 翻译API端点

提供 /api/i18n/translations 和 /api/i18n/locales 接口。
"""

from fastapi import APIRouter, Query

from app.i18n import TRANSLATIONS
from datetime import datetime, date
from typing import Union

from app.i18n.localization import (
    get_locale_formatter,
    get_supported_locales,
)

router = APIRouter(prefix="/api/i18n", tags=["i18n"])

# 所有支持的语言
LOCALES = {"zh", "en", "ja", "ko", "es", "fr", "de", "pt", "ru", "ar", "th", "vi"}

# RTL 语言列表
RTL_LOCALES = {"ar", "he", "fa", "ur"}

# 语言显示名称
LOCALE_LABELS = {
    "zh": "中文",
    "en": "English",
    "ja": "日本語",
    "ko": "한국어",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "pt": "Português",
    "ru": "Русский",
    "ar": "العربية",
    "th": "ไทย",
    "vi": "Tiếng Việt",
}


@router.get("/translations")
def get_translations(
    locale: str = Query(default=None, description="语言代码，不传则返回全部"),
):
    """
    返回当前支持的所有语言的翻译字典。

    - 省略 locale 参数时，返回 { locale: { key: value, ... }, ... }
    - 指定 locale 时，返回 { locale: "zh", translations: { key: "值", ... } }
    """
    if locale:
        # 验证 locale 是否支持
        if locale not in LOCALES:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail=f"Unsupported locale '{locale}'; supported: {', '.join(sorted(LOCALES))}")

        flat: dict[str, str] = {}
        for key, entry in TRANSLATIONS.items():
            flat[key] = entry.get(locale, entry.get("en", key))

        return {"locale": locale, "translations": flat}

    # 不传 locale → 返回所有语言的完整翻译树
    result: dict[str, dict[str, str]] = {}
    for loc in sorted(LOCALES):
        loc_dict: dict[str, str] = {}
        for key, entry in TRANSLATIONS.items():
            loc_dict[key] = entry.get(loc, entry.get("en", key))
        result[loc] = loc_dict

    return result


@router.get("/locale/{locale}")
def get_locale_formatting(locale: str):
    """获取指定 locale 的日期/货币/数字格式化配置

    返回该 locale 的完整格式化配置，以及演示示例值。

    Args:
        locale: 完整 locale 代码，如 ``zh-CN``, ``en-US``, ``ja-JP``, ``de-DE``

    Returns:
        {
          "code": 200,
          "data": {
            "locale": "zh-CN",
            "label": "中文（中国）",
            "lang": "zh",
            "formats": {
              "date": "%Y年%m月%d日",
              "currency": "¥",
              "number": ["1,234.56", "1,234"]
            },
            "examples": {
              "date": "2026年07月02日",
              "datetime": "2026年07月02日 14:30:00",
              "currency": "¥12,345.67",
              "number": "1,234.56"
            }
          }
        }

    Raises:
        HTTPException 400: 不支持的 locale
    """
    try:
        fmt = get_locale_formatter(locale)
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    # 生成示例值
    now = datetime(2026, 7, 2, 14, 30, 0)

    return {
        "code": 200,
        "data": {
            "locale": fmt.locale,
            "label": fmt.label,
            "lang": fmt.lang,
            "formats": {
                "date": fmt.date_format,
                "currency": fmt.currency_symbol,
                "currency_code": fmt.currency_code,
                "thousands_separator": fmt.thousands_sep,
                "decimal_separator": fmt.decimal_sep,
            },
            "examples": {
                "date": fmt.format_date(now),
                "datetime": fmt.format_datetime(now),
                "currency": fmt.format_currency(12345.67),
                "number": fmt.format_number(1234.56),
                "number_int": fmt.format_number(1234),
            },
        },
    }


@router.get("/locales")
def get_locales():
    """
    返回所有支持的语言元数据，包含 RTL 标记和显示名称。
    """
    return {
        "locales": sorted(LOCALES),
        "rtl_locales": sorted(RTL_LOCALES),
        "details": {
            lang: {
                "label": LOCALE_LABELS.get(lang, lang),
                "dir": "rtl" if lang in RTL_LOCALES else "ltr",
            }
            for lang in sorted(LOCALES)
        },
    }

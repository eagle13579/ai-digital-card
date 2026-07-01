"""
AI数字名片 翻译API端点

提供 /api/i18n/translations 接口，返回前端所需的全部翻译字典。
前端可直接缓存使用。
"""

from fastapi import APIRouter, Query

from app.i18n import TRANSLATIONS

router = APIRouter(prefix="/api/i18n", tags=["i18n"])

LOCALES = {"zh", "en"}


@router.get("/translations")
def get_translations(
    locale: str = Query(default=None, description="语言代码 (zh/en)，不传则返回全部"),
):
    """
    返回当前支持的所有语言的翻译字典。

    - 省略 locale 参数时，返回 { locale: { key: value, ... }, ... }
    - 指定 locale (zh/en) 时，返回 { locale: "zh", translations: { key: "值", ... } }
    """
    if locale:
        # 验证 locale 是否支持
        if locale not in LOCALES:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail=f"Unsupported locale '{locale}'; supported: {', '.join(sorted(LOCALES))}")

        flat: dict[str, str] = {}
        for key, entry in TRANSLATIONS.items():
            flat[key] = entry.get(locale, entry.get("zh", key))

        return {"locale": locale, "translations": flat}

    # 不传 locale → 返回所有语言的完整翻译树
    result: dict[str, dict[str, str]] = {}
    for loc in sorted(LOCALES):
        loc_dict: dict[str, str] = {}
        for key, entry in TRANSLATIONS.items():
            loc_dict[key] = entry.get(loc, entry.get("zh", key))
        result[loc] = loc_dict

    return result

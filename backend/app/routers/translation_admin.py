"""
自动翻译管理平台 — Web 管理 API
=================================

提供翻译管理 Web API：
  - GET    /api/admin/translations            — 列出所有翻译 key 及各语言状态
  - POST   /api/admin/translations/auto-translate — 触发 DeepSeek 自动翻译
  - PUT    /api/admin/translations/{key}      — 人工修正某条翻译
  - GET    /api/admin/translations/stats      — 翻译覆盖率统计
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.services.translation_service import (
    LANG_NAMES,
    auto_translate,
    get_translation_stats,
    list_all_keys_with_status,
    update_single_translation,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/translations", tags=["Translation Admin"])


@router.get("")
async def admin_list_translations(
    lang: Optional[str] = Query(None, description="按语言过滤（仅返回该语言缺失的 key）"),
    missing_only: bool = Query(False, description="仅返回缺失翻译的 key"),
    context: Optional[str] = Query(None, description="按 section 上下文过滤"),
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(50, ge=1, le=500, description="每页条数"),
):
    """列出所有翻译 key 及每个语言的状态"""
    keys = list_all_keys_with_status()
    if not keys:
        return {"total": 0, "items": [], "page": page, "per_page": per_page}

    # 过滤
    filtered = keys
    if lang:
        filtered = [k for k in filtered if not k["languages"].get(lang)]
    if missing_only:
        # 任一非 zh 语言缺失即算缺失
        non_zh = [l for l in LANG_NAMES if l != "zh"]
        filtered = [
            k for k in filtered
            if any(not k["languages"].get(l) for l in non_zh)
        ]
    if context:
        filtered = [k for k in filtered if context.lower() in k["context"].lower()]

    total = len(filtered)
    offset = (page - 1) * per_page
    items = filtered[offset : offset + per_page]

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": items,
    }


@router.get("/stats")
async def admin_translation_stats():
    """翻译覆盖率统计 — 每语言完成百分比"""
    stats = get_translation_stats()
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="无法解析翻译文件，请检查 backend/app/i18n/__init__.py",
        )

    overall_total = 0
    overall_translated = 0
    for s in stats.values():
        overall_total = s["total"]
        overall_translated += s["translated"]

    overall_pct = round(
        overall_translated / (overall_total * len(stats)) * 100, 1
    ) if overall_total > 0 else 0.0

    return {
        "overall": {
            "total_keys": overall_total,
            "total_translations": overall_translated,
            "total_expected": overall_total * len(stats),
            "completion_pct": overall_pct,
        },
        "languages": sorted(stats.values(), key=lambda x: x["completion_pct"]),
    }


@router.post("/auto-translate")
async def admin_auto_translate(
    langs: Optional[str] = Query(None, description="目标语言，逗号分隔，默认所有非 zh 语言"),
    incremental_only: bool = Query(True, description="仅翻译缺失 key"),
    dry_run: bool = Query(False, description="预览模式（不调用 API 不写入）"),
):
    """触发 DeepSeek 自动翻译"""
    target_langs = (
        [l.strip() for l in langs.split(",") if l.strip()]
        if langs
        else None
    )

    try:
        results = auto_translate(
            target_langs=target_langs,
            incremental_only=incremental_only,
            dry_run=dry_run,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    summary = {}
    total_translated = 0
    total_failed = 0

    for lang_code, result in results.items():
        summary[lang_code] = {
            "lang_name": LANG_NAMES.get(lang_code, lang_code),
            "total_keys": result.total_keys,
            "existing_keys": result.existing_keys,
            "translated_keys": result.translated_keys,
            "failed_keys": result.failed_keys,
            "failed_details": result.failed_details,
            "elapsed_seconds": round(result.elapsed, 1),
        }
        total_translated += result.translated_keys
        total_failed += result.failed_keys

    return {
        "success": total_failed == 0,
        "total_translated": total_translated,
        "total_failed": total_failed,
        "dry_run": dry_run,
        "languages": summary,
    }


@router.put("/{key}")
async def admin_update_translation(
    key: str,
    lang: str = Query(..., description="目标语言代码，如 en, ja, ko"),
    value: str = Query(..., description="新的翻译文本"),
):
    """人工修正某条翻译"""
    if lang not in LANG_NAMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的语言代码: {lang}，支持: {', '.join(LANG_NAMES.keys())}",
        )

    success = update_single_translation(key, lang, value)
    if not success:
        # 可能是 key 不存在
        all_keys = list_all_keys_with_status()
        key_exists = any(k["key"] == key for k in all_keys)
        if not key_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"翻译 key '{key}' 不存在",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新翻译 '{key}' 失败，文件可能不匹配",
        )

    return {
        "success": True,
        "key": key,
        "lang": lang,
        "value": value,
        "message": f"翻译 '{key}' ({LANG_NAMES.get(lang, lang)}) 已更新",
    }

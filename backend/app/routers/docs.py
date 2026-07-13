"""API 文档 / 版本变更记录端点。"""

from __future__ import annotations
import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse

router = APIRouter(tags=["API 文档"])


CHANGELOG: list[dict] = [
    {
        "version": "2.0.0",
        "date": "2026-06-20",
        "changes": [
            "🎉 全新模块化架构",
            "  新增 AI 推荐、AB 测试、支付、SSO 模块",
            "  重构路由注册与中间件体系",
        ],
    },
    {
        "version": "1.2.0",
        "date": "2026-05-15",
        "changes": [
            "✅ 访客追踪与信任网络",
            "  新增访客记录 /api/visitor/*",
            "  新增信任网络 /api/trust/*",
        ],
    },
    {
        "version": "1.1.0",
        "date": "2026-04-01",
        "changes": [
            "🚀 多语言与分享功能",
            "  新增国际化 /api/i18n/*",
            "  新增分享 /api/share/*",
        ],
    },
    {
        "version": "1.0.0",
        "date": "2026-03-01",
        "changes": [
            "📌 初始发布",
            "  用户认证、名片管理、标签匹配",
        ],
    },
]


@router.get("/docs", include_in_schema=False)
async def redirect_to_swagger():
    """重定向到 FastAPI Swagger UI。"""
    return RedirectResponse(url="/docs")


@router.get("/api/changelog", summary="API 版本变更日志")
async def get_changelog():
    """返回 API 版本历史和变更记录。"""
    return JSONResponse(
        content={
            "latest_version": CHANGELOG[0]["version"],
            "changelog": CHANGELOG,
        }
    )


@router.get("/api/openapi.yaml", summary="导出 OpenAPI 规范文件 (YAML)")
async def get_openapi_yaml():
    """返回完整的 OpenAPI 3.0 规范 YAML 文件。"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    yaml_path = os.path.join(base_dir, "openapi.yaml")
    if os.path.exists(yaml_path):
        return FileResponse(
            path=yaml_path,
            media_type="text/yaml",
            filename="openapi.yaml",
            headers={"Content-Disposition": 'inline; filename="openapi.yaml"'},
        )
    return JSONResponse(
        status_code=404,
        content={"error": "openapi.yaml 文件未找到，请运行生成脚本"},
    )

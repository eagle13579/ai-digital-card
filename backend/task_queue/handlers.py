"""默认任务处理器实现 — 名片AI扫描/匹配/通知/导出。

这些是骨架/参考实现。实际生产环境中应由具体业务服务层
（如 app/services/ 下的模块）替换或扩展这些处理器。
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def handle_scan_card(ctx: dict[str, Any]) -> dict[str, Any]:
    """名片AI扫描/OCR 处理任务。

    Payload 结构:
        card_id: str          — 名片记录 ID
        image_url: str        — 原始图片 URL 或本地路径
        user_id: str          — 提交扫描的用户 ID
        options: dict | None  — 额外选项（语言、模型等）

    Returns:
        dict — OCR 结果, 包含 text, fields, confidence 等。
    """
    card_id = ctx.get("card_id", "unknown")
    image_url = ctx.get("image_url", "")
    user_id = ctx.get("user_id", "")

    logger.info(
        "[SCAN_CARD] Processing card %s for user %s (image: %s)",
        card_id,
        user_id,
        image_url,
    )

    # ── TODO: 调用实际 AI 扫描服务 ──────────────────────────────────
    # from app.services.card_scanner import scan_business_card
    # result = await scan_business_card(image_url, options=ctx.get("options"))

    # 模拟处理耗时
    import asyncio
    await asyncio.sleep(0.5)

    result = {
        "card_id": card_id,
        "status": "processed",
        "text": "示例OCR文本内容",
        "fields": {
            "name": "张三",
            "company": "示例科技有限公司",
            "title": "技术总监",
            "phone": "13800138000",
            "email": "zhangsan@example.com",
        },
        "confidence": 0.95,
    }

    logger.info("[SCAN_CARD] Card %s processed successfully", card_id)
    return result


async def handle_match_request(ctx: dict[str, Any]) -> dict[str, Any]:
    """名片匹配请求处理任务。

    Payload 结构:
        match_id: str         — 匹配请求 ID
        source_card_id: str   — 源名片 ID
        target_card_ids: list — 待匹配的目标名片 ID 列表
        user_id: str          — 发起匹配的用户 ID
        threshold: float      — 匹配阈值 (0-1)

    Returns:
        dict — 匹配结果列表。
    """
    match_id = ctx.get("match_id", "unknown")
    source_card_id = ctx.get("source_card_id", "")
    target_ids = ctx.get("target_card_ids", [])
    user_id = ctx.get("user_id", "")

    logger.info(
        "[MATCH_REQUEST] Processing match %s for user %s (source: %s, targets: %d)",
        match_id,
        user_id,
        source_card_id,
        len(target_ids),
    )

    # ── TODO: 调用实际匹配引擎 ───────────────────────────────────────
    # from app.services.matching_engine import match_cards
    # results = await match_cards(source_card_id, target_ids, threshold=...)

    import asyncio
    await asyncio.sleep(0.3)

    result = {
        "match_id": match_id,
        "status": "completed",
        "matches": [],
        "total_candidates": len(target_ids),
    }

    logger.info("[MATCH_REQUEST] Match %s completed (0 matches found)", match_id)
    return result


async def handle_send_notification(ctx: dict[str, Any]) -> dict[str, Any]:
    """通知推送任务（邮件/IM/站内信）。

    Payload 结构:
        notification_id: str       — 通知记录 ID
        user_id: str               — 目标用户 ID
        channel: str               — 渠道 (email/sms/wechat/slack/feishu/dingtalk/in_app)
        subject: str               — 主题
        body: str                  — 正文
        template_id: str | None    — 模板 ID
        template_data: dict | None — 模板变量
        attachments: list | None   — 附件

    Returns:
        dict — 发送结果。
    """
    notification_id = ctx.get("notification_id", "unknown")
    user_id = ctx.get("user_id", "")
    channel = ctx.get("channel", "in_app")
    subject = ctx.get("subject", "")

    logger.info(
        "[SEND_NOTIFICATION] Sending '%s' via %s to user %s (notif_id: %s)",
        subject,
        channel,
        user_id,
        notification_id,
    )

    # ── TODO: 调用实际通知服务 ───────────────────────────────────────
    # if channel == "email":
    #     await email_service.send(...)
    # elif channel == "slack":
    #     await slack_service.send(...)
    # ...

    import asyncio
    await asyncio.sleep(0.2)

    result = {
        "notification_id": notification_id,
        "channel": channel,
        "status": "sent",
        "user_id": user_id,
    }

    logger.info(
        "[SEND_NOTIFICATION] Notification %s sent via %s",
        notification_id,
        channel,
    )
    return result


async def handle_export_data(ctx: dict[str, Any]) -> dict[str, Any]:
    """数据导出任务（CSV/Excel/PDF）。

    Payload 结构:
        export_id: str         — 导出请求 ID
        user_id: str           — 请求导出的用户 ID
        export_type: str       — 导出格式 (csv/excel/pdf)
        entity_type: str       — 导出实体类型 (cards/contacts/analytics)
        filters: dict          — 过滤条件
        output_path: str       — 输出文件路径

    Returns:
        dict — 导出结果，包含文件路径和统计。
    """
    export_id = ctx.get("export_id", "unknown")
    user_id = ctx.get("user_id", "")
    export_type = ctx.get("export_type", "csv")
    entity_type = ctx.get("entity_type", "cards")
    output_path = ctx.get("output_path", "")

    logger.info(
        "[EXPORT_DATA] Exporting %s as %s for user %s (export_id: %s)",
        entity_type,
        export_type,
        user_id,
        export_id,
    )

    # ── TODO: 调用实际导出服务 ───────────────────────────────────────
    # from app.services.exporter import export_entity
    # file_path = await export_entity(entity_type, export_type, filters)

    import asyncio
    await asyncio.sleep(1.0)

    result = {
        "export_id": export_id,
        "export_type": export_type,
        "entity_type": entity_type,
        "status": "completed",
        "output_path": output_path or f"/tmp/exports/{export_id}.{export_type}",
        "record_count": 0,
        "file_size_bytes": 0,
    }

    logger.info(
        "[EXPORT_DATA] Export %s completed (%s format, %s)",
        export_id,
        export_type,
        entity_type,
    )
    return result

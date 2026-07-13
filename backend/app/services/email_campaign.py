"""邮件营销 — Campaign 创建、筛选、分批发送、追踪像素、退订、统计。

依赖:
  - app.services.email_service.email_service  (发送邮件)
  - app.services.email_templates               (模板函数)
  - app.crm.crm_models.CrmCampaign / CrmCampaignRecipient
  - app.crm.crm_models.CrmContact              (筛选目标人群)
  - app.database.get_db                        (异步 session)
  - app.config.settings.BASE_URL               (生成追踪链接)

功能:
  1. Campaign CRUD (创建 / 列表 / 详情)
  2. 按 tags / pipeline_stage_ids / sources / created_at 筛选联系人
  3. 分批发送 (每批 50 封，间隔 5 秒)
  4. 嵌入追踪像素 (1×1 透明 GIF) → 记录打开事件
  5. 嵌入退订链接 → 记录退订事件
  6. 统计: 发送数 / 打开数 / 退订数
"""

from __future__ import annotations

import asyncio
import json
import logging
import secrets

from sqlalchemy import case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.crm.crm_models import CrmCampaign, CrmCampaignRecipient, CrmContact

logger = logging.getLogger(__name__)

# ── 分批发送配置 ──────────────────────────────────────────────────────────────────

BATCH_SIZE = 50          # 每批发送数量
BATCH_INTERVAL = 5       # 每批间隔秒数 (防封)

# ── 追踪像素 (1×1 透明 GIF) ───────────────────────────────────────────────────────

_TRACKING_PIXEL_BYTES = (
    b"\x47\x49\x46\x38\x39\x61"  # GIF89a
    b"\x01\x00\x01\x00"          # 1x1 pixel
    b"\x80\x00\x00"              # global color table
    b"\xff\xff\xff\x00\x00\x00"  # color map
    b"\x21\xf9\x04\x00\x00\x00\x00\x00"
    b"\x2c\x00\x00\x00\x00"
    b"\x01\x00\x01\x00"
    b"\x00\x02\x02\x44\x01\x00\x3b"
)

# ── 模板函数名白名单 ──────────────────────────────────────────────────────────────

_ALLOWED_TEMPLATES = {
    "welcome_html",
    "trial_expiring_3d_html",
    "trial_expiring_1d_html",
    "trial_expired_html",
    "crm_new_contact_html",
    "campaign_broadcast_html",
}


# ═══════════════════════════════════════════════════════════════════════════════════
# Campaign Service
# ═══════════════════════════════════════════════════════════════════════════════════


class EmailCampaignService:
    """邮件营销服务。

    使用方法:
        svc = EmailCampaignService(db, user_id)
        campaign = await svc.create_campaign({...})
        await svc.send_campaign(campaign.id)
    """

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id

    # ── Campaign CRUD ──────────────────────────────────────────────────────────────

    async def create_campaign(self, data: dict) -> CrmCampaign:
        """创建邮件营销活动。"""
        campaign = CrmCampaign(
            owner_id=self.user_id,
            name=data["name"],
            subject=data["subject"],
            template_name=data["template_name"],
            template_params=json.dumps(data.get("template_params", {}), ensure_ascii=False),
            target_filter=json.dumps(data.get("target_filter", {}), ensure_ascii=False),
            status="draft",
        )
        self.db.add(campaign)
        await self.db.commit()
        await self.db.refresh(campaign)
        logger.info("创建营销活动 id=%s name=%s", campaign.id, campaign.name)
        return campaign

    async def get_campaign(self, campaign_id: int) -> CrmCampaign | None:
        """获取单个活动详情。"""
        from sqlalchemy import select

        result = await self.db.execute(
            select(CrmCampaign).where(
                CrmCampaign.id == campaign_id,
                CrmCampaign.owner_id == self.user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_campaigns(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[CrmCampaign], int]:
        """获取活动列表。"""
        from sqlalchemy import select, func

        query = select(CrmCampaign).where(CrmCampaign.owner_id == self.user_id)

        # 总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(CrmCampaign.updated_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        campaigns = list(result.scalars().all())

        return campaigns, total

    # ── 目标人群筛选 ──────────────────────────────────────────────────────────────

    async def get_target_contacts(self, target_filter: dict) -> list[CrmContact]:
        """根据筛选条件获取目标联系人列表 (有邮箱且有未退订记录)。

        target_filter 支持:
            tags: list[str]             — 标签交集 (联系人 tags 字段含所有标签)
            pipeline_stage_ids: list[int] — 管道阶段
            sources: list[str]           — 来源 (match/manual/visitor/import)
            created_after: str           — ISO 日期，仅含此日期后创建的联系人
            created_before: str          — ISO 日期，仅含此日期前创建的联系人
        """
        from sqlalchemy import select

        query = select(CrmContact).where(
            CrmContact.owner_id == self.user_id,
            CrmContact.email != "",
            CrmContact.email.isnot(None),
        )

        # 标签筛选 (JSON 数组包含所有指定标签)
        tags = target_filter.get("tags", [])
        if tags:
            for tag in tags:
                query = query.where(CrmContact.tags.ilike(f"%{tag}%"))

        # 管道阶段筛选
        stage_ids = target_filter.get("pipeline_stage_ids", [])
        if stage_ids:
            query = query.where(CrmContact.pipeline_stage_id.in_(stage_ids))

        # 来源筛选
        sources = target_filter.get("sources", [])
        if sources:
            query = query.where(CrmContact.source.in_(sources))

        # 创建时间范围
        after = target_filter.get("created_after")
        if after:
            query = query.where(CrmContact.created_at >= after)
        before = target_filter.get("created_before")
        if before:
            query = query.where(CrmContact.created_at <= before)

        # 排除已退订的联系人 (从 campaign_recipients 中查找该用户下所有退订记录)
        subq = (
            select(CrmCampaignRecipient.contact_id)
            .join(CrmCampaign, CrmCampaign.id == CrmCampaignRecipient.campaign_id)
            .where(
                CrmCampaign.owner_id == self.user_id,
                CrmCampaignRecipient.unsubscribed,
            )
        )
        query = query.where(CrmContact.id.notin_(subq))

        query = query.order_by(CrmContact.id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ── 分批发送 ──────────────────────────────────────────────────────────────────

    async def send_campaign(self, campaign_id: int) -> dict:
        """发送营销活动。

        流程:
          1. 验证活动状态 (必须是 draft)
          2. 从 target_filter 筛选目标联系人
          3. 创建 CrmCampaignRecipient 记录
          4. 分批发送 (每批 BATCH_SIZE=50，间隔 BATCH_INTERVAL=5s)
          5. 更新活动状态为 sent

        返回格式:
            {
                "campaign_id": int,
                "total_recipients": int,
                "sent_count": int,
                "failed_count": int,
                "errors": list[str],
            }
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            return {"error": "活动不存在", "campaign_id": campaign_id}
        if campaign.status != "draft":
            return {"error": f"活动状态不是 draft (当前: {campaign.status})", "campaign_id": campaign_id}

        # 1. 筛选目标联系人
        target_filter = json.loads(campaign.target_filter) if campaign.target_filter else {}
        contacts = await self.get_target_contacts(target_filter)
        if not contacts:
            return {"error": "没有符合条件的联系人", "campaign_id": campaign_id}

        # 2. 创建收件人记录
        logger.info("活动 %s: 目标联系人 %d 个", campaign_id, len(contacts))
        recipients = await self._create_recipients(campaign, contacts)
        if not recipients:
            return {"error": "没有有效的收件人（可能已全部发送过）", "campaign_id": campaign_id}

        # 3. 更新活动状态
        campaign.status = "sending"
        campaign.total_recipients = len(recipients)
        await self.db.commit()

        # 4. 分批发送
        sent_count = 0
        failed_count = 0
        errors = []

        from app.services.email_service import email_service
        from app.services.email_templates import campaign_broadcast_html

        base_url = settings.BASE_URL.rstrip("/")
        template_fn = _resolve_template(campaign.template_name)

        batches = [
            recipients[i : i + BATCH_SIZE] for i in range(0, len(recipients), BATCH_SIZE)
        ]
        total_batches = len(batches)

        for batch_idx, batch_recipients in enumerate(batches):
            logger.info(
                "活动 %s: 发送批 %d/%d (%d 封)",
                campaign_id,
                batch_idx + 1,
                total_batches,
                len(batch_recipients),
            )

            for recipient in batch_recipients:
                # 渲染追踪像素 HTML
                tracking_url = f"{base_url}/api/crm/track/open/{recipient.tracking_token}"
                unsubscribe_url = f"{base_url}/api/crm/unsubscribe/{recipient.tracking_token}"

                # 构建带追踪和退订的邮件 HTML
                try:
                    # 解析模板参数
                    params = json.loads(campaign.template_params) if campaign.template_params else {}
                    params.setdefault("name", recipient.name)

                    if template_fn:
                        inner_html = template_fn(**params)
                    else:
                        inner_html = f"<p>您好，{recipient.name}</p>"

                    # 用 campaign_broadcast_html 包裹（添加追踪像素 + 退订链接）
                    full_html = campaign_broadcast_html(
                        name=recipient.name,
                        subject=campaign.subject,
                        inner_body=inner_html,
                        unsubscribe_url=unsubscribe_url,
                    )

                except Exception as e:
                    logger.warning("渲染模板失败: %s", e)
                    full_html = f"<p>您好，{recipient.name}</p>"
                    full_html += _build_tracking_and_unsubscribe(tracking_url, unsubscribe_url)

                # 嵌入追踪像素（额外加到 body 尾部确保被渲染）
                pixel_img = f'<img src="{tracking_url}" width="1" height="1" style="display:none;" alt=""/>'
                full_html += pixel_img

                # 发送
                result = await email_service.send(
                    to=recipient.email,
                    subject=campaign.subject,
                    body=f"您好，{recipient.name}，请查看邮件内容。",
                    html=full_html,
                )

                if result.get("success"):
                    # 更新 recipient 发送状态
                    rec_update = await self.db.execute(
                        select(CrmCampaignRecipient).where(
                            CrmCampaignRecipient.id == recipient.id
                        )
                    )
                    rec = rec_update.scalar_one_or_none()
                    if rec:
                        rec.sent = True
                        rec.sent_at = func.now()
                    sent_count += 1
                else:
                    rec_update = await self.db.execute(
                        select(CrmCampaignRecipient).where(
                            CrmCampaignRecipient.id == recipient.id
                        )
                    )
                    rec = rec_update.scalar_one_or_none()
                    if rec:
                        rec.send_error = result.get("error", "unknown")
                    failed_count += 1
                    error_msg = result.get("error", "unknown")
                    if error_msg:
                        errors.append(f"{recipient.email}: {error_msg}")

            # 提交每批的更新
            await self.db.commit()

            # 更新活动计数
            campaign.sent_count = sent_count
            await self.db.commit()

            # 批间延迟
            if batch_idx < total_batches - 1:
                await asyncio.sleep(BATCH_INTERVAL)

        # 5. 完成
        campaign.status = "sent"
        campaign.sent_count = sent_count
        await self.db.commit()
        await self.db.refresh(campaign)

        logger.info(
            "活动 %s 发送完成: 总共 %d, 成功 %d, 失败 %d",
            campaign_id,
            len(recipients),
            sent_count,
            failed_count,
        )

        return {
            "campaign_id": campaign_id,
            "total_recipients": len(recipients),
            "sent_count": sent_count,
            "failed_count": failed_count,
            "errors": errors[:20],  # 只返回前 20 个错误
        }

    async def _create_recipients(
        self, campaign: CrmCampaign, contacts: list[CrmContact]
    ) -> list[CrmCampaignRecipient]:
        """为活动创建收件人记录（已存在的跳过）。"""
        from sqlalchemy import select

        # 查已存在的收件人
        existing_result = await self.db.execute(
            select(CrmCampaignRecipient.contact_id).where(
                CrmCampaignRecipient.campaign_id == campaign.id
            )
        )
        existing_ids = {row[0] for row in existing_result.fetchall()}

        recipients = []
        for c in contacts:
            if c.id in existing_ids:
                continue
            if not c.email:
                continue

            token = secrets.token_urlsafe(32)
            recipient = CrmCampaignRecipient(
                campaign_id=campaign.id,
                contact_id=c.id,
                email=c.email,
                name=c.name,
                tracking_token=token,
            )
            self.db.add(recipient)
            recipients.append(recipient)

        if recipients:
            await self.db.commit()
            for r in recipients:
                await self.db.refresh(r)

        return recipients

    # ── 追踪像素处理 ──────────────────────────────────────────────────────────────

    async def record_open(self, tracking_token: str) -> bool:
        """记录邮件打开事件（追踪像素被加载时调用）。

        返回 True 表示成功记录，False 表示令牌无效。
        """
        result = await self.db.execute(
            select(CrmCampaignRecipient).where(
                CrmCampaignRecipient.tracking_token == tracking_token
            )
        )
        recipient = result.scalar_one_or_none()
        if not recipient:
            return False

        if not recipient.opened:
            recipient.opened = True
            recipient.opened_at = func.now()
            await self.db.commit()

            # 同步更新活动计数
            await self._sync_campaign_stats(recipient.campaign_id)

        return True

    # ── 退订处理 ──────────────────────────────────────────────────────────────────

    async def unsubscribe(self, tracking_token: str) -> bool:
        """处理退订请求。

        返回 True 表示成功退订，False 表示令牌无效。
        """
        result = await self.db.execute(
            select(CrmCampaignRecipient).where(
                CrmCampaignRecipient.tracking_token == tracking_token
            )
        )
        recipient = result.scalar_one_or_none()
        if not recipient:
            return False

        if not recipient.unsubscribed:
            recipient.unsubscribed = True
            recipient.unsubscribed_at = func.now()
            await self.db.commit()

            # 同步更新活动计数
            await self._sync_campaign_stats(recipient.campaign_id)

        return True

    # ── 统计 ──────────────────────────────────────────────────────────────────────

    async def get_campaign_stats(self, campaign_id: int) -> dict:
        """获取活动统计数据。

        返回格式:
            {
                "campaign_id": int,
                "name": str,
                "status": str,
                "total_recipients": int,
                "sent_count": int,
                "opened_count": int,
                "unsubscribed_count": int,
                "open_rate": float,       # 打开率 (基于已发送)
                "unsubscribe_rate": float, # 退订率 (基于已发送)
                "opened_recipients": list[dict],   # 已打开的联系人(前50)
            }
        """
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            return {"error": "活动不存在"}

        # 实时从收件人表统计
        stats_result = await self.db.execute(
            select(
                func.count(CrmCampaignRecipient.id).label("total"),
                func.sum(
                    case((CrmCampaignRecipient.sent, 1), else_=0)
                ).label("sent"),
                func.sum(
                    case((CrmCampaignRecipient.opened, 1), else_=0)
                ).label("opened"),
                func.sum(
                    case((CrmCampaignRecipient.unsubscribed, 1), else_=0)
                ).label("unsubscribed"),
            ).where(CrmCampaignRecipient.campaign_id == campaign_id)
        )
        row = stats_result.one()
        total = int(row.total or 0)
        sent = int(row.sent or 0)
        opened = int(row.opened or 0)
        unsubscribed = int(row.unsubscribed or 0)

        # 已打开的联系人详情 (前 50)
        opened_details = []
        if opened > 0:
            detail_result = await self.db.execute(
                select(CrmCampaignRecipient)
                .where(
                    CrmCampaignRecipient.campaign_id == campaign_id,
                    CrmCampaignRecipient.opened,
                )
                .order_by(CrmCampaignRecipient.opened_at.desc().nullslast())
                .limit(50)
            )
            for rec in detail_result.scalars().all():
                opened_details.append({
                    "email": rec.email,
                    "name": rec.name,
                    "opened_at": rec.opened_at.isoformat() if rec.opened_at else None,
                })

        return {
            "campaign_id": campaign_id,
            "name": campaign.name,
            "status": campaign.status,
            "total_recipients": total,
            "sent_count": sent,
            "opened_count": opened,
            "unsubscribed_count": unsubscribed,
            "open_rate": round((opened / sent * 100) if sent > 0 else 0, 2),
            "unsubscribe_rate": round((unsubscribed / sent * 100) if sent > 0 else 0, 2),
            "opened_recipients": opened_details,
        }

    async def _sync_campaign_stats(self, campaign_id: int) -> None:
        """从收件人表同步统计数据到活动表。"""
        from sqlalchemy import case

        stats = await self.db.execute(
            select(
                func.count(CrmCampaignRecipient.id).label("total"),
                func.sum(
                    case((CrmCampaignRecipient.sent, 1), else_=0)
                ).label("sent"),
                func.sum(
                    case((CrmCampaignRecipient.opened, 1), else_=0)
                ).label("opened"),
                func.sum(
                    case((CrmCampaignRecipient.unsubscribed, 1), else_=0)
                ).label("unsubscribed"),
            ).where(CrmCampaignRecipient.campaign_id == campaign_id)
        )
        row = stats.one()

        await self.db.execute(
            update(CrmCampaign)
            .where(CrmCampaign.id == campaign_id)
            .values(
                total_recipients=int(row.total or 0),
                sent_count=int(row.sent or 0),
                opened_count=int(row.opened or 0),
                unsubscribed_count=int(row.unsubscribed or 0),
            )
        )
        await self.db.commit()


# ═══════════════════════════════════════════════════════════════════════════════════
# Helper 函数
# ═══════════════════════════════════════════════════════════════════════════════════


def get_tracking_pixel_bytes() -> bytes:
    """返回 1×1 透明 GIF 的字节数据。"""
    return _TRACKING_PIXEL_BYTES


def _build_tracking_and_unsubscribe(tracking_url: str, unsubscribe_url: str) -> str:
    """构建追踪像素 + 退订链接的 HTML 片段。"""
    return f"""\
<img src="{tracking_url}" width="1" height="1" style="display:none;" alt=""/>
<div style="margin-top:24px;padding-top:16px;border-top:1px solid #e8e8e8;font-size:12px;color:#999;text-align:center;">
<p style="margin:4px 0;">您收到此邮件是因为您在 AI数智名片 注册。</p>
<p style="margin:4px 0;">
<a href="{unsubscribe_url}" target="_blank" style="color:#1890ff;text-decoration:underline;">点击此处退订</a>
—— 我们尊重您的隐私。
</p>
</div>"""


def _resolve_template(template_name: str):
    """解析模板名称到模板函数。

    优先从 email_templates 导入，支持自定义模板名。
    """
    if template_name not in _ALLOWED_TEMPLATES:
        logger.warning("未知模板 '%s'，回退到默认", template_name)
        return None

    try:
        import importlib

        mod = importlib.import_module("app.services.email_templates")
        fn = getattr(mod, template_name, None)
        if fn is None:
            logger.warning("模板函数 '%s' 不存在", template_name)
        return fn
    except Exception as e:
        logger.warning("加载模板失败: %s", e)
        return None

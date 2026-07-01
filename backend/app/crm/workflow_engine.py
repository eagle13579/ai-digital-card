"""CRM 工作流自动化引擎。

纯 Python 实现，JSON 配置规则。支持:
  - 触发事件: contact_added, deal_created, stage_changed
  - 条件过滤: 根据字段值匹配
  - 动作类型: send_email, update_field, notify_user, create_task
  - 模板变量: {{contact.field}}, {{deal.field}}, {{stage.name}}

架构:
  WorkflowRule        → JSON 配置的规则定义（可存 DB 或文件）
  WorkflowEngine      → 事件触发后遍历规则、匹配条件、执行动作
  ActionRunner        → 动作执行器（每种动作一个方法）

使用示例:
    engine = WorkflowEngine(db, user_id)
    await engine.fire("contact_added", contact={"id": 1, "name": "张三", "email": "z@example.com"})
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crm.crm_models import CrmWorkflowRule, CrmWorkflowLog

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# 默认预置规则（JSON 配置）
# ═══════════════════════════════════════════════════════════════════════════════

PRESET_RULES: list[dict] = [
    {
        "name": "新联系人欢迎",
        "description": "创建联系人后自动发送欢迎邮件",
        "trigger_event": "contact_added",
        "conditions": [
            {"field": "email", "operator": "not_empty"}
        ],
        "actions": [
            {
                "type": "send_email",
                "config": {
                    "to": "{{contact.email}}",
                    "subject": "感谢联系 — 欢迎加入 {{contact.company}}！",
                    "body": "您好 {{contact.name}}，\n\n非常感谢您的联系！很高兴认识您。\n\n此致\n敬礼",
                    "html": "<h2>您好 {{contact.name}}，</h2><p>非常感谢您的联系！很高兴认识您。</p><p>此致<br>敬礼</p>"
                }
            }
        ],
        "enabled": True,
    },
    {
        "name": "机会进入谈判",
        "description": "机会阶段变为「谈判中」时通知销售经理",
        "trigger_event": "stage_changed",
        "conditions": [
            {"field": "stage_name", "operator": "eq", "value": "谈判中"}
        ],
        "actions": [
            {
                "type": "notify_user",
                "config": {
                    "title": "机会进入谈判阶段",
                    "message": "商机「{{deal.title}}」已进入谈判阶段，请及时跟进。"
                }
            }
        ],
        "enabled": True,
    },
    {
        "name": "成交庆祝",
        "description": "机会阶段变为「已成交」时更新赢单率为 100%",
        "trigger_event": "stage_changed",
        "conditions": [
            {"field": "stage_name", "operator": "eq", "value": "已成交"}
        ],
        "actions": [
            {
                "type": "update_field",
                "config": {
                    "target": "deal",
                    "field": "probability",
                    "value": 100.0
                }
            },
            {
                "type": "notify_user",
                "config": {
                    "title": "🎉 恭喜成交！",
                    "message": "商机「{{deal.title}}」已成功成交！金额: ¥{{deal.value}}"
                }
            }
        ],
        "enabled": True,
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# 模板引擎（变量替换）
# ═══════════════════════════════════════════════════════════════════════════════

def _render_template(template: str, context: dict[str, Any]) -> str:
    """替换模板中的 {{contact.xxx}} / {{deal.xxx}} / {{stage.xxx}} 变量。"""

    def _replacer(m: re.Match) -> str:
        expr = m.group(1).strip()
        # expr like "contact.name" or "deal.title"
        parts = expr.split(".", 1)
        if len(parts) == 2:
            obj_key, field = parts
            obj = context.get(obj_key)
            if isinstance(obj, dict):
                val = obj.get(field, "")
                if val is None:
                    val = ""
                return str(val)
        return m.group(0)  # 未匹配到，原样保留

    return re.sub(r"\{\{\s*([^}]+)\s*}}", _replacer, template)


# ═══════════════════════════════════════════════════════════════════════════════
# 条件匹配器
# ═══════════════════════════════════════════════════════════════════════════════

def _match_condition(condition: dict, context: dict[str, Any]) -> bool:
    """检查单条条件是否满足。"""
    field_path = condition["field"]
    operator = condition.get("operator", "eq")
    expected = condition.get("value")

    # 从 context 中解析字段值 (支持 contact.field / deal.field)
    parts = field_path.split(".", 1)
    if len(parts) == 2:
        obj = context.get(parts[0], {})
        if isinstance(obj, dict):
            actual = obj.get(parts[1])
        else:
            actual = None
    else:
        actual = context.get(field_path)

    if operator == "eq":
        return actual == expected
    elif operator == "ne":
        return actual != expected
    elif operator == "gt":
        return (actual or 0) > (expected or 0)
    elif operator == "gte":
        return (actual or 0) >= (expected or 0)
    elif operator == "lt":
        return (actual or 0) < (expected or 0)
    elif operator == "lte":
        return (actual or 0) <= (expected or 0)
    elif operator == "contains":
        return (expected or "") in (actual or "")
    elif operator == "not_empty":
        return bool(actual)
    elif operator == "empty":
        return not actual
    elif operator == "in":
        if isinstance(expected, list):
            return actual in expected
        return False
    return False


def _check_conditions(rule: dict, context: dict[str, Any]) -> bool:
    """检查规则的所有条件是否全部满足（AND 逻辑）。"""
    conditions = rule.get("conditions", [])
    if not conditions:
        return True  # 无条件 = 总是触发
    return all(_match_condition(c, context) for c in conditions)


# ═══════════════════════════════════════════════════════════════════════════════
# 动作执行器
# ═══════════════════════════════════════════════════════════════════════════════

class ActionRunner:
    """执行工作流动作。"""

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id

    async def execute(
        self,
        action: dict,
        context: dict[str, Any],
    ) -> dict:
        """执行单个动作，返回执行结果。"""
        action_type = action["type"]
        config = action.get("config", {})

        # 渲染模板变量
        rendered = {}
        for k, v in config.items():
            if isinstance(v, str):
                rendered[k] = _render_template(v, context)
            else:
                rendered[k] = v

        method_name = f"_do_{action_type}"
        method = getattr(self, method_name, None)
        if method is None:
            return {"success": False, "error": f"未知动作类型: {action_type}"}

        try:
            result = await method(rendered, context)
            return result
        except Exception as e:
            logger.error("动作执行失败 type=%s error=%s", action_type, str(e), exc_info=True)
            return {"success": False, "error": str(e)}

    # ── 动作: 发送邮件 ────────────────────────────────────────────────────────

    async def _do_send_email(
        self,
        config: dict,
        context: dict[str, Any],
    ) -> dict:
        """发送邮件。config: {to, subject, body, html}"""
        from app.services.email_service import email_service

        to = config.get("to", "")
        subject = config.get("subject", "无主题")
        body = config.get("body", "")
        html = config.get("html", "")

        if not to:
            return {"success": False, "error": "缺少收件人 (to)"}

        result = await email_service.send(
            to=to,
            subject=subject,
            body=body,
            html=html,
        )
        return {
            "success": result.get("success", False),
            "sent": result.get("sent", False),
            "to": to,
            "subject": subject,
            "error": result.get("error"),
        }

    # ── 动作: 更新字段 ────────────────────────────────────────────────────────

    async def _do_update_field(
        self,
        config: dict,
        context: dict[str, Any],
    ) -> dict:
        """更新字段。config: {target: "contact"|"deal", field, value}"""
        from app.crm.crm_service import CrmService
        from app.crm.crm_models import CrmDeal

        target = config.get("target", "deal")
        field = config.get("field", "")
        value = config.get("value")

        if target == "deal":
            deal = context.get("deal")
            if not deal or not deal.get("id"):
                return {"success": False, "error": "上下文中缺少 deal 信息"}
            deal_id = deal["id"]

            # 查询并更新
            svc = CrmService(self.db, self.user_id)
            result = await self.db.execute(
                select(CrmDeal).where(
                    CrmDeal.id == deal_id,
                    CrmDeal.owner_id == self.user_id,
                )
            )
            deal_obj = result.scalar_one_or_none()
            if not deal_obj:
                return {"success": False, "error": "机会不存在"}

            if hasattr(deal_obj, field):
                setattr(deal_obj, field, value)
                await self.db.commit()
                await self.db.refresh(deal_obj)
                return {"success": True, "field": field, "value": value}

            return {"success": False, "error": f"字段 {field} 在 CrmDeal 上不存在"}

        elif target == "contact":
            contact = context.get("contact")
            if not contact or not contact.get("id"):
                return {"success": False, "error": "上下文中缺少 contact 信息"}
            contact_id = contact["id"]

            svc = CrmService(self.db, self.user_id)
            updated = await svc.update_contact(contact_id, {field: value})
            if updated:
                return {"success": True, "field": field, "value": value}
            return {"success": False, "error": "更新联系人失败"}

        return {"success": False, "error": f"未知目标类型: {target}"}

    # ── 动作: 通知用户 ────────────────────────────────────────────────────────

    async def _do_notify_user(
        self,
        config: dict,
        context: dict[str, Any],
    ) -> dict:
        """通知用户（创建活动记录 + 记录日志）。"""
        from app.crm.crm_models import CrmActivity

        title = config.get("title", "系统通知")
        message = config.get("message", "")

        # 记录为系统活动
        contact_id = None
        if "contact" in context and context["contact"]:
            contact_id = context["contact"].get("id")

        if contact_id:
            activity = CrmActivity(
                owner_id=self.user_id,
                contact_id=contact_id,
                activity_type="system",
                title=title[:256],
                description=message,
                activity_date=datetime.utcnow(),
            )
            self.db.add(activity)
            await self.db.commit()
            await self.db.refresh(activity)

        logger.info(
            "[WorkflowNotify] user=%s title=%s message=%s",
            self.user_id, title, message,
        )

        return {
            "success": True,
            "title": title,
            "message": message,
            "logged": True,
        }

    # ── 动作: 创建任务 ────────────────────────────────────────────────────────

    async def _do_create_task(
        self,
        config: dict,
        context: dict[str, Any],
    ) -> dict:
        """创建任务（记录为笔记 + 活动）。"""
        from app.crm.crm_models import CrmNote

        title = config.get("title", "待办事项")
        description = config.get("description", "")
        contact_id = None
        deal_id = None

        if "contact" in context and context["contact"]:
            contact_id = context["contact"].get("id")
        if "deal" in context and context["deal"]:
            deal_id = context["deal"].get("id")

        content = f"【工作流任务】{title}\n{description}"

        note = CrmNote(
            owner_id=self.user_id,
            contact_id=contact_id,
            deal_id=deal_id,
            content=content,
            is_pinned=False,
        )
        self.db.add(note)
        await self.db.commit()
        await self.db.refresh(note)

        return {
            "success": True,
            "note_id": note.id,
            "title": title,
            "description": description,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 工作流引擎
# ═══════════════════════════════════════════════════════════════════════════════

class WorkflowEngine:
    """CRM 工作流自动化引擎。

    用法:
        engine = WorkflowEngine(db, user_id)
        await engine.fire("contact_added", contact={"name": "张三", "email": "z@example.com"})
    """

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id

    async def fire(
        self,
        trigger_event: str,
        *,
        contact: dict | None = None,
        deal: dict | None = None,
        stage: dict | None = None,
        extra: dict | None = None,
    ) -> list[dict]:
        """触发工作流。

        Args:
            trigger_event: 事件类型 (contact_added / deal_created / stage_changed)
            contact: 联系人数据字典
            deal: 机会数据字典
            stage: 管道阶段数据字典
            extra: 额外上下文

        Returns:
            执行结果列表: [{"rule_id": int, "rule_name": str, "actions": [...]}]
        """
        context: dict[str, Any] = {
            "contact": contact or {},
            "deal": deal or {},
            "stage": stage or {},
            **(extra or {}),
        }

        # 1. 加载所有启用的规则
        rules = await self._load_rules(trigger_event)

        if not rules:
            logger.debug("工作流: 事件=%s 没有匹配的启用规则", trigger_event)
            return []

        # 2. 遍历规则，匹配条件，执行动作
        results: list[dict] = []
        runner = ActionRunner(self.db, self.user_id)

        for rule in rules:
            rule_data = rule.get("rule_data", rule)  # 兼容 dict 或 model
            rule_name = rule_data.get("name", "未命名规则")
            rule_id = rule_data.get("id", 0)

            # 检查条件
            if not _check_conditions(rule_data, context):
                logger.debug("工作流: 规则=%s 条件不匹配，跳过", rule_name)
                continue

            # 执行动作
            logger.info("工作流: 规则=%s 触发", rule_name)
            action_results: list[dict] = []
            for action in rule_data.get("actions", []):
                action_result = await runner.execute(action, context)
                action_results.append(action_result)

            # 记录日志
            await self._log_execution(rule_data, context, action_results)

            results.append({
                "rule_id": rule_id,
                "rule_name": rule_name,
                "actions": action_results,
            })

        return results

    async def _load_rules(self, trigger_event: str) -> list[dict]:
        """从数据库加载所有匹配事件的启用规则。"""
        from app.crm.crm_models import CrmWorkflowRule

        result = await self.db.execute(
            select(CrmWorkflowRule).where(
                CrmWorkflowRule.owner_id == self.user_id,
                CrmWorkflowRule.trigger_event == trigger_event,
                CrmWorkflowRule.enabled == True,  # noqa: E712
            ).order_by(CrmWorkflowRule.created_at)
        )
        models = list(result.scalars().all())

        rules = []
        for m in models:
            rule_dict = m.to_dict()
            rule_dict["rule_data"] = rule_dict  # 统一引用
            rules.append(rule_dict)

        return rules

    async def _log_execution(
        self,
        rule: dict,
        context: dict[str, Any],
        action_results: list[dict],
    ) -> None:
        """记录工作流执行日志到数据库。"""
        from app.crm.crm_models import CrmWorkflowLog

        log = CrmWorkflowLog(
            owner_id=self.user_id,
            rule_id=rule.get("id", 0),
            rule_name=rule.get("name", ""),
            trigger_event=rule.get("trigger_event", ""),
            context_snapshot=json.dumps(context, ensure_ascii=False, default=str),
            action_results=json.dumps(action_results, ensure_ascii=False, default=str),
            success=all(r.get("success", False) for r in action_results if r),
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)

    # ── 规则 CRUD 辅助 ────────────────────────────────────────────────────────

    @staticmethod
    async def create_rule(
        db: AsyncSession,
        owner_id: int,
        data: dict,
    ) -> CrmWorkflowRule:
        """创建新的工作流规则。"""
        from app.crm.crm_models import CrmWorkflowRule

        rule = CrmWorkflowRule(
            owner_id=owner_id,
            name=data["name"],
            description=data.get("description", ""),
            trigger_event=data["trigger_event"],
            conditions=json.dumps(data.get("conditions", []), ensure_ascii=False),
            actions=json.dumps(data["actions"], ensure_ascii=False),
            enabled=data.get("enabled", True),
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        logger.info("创建工作流规则: user=%s name=%s", owner_id, rule.name)
        return rule

    @staticmethod
    async def update_rule_toggle(
        db: AsyncSession,
        owner_id: int,
        rule_id: int,
        enabled: bool | None = None,
    ) -> CrmWorkflowRule | None:
        """启用/禁用规则。"""
        from app.crm.crm_models import CrmWorkflowRule

        result = await db.execute(
            select(CrmWorkflowRule).where(
                CrmWorkflowRule.id == rule_id,
                CrmWorkflowRule.owner_id == owner_id,
            )
        )
        rule = result.scalar_one_or_none()
        if not rule:
            return None

        if enabled is not None:
            rule.enabled = enabled
        else:
            rule.enabled = not rule.enabled

        await db.commit()
        await db.refresh(rule)
        return rule

    @staticmethod
    async def delete_rule(
        db: AsyncSession,
        owner_id: int,
        rule_id: int,
    ) -> bool:
        """删除规则。"""
        from app.crm.crm_models import CrmWorkflowRule

        result = await db.execute(
            select(CrmWorkflowRule).where(
                CrmWorkflowRule.id == rule_id,
                CrmWorkflowRule.owner_id == owner_id,
            )
        )
        rule = result.scalar_one_or_none()
        if not rule:
            return False
        await db.delete(rule)
        await db.commit()
        return True

    @staticmethod
    async def get_rules(
        db: AsyncSession,
        owner_id: int,
    ) -> list[CrmWorkflowRule]:
        """获取用户的所有工作流规则。"""
        from app.crm.crm_models import CrmWorkflowRule

        result = await db.execute(
            select(CrmWorkflowRule).where(
                CrmWorkflowRule.owner_id == owner_id,
            ).order_by(CrmWorkflowRule.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def init_preset_rules(
        db: AsyncSession,
        owner_id: int,
    ) -> list[CrmWorkflowRule]:
        """为用户初始化 3 条预置规则（如果还没有任何规则）。"""
        from app.crm.crm_models import CrmWorkflowRule

        result = await db.execute(
            select(CrmWorkflowRule).where(
                CrmWorkflowRule.owner_id == owner_id,
            ).limit(1)
        )
        existing = result.scalar_one_or_none()
        if existing:
            # 已有规则，不重复创建
            result = await db.execute(
                select(CrmWorkflowRule).where(
                    CrmWorkflowRule.owner_id == owner_id,
                ).order_by(CrmWorkflowRule.created_at)
            )
            return list(result.scalars().all())

        created = []
        for preset in PRESET_RULES:
            rule = CrmWorkflowRule(
                owner_id=owner_id,
                name=preset["name"],
                description=preset.get("description", ""),
                trigger_event=preset["trigger_event"],
                conditions=json.dumps(preset.get("conditions", []), ensure_ascii=False),
                actions=json.dumps(preset["actions"], ensure_ascii=False),
                enabled=preset.get("enabled", False),  # 默认禁用，用户手动启用
            )
            db.add(rule)
            created.append(rule)

        await db.commit()
        for r in created:
            await db.refresh(r)

        logger.info("为用户 %s 初始化 %d 条预置工作流规则", owner_id, len(created))
        return created


# ── 测试规则（无需 DB） ──────────────────────────────────────────────────────

async def test_rule_execution(
    rule_data: dict,
    context: dict[str, Any],
) -> list[dict]:
    """测试规则执行，返回动作结果列表（不操作数据库）。"""
    runner = ActionRunner.__new__(ActionRunner)
    # 用不到 db 和 user_id，因为不会执行写库动作… 为安全起见设个 mock
    import types

    async def mock_add(*args, **kwargs):
        pass

    async def mock_commit(*args, **kwargs):
        pass

    runner.db = types.SimpleNamespace(add=mock_add)
    runner.db.commit = mock_commit

    results = []
    for action in rule_data.get("actions", []):
        result = await runner.execute(action, context)
        results.append(result)
    return results

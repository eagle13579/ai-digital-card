"""Web 表单捕获服务 — 嵌入网站表单 → 自动创建 CRM 联系人。

架构:
  Form 模型 (SQLAlchemy) 存储表单定义
  FormCaptureService 处理表单提交和嵌入代码生成
  反垃圾: Honeypot (隐藏字段) + 速率限制 (同IP每小时10次)

用法:
  1. 创建表单 (POST /api/crm/forms)
  2. 获取嵌入代码 (GET /api/crm/forms/{id}/embed)
  3. 将<script>放入网站 HTML
  4. 访客填写提交 → 自动创建 CRM 联系人
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

logger = logging.getLogger(__name__)

# ── 速率限制 (内存存储，生产环境建议迁移到 Redis) ──────────────────────────────

class RateLimiter:
    """简易内存速率限制器。

    生产环境建议替换为 Redis 实现 (app.cache)。
    每个 IP 每小时最多 submit_limit 次。
    """

    def __init__(self, max_per_hour: int = 10):
        self.max_per_hour = max_per_hour
        self._buckets: dict[str, list[float]] = {}  # ip -> [timestamps]

    def is_allowed(self, ip: str) -> bool:
        now = time.time()
        timestamps = self._buckets.get(ip, [])
        # 清理1小时以前的记录
        cutoff = now - 3600
        timestamps = [t for t in timestamps if t > cutoff]
        self._buckets[ip] = timestamps
        if len(timestamps) >= self.max_per_hour:
            return False
        self._buckets[ip].append(now)
        return True

    def get_remaining(self, ip: str) -> int:
        now = time.time()
        timestamps = self._buckets.get(ip, [])
        cutoff = now - 3600
        active = [t for t in timestamps if t > cutoff]
        remaining = self.max_per_hour - len(active)
        return max(0, remaining)


# 全局速率限制器实例
form_rate_limiter = RateLimiter(max_per_hour=10)


# ── Form 模型 ──────────────────────────────────────────────────────────────────

class CrmForm(Base):
    """Web 表单捕获定义。

    每个表单属于一个用户 (owner_id)，包含字段定义、提交动作和防垃圾配置。
    """

    __tablename__ = "crm_forms"

    id: int = Column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    owner_id: int = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # type: ignore

    # ── 表单基本信息 ─────────────────────────────────────────────────
    name: str = Column(String(128), nullable=False, comment="表单名称（内部标识）")  # type: ignore
    title: str = Column(String(256), default="", comment="表单标题（显示给访客）")  # type: ignore
    description: str = Column(Text, default="", comment="表单描述/说明文字")  # type: ignore

    # ── 字段定义 (JSON) ──────────────────────────────────────────────
    # [{"name":"姓名","field":"name","type":"text","required":true},
    #  {"name":"手机","field":"phone","type":"tel","required":true},
    #  {"name":"邮箱","field":"email","type":"email","required":false},
    #  {"name":"公司","field":"company","type":"text","required":false},
    #  {"name":"职位","field":"title","type":"text","required":false}]
    fields: str = Column(Text, nullable=False, default="[]", comment="字段定义 (JSON 数组)")  # type: ignore

    # ── 提交动作 ─────────────────────────────────────────────────────
    # "create_contact" | "update_contact"
    submit_action: str = Column(String(32), default="create_contact", comment="提交后动作")  # type: ignore
    # 提交成功后跳转 URL
    redirect_url: str = Column(String(512), default="", comment="提交成功后跳转URL")  # type: ignore
    # 成功提示文字
    success_message: str = Column(String(256), default="感谢您的提交，我们会尽快与您联系！", comment="成功提示")  # type: ignore

    # ── 反垃圾配置 ───────────────────────────────────────────────────
    enable_honeypot: bool = Column(Boolean, default=True, comment="启用 Honeypot 反垃圾")  # type: ignore
    enable_rate_limit: bool = Column(Boolean, default=True, comment="启用 IP 速率限制")  # type: ignore

    # ── 标签（自动添加到新建联系人） ────────────────────────────────
    auto_tags: str = Column(Text, default="[]", comment="自动添加的标签 (JSON 数组)")  # type: ignore

    # ── 状态 ─────────────────────────────────────────────────────────
    is_active: bool = Column(Boolean, default=True, comment="是否启用")  # type: ignore
    submission_count: int = Column(Integer, default=0, comment="总提交次数")  # type: ignore

    # ── 嵌入配置 ─────────────────────────────────────────────────────
    embed_theme: str = Column(String(32), default="light", comment="嵌入主题: light | dark")  # type: ignore
    embed_primary_color: str = Column(String(16), default="#1890ff", comment="嵌入主色调")  # type: ignore

    # ── 时间戳 ───────────────────────────────────────────────────────
    created_at: datetime = Column(DateTime, server_default=func.now())  # type: ignore
    updated_at: datetime = Column(DateTime, server_default=func.now(), onupdate=func.now())  # type: ignore

    def get_fields_list(self) -> list[dict]:
        """解析字段定义 JSON。"""
        if isinstance(self.fields, str):
            return json.loads(self.fields) if self.fields else []
        return self.fields or []

    def get_auto_tags_list(self) -> list[str]:
        """解析自动标签 JSON。"""
        if isinstance(self.auto_tags, str):
            return json.loads(self.auto_tags) if self.auto_tags else []
        return self.auto_tags or []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "fields": self.get_fields_list(),
            "submit_action": self.submit_action,
            "redirect_url": self.redirect_url,
            "success_message": self.success_message,
            "enable_honeypot": self.enable_honeypot,
            "enable_rate_limit": self.enable_rate_limit,
            "auto_tags": self.get_auto_tags_list(),
            "is_active": self.is_active,
            "submission_count": self.submission_count,
            "embed_theme": self.embed_theme,
            "embed_primary_color": self.embed_primary_color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ── 表单提交日志（审计/防重放） ────────────────────────────────────────────────

class FormSubmissionLog(Base):
    """表单提交日志 — 用于审计和防重放。"""

    __tablename__ = "crm_form_submission_logs"

    id: int = Column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    form_id: int = Column(Integer, ForeignKey("crm_forms.id"), nullable=False, index=True)  # type: ignore
    submitter_ip: str = Column(String(45), default="", comment="提交者IP")  # type: ignore
    submitter_ua: str = Column(Text, default="", comment="User-Agent")  # type: ignore
    payload: str = Column(Text, default="{}", comment="原始提交数据 (JSON)")  # type: ignore
    contact_id: int | None = Column(Integer, nullable=True, comment="创建的 CRM 联系人 ID")  # type: ignore
    honeypot_triggered: bool = Column(Boolean, default=False, comment="是否触发了 Honeypot")  # type: ignore
    success: bool = Column(Boolean, default=False, comment="是否成功")  # type: ignore
    error_message: str = Column(Text, default="", comment="错误信息")  # type: ignore
    created_at: datetime = Column(DateTime, server_default=func.now())  # type: ignore

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "form_id": self.form_id,
            "submitter_ip": self.submitter_ip,
            "submitter_ua": self.submitter_ua,
            "payload": json.loads(self.payload) if isinstance(self.payload, str) else self.payload,
            "contact_id": self.contact_id,
            "honeypot_triggered": self.honeypot_triggered,
            "success": self.success,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── FormCaptureService ─────────────────────────────────────────────────────────

class FormCaptureService:
    """Web 表单捕获核心业务逻辑。"""

    # CRM联系人字段到表单字段名的映射
    FIELD_MAPPING = {
        "name": "name",
        "phone": "phone",
        "email": "email",
        "company": "company",
        "title": "title",
        "department": "department",
        "intro": "intro",
    }

    def __init__(self, db: AsyncSession, owner_id: int | None = None):
        self.db = db
        self.owner_id = owner_id

    # ── 表单 CRUD ─────────────────────────────────────────────────────────────

    async def create_form(self, data: dict) -> CrmForm:
        """创建表单。"""
        form = CrmForm(
            owner_id=self.owner_id,
            name=data["name"],
            title=data.get("title", ""),
            description=data.get("description", ""),
            fields=json.dumps(data.get("fields", []), ensure_ascii=False),
            submit_action=data.get("submit_action", "create_contact"),
            redirect_url=data.get("redirect_url", ""),
            success_message=data.get("success_message", "感谢您的提交，我们会尽快与您联系！"),
            enable_honeypot=data.get("enable_honeypot", True),
            enable_rate_limit=data.get("enable_rate_limit", True),
            auto_tags=json.dumps(data.get("auto_tags", []), ensure_ascii=False),
            embed_theme=data.get("embed_theme", "light"),
            embed_primary_color=data.get("embed_primary_color", "#1890ff"),
            is_active=True,
            submission_count=0,
        )
        self.db.add(form)
        await self.db.commit()
        await self.db.refresh(form)
        logger.info("用户 %s 创建了表单 %s (id=%s)", self.owner_id, form.name, form.id)
        return form

    async def get_form(self, form_id: int) -> CrmForm | None:
        """获取表单。"""
        result = await self.db.execute(
            select(CrmForm).where(CrmForm.id == form_id)
        )
        return result.scalar_one_or_none()

    async def get_owned_form(self, form_id: int) -> CrmForm | None:
        """获取当前用户的表单（权限检查）。"""
        if not self.owner_id:
            return await self.get_form(form_id)
        result = await self.db.execute(
            select(CrmForm).where(
                CrmForm.id == form_id,
                CrmForm.owner_id == self.owner_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_forms(self) -> list[CrmForm]:
        """获取当前用户的表单列表。"""
        if not self.owner_id:
            result = await self.db.execute(
                select(CrmForm).order_by(CrmForm.updated_at.desc())
            )
            return list(result.scalars().all())
        result = await self.db.execute(
            select(CrmForm).where(
                CrmForm.owner_id == self.owner_id
            ).order_by(CrmForm.updated_at.desc())
        )
        return list(result.scalars().all())

    async def delete_form(self, form_id: int) -> bool:
        """删除表单。"""
        form = await self.get_owned_form(form_id)
        if not form:
            return False
        # 同时删除提交日志
        await self.db.execute(
            FormSubmissionLog.__table__.delete().where(
                FormSubmissionLog.form_id == form_id
            )
        )
        await self.db.delete(form)
        await self.db.commit()
        return True

    # ── 嵌入代码生成 ───────────────────────────────────────────────────────────

    def generate_embed_code(self, form: CrmForm, base_url: str = "") -> str:
        """生成网站嵌入脚本。

        返回一段 <script> 标签，网站管理员将其放入 HTML 中。
        脚本会自动渲染表单并处理提交。

        参数:
            form: CrmForm 实例
            base_url: 后端 API 地址，默认从 settings.BASE_URL 读取

        返回:
            HTML/JS 嵌入代码字符串
        """
        fields = form.get_fields_list()
        fields_json = json.dumps(fields, ensure_ascii=False)
        auto_tags = form.get_auto_tags_list()
        auto_tags_json = json.dumps(auto_tags, ensure_ascii=False)
        embed_theme = form.embed_theme
        primary_color = form.embed_primary_color

        # 生成随机的 CSS class 前缀以避免与宿主页面样式冲突
        scope_id = f"fc-{uuid.uuid4().hex[:8]}"

        # 如果 base_url 未提供，从 settings 获取
        if not base_url:
            try:
                from app.config import settings
                base_url = settings.BASE_URL
            except (ImportError, AttributeError):
                base_url = "http://localhost:8000"

        submit_url = f"{base_url.rstrip('/')}/api/crm/forms/{form.id}/submit"

        html = f"""<!-- AI数字名片 - 表单捕获 {form.name} -->
<div id="{scope_id}-root" data-form-id="{form.id}"></div>
<script>
(function() {{
    var root = document.getElementById("{scope_id}-root");
    if (!root) return;

    var fields = {fields_json};
    var submitUrl = "{submit_url}";
    var redirectUrl = {json.dumps(form.redirect_url or "")};
    var successMsg = {json.dumps(form.success_message)};
    var autoTags = {auto_tags_json};
    var primaryColor = "{primary_color}";
    var theme = "{embed_theme}";

    // 样式注入
    var style = document.createElement("style");
    style.textContent = `
        #root-{scope_id} .fc-form-container,
        .{scope_id}-form {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 480px;
            margin: 0 auto;
            padding: 24px;
            border-radius: 8px;
            background: ${{theme === 'dark' ? '#1f1f1f' : '#ffffff'}};
            color: ${{theme === 'dark' ? '#e8e8e8' : '#333333'}};
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .{scope_id}-form .fc-title {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        .{scope_id}-form .fc-desc {{
            font-size: 14px;
            color: ${{theme === 'dark' ? '#999' : '#666'}};
            margin-bottom: 20px;
        }}
        .{scope_id}-form .fc-field {{
            margin-bottom: 16px;
        }}
        .{scope_id}-form .fc-field label {{
            display: block;
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 4px;
            color: ${{theme === 'dark' ? '#ccc' : '#333'}};
        }}
        .{scope_id}-form .fc-field label .required {{
            color: #ff4d4f;
            margin-left: 2px;
        }}
        .{scope_id}-form .fc-field input,
        .{scope_id}-form .fc-field textarea,
        .{scope_id}-form .fc-field select {{
            width: 100%%;
            padding: 8px 12px;
            border: 1px solid ${{theme === 'dark' ? '#434343' : '#d9d9d9'}};
            border-radius: 4px;
            font-size: 14px;
            background: ${{theme === 'dark' ? '#141414' : '#ffffff'}};
            color: ${{theme === 'dark' ? '#e8e8e8' : '#333'}};
            box-sizing: border-box;
            transition: border-color 0.2s;
        }}
        .{scope_id}-form .fc-field input:focus,
        .{scope_id}-form .fc-field textarea:focus {{
            outline: none;
            border-color: ${{primaryColor}};
            box-shadow: 0 0 0 2px ${{primaryColor}}33;
        }}
        .{scope_id}-form .fc-submit {{
            width: 100%%;
            padding: 10px 16px;
            background: ${{primaryColor}};
            color: #fff;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: opacity 0.2s;
        }}
        .{scope_id}-form .fc-submit:hover {{
            opacity: 0.85;
        }}
        .{scope_id}-form .fc-submit:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        .{scope_id}-form .fc-error {{
            color: #ff4d4f;
            font-size: 13px;
            margin-top: 8px;
        }}
        .{scope_id}-form .fc-success {{
            color: #52c41a;
            font-size: 14px;
            text-align: center;
            padding: 20px;
        }}
        .{scope_id}-form .fc-hp-field {{
            position: absolute;
            left: -9999px;
            opacity: 0;
            height: 0;
            overflow: hidden;
        }}
    `;
    document.head.appendChild(style);

    // Honeypot 字段名
    var hpFieldName = "website_" + Math.random().toString(36).slice(2, 8);

    // 构建表单 HTML
    var html = '<div class="{scope_id}-form fc-form-container">';
    html += '<div class="fc-title">' + (root.getAttribute("data-title") || {json.dumps(form.title or "联系我们")}) + '</div>';
    html += '<div class="fc-desc">' + (root.getAttribute("data-desc") || {json.dumps(form.description or "")}) + '</div>';
    html += '<form id="fc-form-' + '{scope_id}' + '" onsubmit="return false;">';

    // Honeypot 隐藏字段
    html += '<div class="fc-hp-field">';
    html += '<input type="text" name="' + hpFieldName + '" tabindex="-1" autocomplete="off">';
    html += '</div>';

    for (var i = 0; i < fields.length; i++) {{
        var f = fields[i];
        html += '<div class="fc-field">';
        html += '<label>';
        html += f.label || f.name;
        if (f.required) {{
            html += '<span class="required"> *</span>';
        }}
        html += '</label>';

        var fieldType = f.type || "text";
        var placeholder = f.placeholder || "";
        if (fieldType === "textarea") {{
            html += '<textarea name="' + f.field + '" placeholder="' + placeholder + '" ' + (f.required ? "required" : "") + ' rows="3"></textarea>';
        }} else {{
            html += '<input type="' + fieldType + '" name="' + f.field + '" placeholder="' + placeholder + '" ' + (f.required ? "required" : "") + '>';
        }}
        html += '</div>';
    }}

    html += '<button type="submit" class="fc-submit" id="fc-btn-' + '{scope_id}' + '">提交</button>';
    html += '<div class="fc-error" id="fc-err-' + '{scope_id}' + '" style="display:none;"></div>';
    html += '<div class="fc-success" id="fc-ok-' + '{scope_id}' + '" style="display:none;"></div>';
    html += '</form>';
    html += '</div>';

    root.innerHTML = html;

    // 处理提交
    document.getElementById("fc-form-" + "{scope_id}").addEventListener("submit", async function(e) {{
        e.preventDefault();
        var btn = document.getElementById("fc-btn-" + "{scope_id}");
        var errEl = document.getElementById("fc-err-" + "{scope_id}");
        var okEl = document.getElementById("fc-ok-" + "{scope_id}");
        var form = e.target;

        errEl.style.display = "none";
        okEl.style.display = "none";
        btn.disabled = true;
        btn.textContent = "提交中...";

        var formData = new FormData(form);
        var payload = {{}};
        for (var pair of formData.entries()) {{
            payload[pair[0]] = pair[1];
        }}

        try {{
            var resp = await fetch(submitUrl, {{
                method: "POST",
                headers: {{"Content-Type": "application/json"}},
                body: JSON.stringify(payload)
            }});
            var result = await resp.json();
            if (resp.ok) {{
                okEl.style.display = "block";
                okEl.textContent = successMsg;
                btn.style.display = "none";
                if (redirectUrl) {{
                    setTimeout(function() {{ window.location.href = redirectUrl; }}, 2000);
                }}
            }} else {{
                errEl.textContent = result.detail || "提交失败，请稍后重试";
                errEl.style.display = "block";
                btn.disabled = false;
                btn.textContent = "提交";
            }}
        }} catch (err) {{
            errEl.textContent = "网络错误，请检查连接后重试";
            errEl.style.display = "block";
            btn.disabled = false;
            btn.textContent = "提交";
        }}
    }});
}})();
</script>"""

        return html

    # ── 表单提交处理 ───────────────────────────────────────────────────────────

    async def submit_form(
        self,
        form_id: int,
        payload: dict[str, Any],
        submitter_ip: str = "",
        submitter_ua: str = "",
    ) -> dict[str, Any]:
        """处理表单提交。

        返回:
            成功: {"success": true, "contact_id": int, ...}
            失败: {"success": false, "error": "..."}
        """
        form = await self.get_form(form_id)
        if not form:
            return {"success": False, "error": "表单不存在"}
        if not form.is_active:
            return {"success": False, "error": "表单已禁用"}

        fields = form.get_fields_list()

        # ── 1. Honeypot 检测 ──────────────────────────────────────────
        honeypot_triggered = False
        if form.enable_honeypot:
            # 找出 payload 中不属于预定义字段的键（即 honeypot 字段）
            defined_fields = {f["field"] for f in fields}
            honeypot_keys = [k for k in payload if k not in defined_fields and k != "fc_token"]
            if honeypot_keys:
                # 检查 honeypot 字段是否有值
                has_honeypot_val = any(payload.get(k) for k in honeypot_keys)
                if has_honeypot_val:
                    honeypot_triggered = True
                    logger.warning("Honeypot 触发 form=%s ip=%s keys=%s", form_id, submitter_ip, honeypot_keys)

        # 清理 payload: 只保留定义的字段
        cleaned: dict[str, Any] = {}
        for f in fields:
            field_name = f["field"]
            if field_name in payload:
                cleaned[field_name] = payload[field_name]

        # ── 2. 必填字段验证 ───────────────────────────────────────────
        missing = []
        for f in fields:
            if f.get("required") and not cleaned.get(f["field"], "").strip():
                missing.append(f.get("label") or f["name"])
        if missing:
            log_entry = FormSubmissionLog(
                form_id=form_id,
                submitter_ip=submitter_ip,
                submitter_ua=submitter_ua,
                payload=json.dumps(payload, ensure_ascii=False),
                honeypot_triggered=honeypot_triggered,
                success=False,
                error_message=f"缺少必填字段: {', '.join(missing)}",
            )
            self.db.add(log_entry)
            await self.db.commit()
            return {"success": False, "error": f"缺少必填字段: {', '.join(missing)}"}

        # ── 3. Honeypot 触发则记录但不处理 ──────────────────────────────
        if honeypot_triggered:
            log_entry = FormSubmissionLog(
                form_id=form_id,
                submitter_ip=submitter_ip,
                submitter_ua=submitter_ua,
                payload=json.dumps(payload, ensure_ascii=False),
                honeypot_triggered=True,
                success=False,
                error_message="Honeypot 触犯",
            )
            self.db.add(log_entry)
            await self.db.commit()
            # 返回假成功，不暴露检测逻辑
            return {"success": True, "honeypot": True}

        # ── 4. 创建 CRM 联系人（复用 crm_service） ─────────────────────
        try:
            # 构建联系人数据
            contact_data: dict[str, Any] = {}
            for crm_field, payload_key in self.FIELD_MAPPING.items():
                val = cleaned.get(payload_key, "")
                if val is not None and str(val).strip():
                    contact_data[crm_field] = str(val).strip()

            # 确保有 name
            if "name" not in contact_data:
                # 尝试从其他字段推断姓名
                contact_data["name"] = cleaned.get("姓名", cleaned.get("fullname", "网站访客"))

            # 添加来源标记和标签
            auto_tags = form.get_auto_tags_list()
            existing_tags = contact_data.get("tags", [])
            if isinstance(existing_tags, str):
                existing_tags = [t.strip() for t in existing_tags.split(",") if t.strip()]
            contact_data["tags"] = list(set(existing_tags + auto_tags))
            contact_data["source"] = "web_form"
            contact_data["source_record_id"] = form_id

            # 使用 CrmService 创建联系人
            from app.crm.crm_service import CrmService
            crm_svc = CrmService(self.db, form.owner_id)
            contact = await crm_svc.create_contact(contact_data)

            # ── 5. 更新表单提交计数 ────────────────────────────────────
            form.submission_count = (form.submission_count or 0) + 1

            # ── 6. 记录提交日志 ────────────────────────────────────────
            log_entry = FormSubmissionLog(
                form_id=form_id,
                submitter_ip=submitter_ip,
                submitter_ua=submitter_ua,
                payload=json.dumps(payload, ensure_ascii=False),
                contact_id=contact.id,
                honeypot_triggered=False,
                success=True,
            )
            self.db.add(log_entry)
            await self.db.commit()
            await self.db.refresh(form)

            logger.info(
                "表单提交成功 form=%s contact=%s ip=%s",
                form_id, contact.id, submitter_ip,
            )

            return {
                "success": True,
                "contact_id": contact.id,
                "contact_name": contact.name,
                "redirect_url": form.redirect_url or "",
                "success_message": form.success_message,
            }

        except Exception as exc:
            logger.exception("表单提交处理失败 form=%s: %s", form_id, exc)
            log_entry = FormSubmissionLog(
                form_id=form_id,
                submitter_ip=submitter_ip,
                submitter_ua=submitter_ua,
                payload=json.dumps(payload, ensure_ascii=False),
                honeypot_triggered=False,
                success=False,
                error_message=str(exc),
            )
            self.db.add(log_entry)
            await self.db.commit()
            return {"success": False, "error": "服务器内部错误，请稍后重试"}

    # ── 提交日志 ───────────────────────────────────────────────────────────────

    async def get_submission_logs(
        self, form_id: int, page: int = 1, page_size: int = 20
    ) -> tuple[list[FormSubmissionLog], int]:
        """获取表单提交日志。"""
        if self.owner_id:
            # 验证表单属于当前用户
            form = await self.get_owned_form(form_id)
            if not form:
                return [], 0

        query = select(FormSubmissionLog).where(
            FormSubmissionLog.form_id == form_id
        ).order_by(FormSubmissionLog.created_at.desc())

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        logs = list(result.scalars().all())

        return logs, total

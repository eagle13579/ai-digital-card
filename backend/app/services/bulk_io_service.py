"""CSV 批量导入/导出服务 — 企业级数据迁移。

支持实体类型:
  - 'contacts'   → CRM 联系人 (CrmContact)
  - 'brochures'  → 画册 (Brochure)
  - 'users'      → 用户 (User)

CSV 格式: UTF-8 with BOM, 首行为 header, 逗号分隔。
"""

from __future__ import annotations

import csv
import io
import json
import logging
import traceback
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.brochure import Brochure
from app.models.user import User

logger = logging.getLogger(__name__)

# ── 数据类 ───────────────────────────────────────────────────────────────────


@dataclass
class BulkImportError:
    """单行导入错误记录。"""
    row: int
    message: str
    raw_data: dict[str, str] | None = None


@dataclass
class BulkImportResult:
    """批量导入结果。"""
    total_rows: int = 0
    success_rows: int = 0
    error_rows: int = 0
    errors_detail: list[BulkImportError] = field(default_factory=list)


@dataclass
class BulkExportResult:
    """批量导出结果。"""
    csv_content: str = ""
    file_name: str = ""
    row_count: int = 0


# ── 导入任务状态追踪（内存） ────────────────────────────────────────────────


_import_jobs: dict[str, dict[str, Any]] = {}


def _make_job_id() -> str:
    return uuid4().hex[:12]


# ── 字段定义 ─────────────────────────────────────────────────────────────────


def _contacts_headers() -> list[str]:
    return [
        "姓名", "手机", "邮箱", "公司", "职位", "部门",
        "来源", "标签", "管道阶段", "预估金额", "备注",
    ]


def _brochures_headers() -> list[str]:
    return [
        "标题", "用途", "封面", "状态", "页数",
        "分享令牌", "浏览数",
    ]


def _users_headers() -> list[str]:
    return [
        "用户名", "手机", "姓名", "公司", "职位", "简介",
        "头像", "角色", "会员等级",
    ]


_CONTACT_SOURCES = {"match", "manual", "visitor", "import"}
_BROCHURE_STATUSES = {"draft", "published"}
_BROCHURE_PURPOSES = {"partner", "client", "investor", "supplier", ""}
_USER_ROLES = {"user", "admin"}


def _headers_for(entity_type: str) -> list[str]:
    mapping = {
        "contacts": _contacts_headers,
        "brochures": _brochures_headers,
        "users": _users_headers,
    }
    fn = mapping.get(entity_type)
    if not fn:
        raise ValueError(f"不支持的实体类型: {entity_type}")
    return fn()


# ── Service ──────────────────────────────────────────────────────────────────


class BulkIOService:
    """CSV 批量导入/导出服务。"""

    def __init__(self, db: AsyncSession, user_id: int | None = None):
        self.db = db
        self.user_id = user_id

    # ── 导入 ──────────────────────────────────────────────────────────────

    async def import_csv(
        self,
        file_content: str,
        entity_type: str,
    ) -> BulkImportResult:
        """解析 CSV 内容并批量导入指定实体。

        Args:
            file_content: CSV 文本内容（UTF-8 with BOM 或纯 UTF-8）。
            entity_type: 实体类型 — contacts / brochures / users。

        Returns:
            BulkImportResult 包含导入统计与错误详情。
        """
        # 去除 BOM
        if file_content.startswith("\ufeff"):
            file_content = file_content[1:]

        reader = csv.DictReader(io.StringIO(file_content))
        rows = list(reader)
        total = len(rows)

        result = BulkImportResult(total_rows=total)

        # 按实体类型分发
        dispatch = {
            "contacts": self._import_contacts,
            "brochures": self._import_brochures,
            "users": self._import_users,
        }
        handler = dispatch.get(entity_type)
        if not handler:
            raise ValueError(f"不支持的实体类型: {entity_type}")

        await handler(rows, result)
        await self.db.commit()

        return result

    async def _import_contacts(
        self,
        rows: list[dict[str, str]],
        result: BulkImportResult,
    ) -> None:
        """批量导入 CRM 联系人。"""
        # 延迟导入避免循环
        from app.crm.crm_models import CrmContact

        # 获取默认管道阶段
        stages_result = await self.db.execute(
            select(CrmContact.__table__.c).limit(0)
        )
        _ = stages_result  # 仅用于触发 schema 感知

        # 查找默认 stage
        from app.crm.crm_models import CrmPipelineStage

        stmt = select(CrmPipelineStage).where(
            CrmPipelineStage.user_id == self.user_id,
            CrmPipelineStage.is_default.is_(True),
        )
        stage_result = await self.db.execute(stmt)
        default_stage = stage_result.scalar_one_or_none()

        for i, row in enumerate(rows, start=1):
            try:
                name = row.get("姓名", "").strip()
                if not name:
                    result.errors_detail.append(
                        BulkImportError(row=i, message="姓名为空", raw_data=row)
                    )
                    result.error_rows += 1
                    continue

                tags_str = row.get("标签", "").strip()
                tags = (
                    [t.strip() for t in tags_str.split(";") if t.strip()]
                    if tags_str
                    else []
                )

                contact = CrmContact(
                    owner_id=self.user_id or 0,
                    name=name,
                    phone=row.get("手机", "").strip(),
                    email=row.get("邮箱", "").strip(),
                    company=row.get("公司", "").strip(),
                    title=row.get("职位", "").strip(),
                    department=row.get("部门", "").strip(),
                    source=(
                        row.get("来源", "").strip()
                        if row.get("来源", "").strip() in _CONTACT_SOURCES
                        else "import"
                    ),
                    tags=json.dumps(tags, ensure_ascii=False),
                    pipeline_stage_id=default_stage.id if default_stage else None,
                )
                self.db.add(contact)
                result.success_rows += 1
            except Exception as exc:
                result.errors_detail.append(
                    BulkImportError(
                        row=i,
                        message=f"导入失败: {exc}",
                        raw_data=row,
                    )
                )
                result.error_rows += 1
                logger.warning("CRM 联系人导入失败 row=%d: %s", i, exc)

    async def _import_brochures(
        self,
        rows: list[dict[str, str]],
        result: BulkImportResult,
    ) -> None:
        """批量导入画册。"""
        # 收集所有涉及的用户 ID
        for i, row in enumerate(rows, start=1):
            try:
                title = row.get("标题", "").strip()
                if not title:
                    result.errors_detail.append(
                        BulkImportError(row=i, message="标题为空", raw_data=row)
                    )
                    result.error_rows += 1
                    continue

                purpose = row.get("用途", "").strip()
                if purpose and purpose not in _BROCHURE_PURPOSES:
                    result.errors_detail.append(
                        BulkImportError(
                            row=i,
                            message=f"无效的用途值 '{purpose}'，允许: {','.join(_BROCHURE_PURPOSES)}",
                            raw_data=row,
                        )
                    )
                    result.error_rows += 1
                    continue

                status = row.get("状态", "draft").strip()
                if status not in _BROCHURE_STATUSES:
                    status = "draft"

                cover = row.get("封面", "").strip()
                pages_count_str = row.get("页数", "1").strip()
                try:
                    pages_count = max(1, int(pages_count_str))
                except (ValueError, TypeError):
                    pages_count = 1

                brochure = Brochure(
                    user_id=self.user_id or 0,
                    title=title,
                    cover=cover,
                    purpose=purpose,
                    pages_count=pages_count,
                    status=status,
                )
                self.db.add(brochure)
                result.success_rows += 1
            except Exception as exc:
                result.errors_detail.append(
                    BulkImportError(row=i, message=f"导入失败: {exc}", raw_data=row)
                )
                result.error_rows += 1
                logger.warning("画册导入失败 row=%d: %s", i, exc)

    async def _import_users(
        self,
        rows: list[dict[str, str]],
        result: BulkImportResult,
    ) -> None:
        """批量导入用户（不覆盖已有用户）。"""
        for i, row in enumerate(rows, start=1):
            try:
                phone = row.get("手机", "").strip()
                if not phone:
                    result.errors_detail.append(
                        BulkImportError(row=i, message="手机号为空", raw_data=row)
                    )
                    result.error_rows += 1
                    continue

                # 跳过已存在的手机号
                existing = await self.db.execute(
                    select(User).where(User.phone == phone)
                )
                if existing.scalar_one_or_none():
                    result.errors_detail.append(
                        BulkImportError(
                            row=i,
                            message=f"手机号 {phone} 已存在",
                            raw_data=row,
                        )
                    )
                    result.error_rows += 1
                    continue

                name = row.get("姓名", "").strip() or phone
                role = row.get("角色", "user").strip()
                if role not in _USER_ROLES:
                    role = "user"

                user = User(
                    username=row.get("用户名", "").strip() or None,
                    phone=phone,
                    password_hash="",  # 导入用户需另行设置密码
                    name=name,
                    company=row.get("公司", "").strip(),
                    title=row.get("职位", "").strip(),
                    intro=row.get("简介", "").strip(),
                    avatar=row.get("头像", "").strip(),
                    role=role,
                    membership_tier=row.get("会员等级", "free").strip() or "free",
                )
                self.db.add(user)
                result.success_rows += 1
            except Exception as exc:
                result.errors_detail.append(
                    BulkImportError(row=i, message=f"导入失败: {exc}", raw_data=row)
                )
                result.error_rows += 1
                logger.warning("用户导入失败 row=%d: %s", i, exc)

    # ── 导出 ──────────────────────────────────────────────────────────────

    async def export_csv(
        self,
        entity_type: str,
        filters: dict[str, Any] | None = None,
    ) -> BulkExportResult:
        """导出指定实体类型为 CSV。

        Args:
            entity_type: 实体类型 — contacts / brochures / users。
            filters: 可选过滤条件（如 {"user_id": 123}）。

        Returns:
            BulkExportResult 含 CSV 内容与文件名。
        """
        dispatch = {
            "contacts": self._export_contacts,
            "brochures": self._export_brochures,
            "users": self._export_users,
        }
        handler = dispatch.get(entity_type)
        if not handler:
            raise ValueError(f"不支持的实体类型: {entity_type}")

        return await handler(filters or {})

    async def _export_contacts(
        self,
        filters: dict[str, Any],
    ) -> BulkExportResult:
        """导出 CRM 联系人。"""
        from app.crm.crm_models import CrmContact, CrmPipelineStage

        query = select(CrmContact)
        if self.user_id:
            query = query.where(CrmContact.owner_id == self.user_id)
        for key, val in filters.items():
            if hasattr(CrmContact, key):
                query = query.where(getattr(CrmContact, key) == val)

        result = await self.db.execute(query)
        contacts = result.scalars().all()

        # 获取 stage 映射
        stage_ids = {c.pipeline_stage_id for c in contacts if c.pipeline_stage_id}
        stages = {}
        if stage_ids:
            sr = await self.db.execute(
                select(CrmPipelineStage).where(CrmPipelineStage.id.in_(stage_ids))
            )
            stages = {s.id: s.name for s in sr.scalars().all()}

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(_contacts_headers())

        for c in contacts:
            try:
                tags_list = json.loads(c.tags) if isinstance(c.tags, str) else []
            except (json.JSONDecodeError, TypeError):
                tags_list = []
            writer.writerow([
                c.name,
                c.phone or "",
                c.email or "",
                c.company or "",
                c.title or "",
                c.department or "",
                c.source or "",
                "; ".join(tags_list),
                stages.get(c.pipeline_stage_id, ""),
                float(c.deal_value) if hasattr(c, "deal_value") and c.deal_value else "",
                getattr(c, "notes", "") or "",
            ])

        return BulkExportResult(
            csv_content=output.getvalue(),
            file_name="contacts_export.csv",
            row_count=len(contacts),
        )

    async def _export_brochures(
        self,
        filters: dict[str, Any],
    ) -> BulkExportResult:
        """导出画册。"""
        query = select(Brochure)
        if self.user_id:
            query = query.where(Brochure.user_id == self.user_id)
        for key, val in filters.items():
            if hasattr(Brochure, key):
                query = query.where(getattr(Brochure, key) == val)

        result = await self.db.execute(query)
        brochures = result.scalars().all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(_brochures_headers())

        for b in brochures:
            writer.writerow([
                b.title,
                b.purpose or "",
                b.cover or "",
                b.status,
                b.pages_count,
                b.share_token or "",
                b.view_count,
            ])

        return BulkExportResult(
            csv_content=output.getvalue(),
            file_name="brochures_export.csv",
            row_count=len(brochures),
        )

    async def _export_users(
        self,
        filters: dict[str, Any],
    ) -> BulkExportResult:
        """导出用户。"""
        query = select(User)
        for key, val in filters.items():
            if hasattr(User, key):
                query = query.where(getattr(User, key) == val)

        result = await self.db.execute(query)
        users = result.scalars().all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(_users_headers())

        for u in users:
            writer.writerow([
                u.username or "",
                u.phone,
                u.name,
                u.company or "",
                u.title or "",
                u.intro or "",
                u.avatar or "",
                u.role,
                u.membership_tier,
            ])

        return BulkExportResult(
            csv_content=output.getvalue(),
            file_name="users_export.csv",
            row_count=len(users),
        )

    # ── 验证 ──────────────────────────────────────────────────────────────

    async def validate_csv(
        self,
        file_content: str,
        entity_type: str,
    ) -> BulkImportResult:
        """验证 CSV 数据但不实际导入。

        逐行检查字段完整性、格式合法性，返回错误统计。
        """
        if file_content.startswith("\ufeff"):
            file_content = file_content[1:]

        reader = csv.DictReader(io.StringIO(file_content))
        rows = list(reader)
        total = len(rows)
        result = BulkImportResult(total_rows=total)

        headers = _headers_for(entity_type)

        # 根据实体类型确定必须字段
        required_fields_map = {
            "contacts": ["姓名"],
            "brochures": ["标题"],
            "users": ["手机"],
        }
        required_fields = required_fields_map.get(entity_type, [])

        for i, row in enumerate(rows, start=1):
            # 只检查必须字段
            missing = [h for h in required_fields if not row.get(h, "").strip()]
            if missing:
                result.errors_detail.append(
                    BulkImportError(
                        row=i,
                        message=f"必需字段为空: {', '.join(missing)}",
                        raw_data=row,
                    )
                )
                result.error_rows += 1
                continue

            # 实体特定验证
            try:
                if entity_type == "contacts":
                    self._validate_contact_row(row, i, result)
                elif entity_type == "brochures":
                    self._validate_brochure_row(row, i, result)
                elif entity_type == "users":
                    self._validate_user_row(row, i, result)
                else:
                    result.success_rows += 1
            except Exception as exc:
                result.errors_detail.append(
                    BulkImportError(row=i, message=f"验证失败: {exc}", raw_data=row)
                )
                result.error_rows += 1

        return result

    def _validate_contact_row(
        self,
        row: dict[str, str],
        i: int,
        result: BulkImportResult,
    ) -> None:
        name = row.get("姓名", "").strip()
        if not name:
            raise ValueError("姓名为空")
        source = row.get("来源", "").strip()
        if source and source not in _CONTACT_SOURCES:
            raise ValueError(f"无效来源 '{source}'")
        result.success_rows += 1

    def _validate_brochure_row(
        self,
        row: dict[str, str],
        i: int,
        result: BulkImportResult,
    ) -> None:
        title = row.get("标题", "").strip()
        if not title:
            raise ValueError("标题为空")
        purpose = row.get("用途", "").strip()
        if purpose and purpose not in _BROCHURE_PURPOSES:
            raise ValueError(f"无效用途 '{purpose}'")
        status = row.get("状态", "").strip()
        if status and status not in _BROCHURE_STATUSES:
            raise ValueError(f"无效状态 '{status}'")
        result.success_rows += 1

    def _validate_user_row(
        self,
        row: dict[str, str],
        i: int,
        result: BulkImportResult,
    ) -> None:
        phone = row.get("手机", "").strip()
        if not phone:
            raise ValueError("手机号为空")
        role = row.get("角色", "").strip()
        if role and role not in _USER_ROLES:
            raise ValueError(f"无效角色 '{role}'")
        result.success_rows += 1

    # ── 模板 ──────────────────────────────────────────────────────────────

    def get_import_template(self, entity_type: str) -> str:
        """生成带示例数据的 CSV 模板。

        Returns:
            CSV 字符串（UTF-8 with BOM）。
        """
        headers = _headers_for(entity_type)
        sample_data = self._sample_data(entity_type)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        for row in sample_data:
            writer.writerow(row)

        csv_str = output.getvalue()
        return "\ufeff" + csv_str

    def _sample_data(self, entity_type: str) -> list[list[str]]:
        samples = {
            "contacts": [
                ["张三", "13800138001", "zhangsan@example.com", "科技有限公司", "CTO", "技术部", "manual", "VIP;技术", "潜在客户", "50000", ""],
                ["李四", "13900139002", "lisi@example.com", "数据集团", "市场总监", "市场部", "import", "", "初步接洽", "", ""],
            ],
            "brochures": [
                ["公司简介画册", "partner", "https://example.com/cover1.jpg", "published", "8", "", ""],
                ["产品手册2024", "client", "", "draft", "12", "", ""],
            ],
            "users": [
                ["wangwu", "13700137003", "王五", "创新公司", "CEO", "创业者，专注AI领域", "", "admin", "gold"],
                ["", "13600136004", "赵六", "", "", "", "", "user", "free"],
            ],
        }
        return samples.get(entity_type, [])


# ── 异步上下文管理器工厂 ──────────────────────────────────────────────────


async def get_bulk_io_service(
    db: AsyncSession,
    user_id: int | None = None,
) -> BulkIOService:
    """获取 BulkIOService 实例的工厂函数。"""
    return BulkIOService(db=db, user_id=user_id)

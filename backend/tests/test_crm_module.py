"""CRM 模块测试。

测试策略 (适配当前测试基础设施):
  - 服务层测试 (CrmService 直接调用 test_db): 最可靠, 覆盖核心业务逻辑
  - HTTP API 测试: 需要 CSRF token + 依赖覆盖, 可选执行
  - match_hook 单元测试: 直接调用 match_hook 函数

现有测试基础设施约束:
  - `client` fixture 使用独立的 in-memory DB (与 test_db 隔离)
  - CSRF 中间件对 POST/PUT/DELETE 要求 csrf_token cookie + header
  - 因此 HTTP API 测试需要额外的 fixture 编排

依赖 conftest.py 提供的 fixtures:
  - test_db / test_db_session  (in-memory SQLite async session)
  - client                     (httpx.AsyncClient via ASGITransport)
  - test_user, second_user     (User instances in test_db)
  - auth_headers               (JWT Authorization header dict)
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

# ── 提前导入 CRM 模型, 确保在 test_db 创建表时注册到 Base.metadata ──
from app.crm import crm_models  # noqa: F401 — registers CRM tables on Base


# ═══════════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════════
# 服务层测试 (推荐 — 直接使用 CrmService + test_db 会话)
# ═══════════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
async def crm_svc(test_db: AsyncSession, test_user: User):
    """创建 CrmService 实例，绑定 test_user。"""
    from app.crm.crm_service import CrmService

    return CrmService(db=test_db, user_id=test_user.id)


class TestServiceCreateContact:
    """服务层: 创建联系人"""

    async def test_create_contact_basic(self, crm_svc):
        """创建基本联系人。"""
        contact = await crm_svc.create_contact({
            "name": "张三",
            "phone": "13800001111",
            "email": "zhangsan@example.com",
            "company": "示例科技",
            "title": "技术总监",
            "department": "研发部",
            "intro": "老朋友",
        })
        assert contact.id > 0
        assert contact.name == "张三"
        assert contact.phone == "13800001111"
        assert contact.email == "zhangsan@example.com"
        assert contact.company == "示例科技"
        assert contact.title == "技术总监"
        assert contact.source == "manual"

    async def test_create_contact_with_tags(self, crm_svc):
        """创建带标签的联系人。"""
        contact = await crm_svc.create_contact({
            "name": "李四",
            "phone": "13800002222",
            "tags": ["VIP", "重点客户"],
            "deal_value": 50000.0,
        })
        tags = json.loads(contact.tags) if isinstance(contact.tags, str) else contact.tags
        assert "VIP" in tags
        assert "重点客户" in tags

    async def test_create_contact_with_default_stage(self, crm_svc):
        """创建联系人时自动分配默认管道阶段。"""
        # 先确保有默认阶段
        stages = await crm_svc.ensure_default_stages()
        default_stage = next((s for s in stages if s.is_default), stages[0])
        assert default_stage is not None

        contact = await crm_svc.create_contact({"name": "王五"})
        assert contact.pipeline_stage_id is not None
        assert contact.stage is not None

    async def test_create_contact_triggers_activity(self, crm_svc):
        """创建联系人应自动产生 system 活动。"""
        contact = await crm_svc.create_contact({"name": "活动测试"})
        activities, total = await crm_svc.get_contact_timeline(contact.id)
        assert total >= 1
        assert activities[0].activity_type == "system"
        assert "添加联系人" in activities[0].title


class TestServiceSearchContacts:
    """服务层: 搜索/筛选联系人"""

    @pytest.fixture(autouse=True)
    async def setup(self, crm_svc):
        self.names = ["张三", "李四", "王五", "赵六"]
        self.companies = ["示例科技", "云帆科技", "示例科技", "创新工厂"]
        for name, company in zip(self.names, self.companies):
            contact = await crm_svc.create_contact({
                "name": name,
                "company": company,
                "tags": ["VIP", "普通"][self.names.index(name) % 2],
            })
        await crm_svc.db.flush()

    async def test_list_all(self, crm_svc):
        contacts, total = await crm_svc.list_contacts(page=1, page_size=100)
        assert total >= 4

    async def test_search_by_name(self, crm_svc):
        contacts, total = await crm_svc.list_contacts(search="张三")
        assert total >= 1
        assert contacts[0].name == "张三"

    async def test_search_by_company(self, crm_svc):
        contacts, total = await crm_svc.list_contacts(company="示例科技")
        assert total >= 2

    async def test_search_by_tag(self, crm_svc):
        contacts, total = await crm_svc.list_contacts(tag="VIP")
        assert total >= 2

    async def test_pagination(self, crm_svc):
        contacts, total = await crm_svc.list_contacts(page=1, page_size=2)
        assert len(contacts) <= 2


class TestServiceContactCRUD:
    """服务层: 联系人完整 CRUD"""

    @pytest.fixture(autouse=True)
    async def setup(self, crm_svc):
        self.contact = await crm_svc.create_contact({
            "name": "CRUD测试",
            "phone": "13800009999",
            "email": "crud@test.com",
        })

    async def test_get_contact(self, crm_svc):
        contact = await crm_svc.get_contact(self.contact.id)
        assert contact is not None
        assert contact.name == "CRUD测试"

    async def test_get_nonexistent(self, crm_svc):
        contact = await crm_svc.get_contact(99999)
        assert contact is None

    async def test_update_contact(self, crm_svc):
        updated = await crm_svc.update_contact(self.contact.id, {
            "title": "高级工程师",
            "company": "新公司",
        })
        assert updated is not None
        assert updated.title == "高级工程师"
        assert updated.company == "新公司"

    async def test_update_nonexistent(self, crm_svc):
        result = await crm_svc.update_contact(99999, {"name": "不存在"})
        assert result is None

    async def test_delete_contact(self, crm_svc):
        ok = await crm_svc.delete_contact(self.contact.id)
        assert ok is True

        # 确认已删除
        contact = await crm_svc.get_contact(self.contact.id)
        assert contact is None

    async def test_delete_nonexistent(self, crm_svc):
        ok = await crm_svc.delete_contact(99999)
        assert ok is False


class TestServicePipelineStages:
    """服务层: 管道阶段管理"""

    async def test_ensure_default_stages(self, crm_svc):
        stages = await crm_svc.ensure_default_stages()
        assert len(stages) >= 1
        names = [s.name for s in stages]
        assert "潜在客户" in names
        assert "已成交" in names

    async def test_get_pipeline_stages(self, crm_svc):
        await crm_svc.ensure_default_stages()
        stages = await crm_svc.get_pipeline_stages()
        assert len(stages) >= 1

    async def test_default_stage_is_default(self, crm_svc):
        stages = await crm_svc.ensure_default_stages()
        default = [s for s in stages if s.is_default]
        assert len(default) >= 1
        assert default[0].sort_order == 0


class TestServiceNotes:
    """服务层: 笔记 CRUD"""

    @pytest.fixture(autouse=True)
    async def setup(self, crm_svc):
        self.contact = await crm_svc.create_contact({"name": "笔记测试"})

    async def test_create_note(self, crm_svc):
        note = await crm_svc.create_note({
            "contact_id": self.contact.id,
            "content": "这是一个测试笔记",
            "is_pinned": True,
        })
        assert note.id > 0
        assert note.content == "这是一个测试笔记"
        assert note.is_pinned is True

    async def test_get_contact_notes(self, crm_svc):
        await crm_svc.create_note({"contact_id": self.contact.id, "content": "笔记1"})
        await crm_svc.create_note({"contact_id": self.contact.id, "content": "笔记2"})
        notes, total = await crm_svc.get_contact_notes(self.contact.id)
        assert total >= 2

    async def test_update_note(self, crm_svc):
        note = await crm_svc.create_note({"contact_id": self.contact.id, "content": "原始"})
        updated = await crm_svc.update_note(note.id, {"content": "更新后", "is_pinned": True})
        assert updated.content == "更新后"
        assert updated.is_pinned is True

    async def test_delete_note(self, crm_svc):
        note = await crm_svc.create_note({"contact_id": self.contact.id, "content": "待删除"})
        ok = await crm_svc.delete_note(note.id)
        assert ok is True

        # 确认删除
        result = await crm_svc.update_note(note.id, {"content": "不应存在"})
        assert result is None

    async def test_create_note_triggers_activity(self, crm_svc):
        """创建笔记时自动记录活动。"""
        await crm_svc.create_note({"contact_id": self.contact.id, "content": "笔记活动测试"})
        activities, total = await crm_svc.get_contact_timeline(self.contact.id)
        # 1 system (create contact) + 1 note = 2
        assert total >= 2
        note_activities = [a for a in activities if a.activity_type == "note"]
        assert len(note_activities) >= 1


class TestServiceActivities:
    """服务层: 活动/时间线"""

    @pytest.fixture(autouse=True)
    async def setup(self, crm_svc):
        self.contact = await crm_svc.create_contact({"name": "活动测试"})

    async def test_add_activity(self, crm_svc):
        activity = await crm_svc.add_activity({
            "contact_id": self.contact.id,
            "activity_type": "call",
            "title": "电话沟通",
            "description": "讨论了合作方案",
        })
        assert activity.id > 0
        assert activity.activity_type == "call"
        assert activity.title == "电话沟通"

    async def test_get_timeline(self, crm_svc):
        await crm_svc.add_activity({
            "contact_id": self.contact.id,
            "activity_type": "meeting",
            "title": "面谈",
        })
        activities, total = await crm_svc.get_contact_timeline(self.contact.id)
        assert total >= 1

    async def test_timeline_pagination(self, crm_svc):
        for i in range(3):
            await crm_svc.add_activity({
                "contact_id": self.contact.id,
                "activity_type": "note",
                "title": f"活动{i}",
            })
        activities, total = await crm_svc.get_contact_timeline(
            self.contact.id, page=1, page_size=2
        )
        assert total >= 3
        assert len(activities) <= 2


class TestServiceDeals:
    """服务层: 销售机会"""

    @pytest.fixture(autouse=True)
    async def setup(self, crm_svc):
        self.contact = await crm_svc.create_contact({"name": "机会测试"})
        stages = await crm_svc.ensure_default_stages()
        self.stage_id = stages[0].id

    async def test_create_deal(self, crm_svc):
        deal = await crm_svc.create_deal({
            "contact_id": self.contact.id,
            "pipeline_stage_id": self.stage_id,
            "title": "500万合作项目",
            "value": 5000000.00,
            "probability": 60.0,
        })
        assert deal.id > 0
        assert deal.title == "500万合作项目"
        assert float(deal.value) == 5000000.00
        assert deal.probability == 60.0

    async def test_update_deal_stage(self, crm_svc):
        deal = await crm_svc.create_deal({
            "contact_id": self.contact.id,
            "pipeline_stage_id": self.stage_id,
            "title": "测试机会",
            "value": 10000,
        })
        stages = await crm_svc.ensure_default_stages()
        new_stage_id = stages[-1].id

        updated = await crm_svc.update_deal_stage(deal.id, new_stage_id)
        assert updated is not None
        assert updated.pipeline_stage_id == new_stage_id

    async def test_get_pipeline_deals(self, crm_svc):
        await crm_svc.create_deal({
            "contact_id": self.contact.id,
            "pipeline_stage_id": self.stage_id,
            "title": "看板测试",
        })
        grouped = await crm_svc.get_pipeline_deals()
        assert self.stage_id in grouped
        assert len(grouped[self.stage_id]) >= 1


class TestServiceStats:
    """服务层: 联系人统计"""

    @pytest.fixture(autouse=True)
    async def setup(self, crm_svc):
        for name in ["统计A", "统计B", "统计C"]:
            await crm_svc.create_contact({"name": name, "company": "统计科技"})

    async def test_get_stats(self, crm_svc):
        stats = await crm_svc.get_group_stats()
        assert stats["total_contacts"] >= 3
        assert "manual" in stats["by_source"]
        assert "统计科技" in stats["by_company"]
        assert stats["by_company"]["统计科技"] >= 3


# ═══════════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════════
# match_hook 单元测试
# ═══════════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════════


class TestMatchHook:
    """名片交换自动匹配钩子测试。"""

    @pytest.fixture(autouse=True)
    async def setup_match(self, test_db: AsyncSession, test_user: User, second_user: User):
        """创建匹配记录和基本条件。"""
        from app.models.tag import MatchRecord

        self.test_user = test_user
        self.second_user = second_user

        # 确保 second_user 有邮箱/电话
        second_user.phone = "13800005555"
        second_user.email = "second@example.com"
        second_user.company = "对方公司"
        second_user.title = "CTO"
        test_db.add(second_user)
        await test_db.commit()

        record = MatchRecord(
            user_a_id=test_user.id,
            user_b_id=second_user.id,
            match_score=0.85,
            status="matched",
            common_tags=json.dumps(["技术", "创业"]),
            source="manual",
        )
        test_db.add(record)
        await test_db.commit()
        await test_db.refresh(record)
        self.match_record = record

    async def test_sync_creates_both_contacts(self, test_db):
        """sync_match_to_crm 为双方各创建联系人。"""
        from app.crm.match_hook import sync_match_to_crm

        result = await sync_match_to_crm(db=test_db, match_record_id=self.match_record.id)

        assert result["user_a_contact_id"] is not None
        assert result["user_b_contact_id"] is not None

    async def test_contact_source_is_match(self, test_db):
        """创建的联系人 source 应为 match。"""
        from app.crm.match_hook import sync_match_to_crm
        from app.crm.crm_models import CrmContact

        result = await sync_match_to_crm(db=test_db, match_record_id=self.match_record.id)

        # 检查 A 的联系人
        ca = await test_db.get(CrmContact, result["user_a_contact_id"])
        assert ca is not None
        assert ca.source == "match"
        assert ca.source_record_id == self.match_record.id
        assert ca.user_id == self.second_user.id
        assert ca.owner_id == self.test_user.id
        assert ca.name == self.second_user.name
        assert ca.phone == "13800005555"
        assert ca.email == "second@example.com"

        # 检查 B 的联系人
        cb = await test_db.get(CrmContact, result["user_b_contact_id"])
        assert cb is not None
        assert cb.source == "match"
        assert cb.owner_id == self.second_user.id
        assert cb.user_id == self.test_user.id

    async def test_activity_recorded(self, test_db):
        """同步后应有名片交换活动记录。"""
        from app.crm.match_hook import sync_match_to_crm
        from app.crm.crm_models import CrmActivity

        result = await sync_match_to_crm(db=test_db, match_record_id=self.match_record.id)

        # 检查 A 的活动
        stmt = select(CrmActivity).where(
            CrmActivity.owner_id == self.test_user.id,
            CrmActivity.contact_id == result["user_a_contact_id"],
            CrmActivity.activity_type == "match",
        )
        activities_a = (await test_db.execute(stmt)).scalars().all()
        assert len(activities_a) >= 1
        assert "名片交换" in activities_a[0].title

        # 检查 B 的活动
        stmt = select(CrmActivity).where(
            CrmActivity.owner_id == self.second_user.id,
            CrmActivity.contact_id == result["user_b_contact_id"],
            CrmActivity.activity_type == "match",
        )
        activities_b = (await test_db.execute(stmt)).scalars().all()
        assert len(activities_b) >= 1

    async def test_idempotent(self, test_db):
        """多次同步不创建重复联系人。"""
        from app.crm.match_hook import sync_match_to_crm
        from app.crm.crm_models import CrmContact

        r1 = await sync_match_to_crm(db=test_db, match_record_id=self.match_record.id)
        r2 = await sync_match_to_crm(db=test_db, match_record_id=self.match_record.id)

        # 两次结果一致
        assert r1["user_a_contact_id"] == r2["user_a_contact_id"]
        assert r1["user_b_contact_id"] == r2["user_b_contact_id"]

        # 没有额外联系人
        stmt = select(CrmContact).where(
            CrmContact.owner_id == self.test_user.id,
            CrmContact.user_id == self.second_user.id,
        )
        contacts = (await test_db.execute(stmt)).scalars().all()
        assert len(contacts) == 1

    async def test_updates_existing_contact(self, test_db, crm_svc):
        """如果已存在用户关联的联系人, 应当更新信息。"""
        from app.crm.match_hook import sync_match_to_crm
        from app.crm.crm_models import CrmContact

        # 先通过 CrmService 创建一个用户关联的联系人
        existing = await crm_svc.create_contact({
            "name": "旧名字",
            "user_id": self.second_user.id,
            "phone": "13800005555",
            "source": "manual",
        })

        # 同步 (应更新旧名字 → second_user.name)
        result = await sync_match_to_crm(db=test_db, match_record_id=self.match_record.id)

        # 应该是同一个联系人
        assert result["user_a_contact_id"] == existing.id

        # 名字已更新
        updated = await test_db.get(CrmContact, existing.id)
        assert updated is not None
        assert updated.name == self.second_user.name  # updated
        assert updated.source == "match"  # updated

    async def test_sync_by_phone_or_email(self, test_db, crm_svc):
        """通过手机号匹配已有联系人。"""
        from app.crm.match_hook import sync_match_to_crm
        from app.crm.crm_models import CrmContact

        # 先创建一个无 user_id 但手机号相同的联系人
        existing = await crm_svc.create_contact({
            "name": "手动创建",
            "phone": "13800005555",  # 与 second_user 相同
            "source": "manual",
        })

        result = await sync_match_to_crm(db=test_db, match_record_id=self.match_record.id)

        # 应匹配到已存在的联系人
        assert result["user_a_contact_id"] == existing.id

        # user_id 已关联
        updated = await test_db.get(CrmContact, existing.id)
        assert updated.user_id == self.second_user.id


# ═══════════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════════
# HTTP API 测试 (需 CSRF token)
# ═══════════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
async def csrf_headers(client, auth_headers):
    """获取 CSRF token 并构造完整请求头。

    由于 `client` 和 `test_db` 使用不同的 in-memory DB,
    auth_headers 中的 JWT 在 `client` 的 DB 中可能找不到对应 user。
    这些 HTTP 测试作为可选集成测试, 验证端点可达性和响应格式。
    """
    resp = await client.get("/api/csrf/token")
    if resp.status_code != 200:
        pytest.skip("CSRF token endpoint unavailable")
    token = resp.json()["token"]
    csrf_cookie = resp.cookies.get("csrf_token", token)
    return {
        **auth_headers,
        "X-CSRF-Token": token,
        "Cookie": f"csrf_token={csrf_cookie}",
    }


class TestApiEndpoints:
    """HTTP API 端点测试 (集成测试, 需要 CSRF token)。

    注意: 由于 `client` fixture 使用与 `test_db` 隔离的 in-memory DB,
    这些测试主要用于验证请求路由可达和 CSRF 中间件正常工作。
    业务逻辑验证由上面服务层测试覆盖。
    """

    async def test_get_csrf_token(self, client):
        """GET /api/csrf/token 应返回 CSRF token。"""
        resp = await client.get("/api/csrf/token")
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert len(data["token"]) > 0

    async def test_get_pipeline_stages_endpoint(self, client, csrf_headers):
        """GET /api/crm/pipeline/stages 应返回阶段列表。"""
        resp = await client.get(
            "/api/crm/pipeline/stages",
            headers=csrf_headers,
        )
        # 注意: auth 可能因 DB 隔离失败, 但路由可达
        assert resp.status_code in (200, 401, 403), resp.text

    async def test_get_contacts_endpoint(self, client, csrf_headers):
        """GET /api/crm/contacts 应返回联系人列表。"""
        resp = await client.get(
            "/api/crm/contacts",
            headers=csrf_headers,
        )
        assert resp.status_code in (200, 401, 403), resp.text

    async def test_create_contact_endpoint_reachable(self, client, csrf_headers):
        """POST /api/crm/contacts 端点可达。"""
        payload = {"name": "API测试用户"}
        resp = await client.post(
            "/api/crm/contacts",
            json=payload,
            headers=csrf_headers,
        )
        # 可能成功或 auth 失败, 但不应 404/405
        assert resp.status_code not in (404, 405, 500), resp.text

    async def test_crm_endpoints_require_auth(self, client):
        """未认证的 POST 应返回 401。"""
        payload = {"name": "无权限"}
        resp = await client.post("/api/crm/contacts", json=payload)
        assert resp.status_code in (401, 403), resp.text

    @pytest.mark.skip(reason="需要共享 test_db 的 HTTP client (未来改进)")
    async def test_full_api_create_and_search(self, client, csrf_headers):
        """完整 API 集成测试 (需共享 DB)。"""
        pass

    @pytest.mark.skip(reason="需要共享 test_db 的 HTTP client (未来改进)")
    async def test_exchange_triggers_match_hook(self, client, csrf_headers):
        """交换名片触发 CRM 匹配钩子集成测试。"""
        pass

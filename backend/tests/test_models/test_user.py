"""用户模型单元测试。"""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

# 预先导入模型，使其注册到 Base.metadata，确保 test_db 能创建对应表
from app.models.user import User  # noqa: F401


class TestUserModel:
    """User SQLAlchemy 模型行为测试"""

    @pytest.mark.asyncio
    async def test_create_user(self, test_db):
        """创建 User 实例并持久化到数据库"""
        user = User(
            phone="13900000001",
            name="模型测试用户",
            password_hash="hashed_password_here",
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        assert user.id is not None
        assert user.id > 0
        assert user.phone == "13900000001"
        assert user.name == "模型测试用户"

    @pytest.mark.asyncio
    async def test_user_default_values(self, test_db):
        """验证 User 模型的默认值"""
        user = User(
            phone="13900000002",
            name="默认值测试",
            password_hash="hashed",
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        assert user.role == "user"
        assert user.membership_tier == "free"
        assert user.company == ""
        assert user.title == ""
        assert user.intro == ""

    @pytest.mark.asyncio
    async def test_user_unique_phone(self, test_db):
        """相同手机号应违反唯一约束"""
        user1 = User(phone="13900000003", name="用户A", password_hash="hash1")
        test_db.add(user1)
        await test_db.commit()

        user2 = User(phone="13900000003", name="用户B", password_hash="hash2")
        test_db.add(user2)
        with pytest.raises(IntegrityError):
            await test_db.commit()
        await test_db.rollback()

    @pytest.mark.asyncio
    async def test_user_timestamps(self, test_db):
        """created_at 和 updated_at 应在创建时自动生成"""
        user = User(
            phone="13900000004",
            name="时间戳测试",
            password_hash="hash",
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        assert user.created_at is not None
        assert user.updated_at is not None

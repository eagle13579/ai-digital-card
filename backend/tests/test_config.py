"""配置层单元测试 — 验证 Settings 模型的行为和验证逻辑。"""

from __future__ import annotations

import os
from unittest import mock

import pytest

from app.config import Settings


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """清除 Settings 的 pydantic 缓存，使每个测试类获得独立 settings。"""
    # pydantic-settings 使用 lru_cache 或类级别的 _settings 缓存，
    # 我们直接通过环境变量控制测试行为，不依赖共享 settings 实例。
    yield


class TestSettingsDefaults:
    """验证 Settings 默认值正确性。"""

    def test_app_name_default(self):
        """APP_NAME 默认值为 'AI数智名片'"""
        with mock.patch.dict(os.environ, {"JWT_SECRET": "test-secret-key"}):
            s = Settings()
            assert s.APP_NAME == "AI数智名片"

    def test_database_url_default(self):
        """DATABASE_URL 默认值为 SQLite 内存数据库"""
        with mock.patch.dict(os.environ, {"JWT_SECRET": "test-secret-key"}):
            s = Settings()
            assert "sqlite" in s.DATABASE_URL

    def test_algorithm_default(self):
        """默认算法为 HS256"""
        with mock.patch.dict(os.environ, {"JWT_SECRET": "test-secret-key"}):
            s = Settings()
            assert s.ALGORITHM == "HS256"

    def test_access_token_expire_default(self):
        """默认 access_token 过期时间为 60 分钟"""
        with mock.patch.dict(os.environ, {"JWT_SECRET": "test-secret-key"}):
            s = Settings()
            assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 60

    def test_cors_origins_default(self):
        """CORS_ORIGINS 默认包含 localhost 和 liankebao.top"""
        with mock.patch.dict(os.environ, {"JWT_SECRET": "test-secret-key"}):
            s = Settings()
            assert "localhost" in s.CORS_ORIGINS
            assert "liankebao.top" in s.CORS_ORIGINS

    def test_embedding_defaults(self):
        """Embedding 相关参数默认值"""
        with mock.patch.dict(os.environ, {"JWT_SECRET": "test-secret-key"}):
            s = Settings()
            assert s.USE_VECTOR_SEARCH is True
            assert s.EMBEDDING_DIM == 768
            assert s.VECTOR_TOP_K == 50


class TestSettingsValidation:
    """验证 Settings 的 field_validator 和属性行为。"""

    def test_jwt_secret_dev_env_accepts_weak(self):
        """开发环境下，弱 JWT_SECRET 应通过验证"""
        with mock.patch.dict(os.environ, {"JWT_SECRET": "weak-test-key", "ENV": "development"}):
            s = Settings()
            assert s.JWT_SECRET == "weak-test-key"

    def test_jwt_secret_production_requires_strong(self):
        """生产环境下，弱 JWT_SECRET 应引发 ValueError"""
        with mock.patch.dict(os.environ, {"JWT_SECRET": "change-me", "ENV": "production"}):
            with pytest.raises(ValueError, match="强随机JWT_SECRET"):
                Settings()

    def test_jwt_secret_production_strong_ok(self):
        """生产环境下，强 JWT_SECRET 应通过验证"""
        with mock.patch.dict(
            os.environ,
            {"JWT_SECRET": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2", "ENV": "production"},
        ):
            s = Settings()
            assert s.JWT_SECRET == "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"

    def test_docs_enabled_dev(self):
        """开发环境下 docs_enabled 应为 True"""
        with mock.patch.dict(os.environ, {"JWT_SECRET": "test-secret-key", "ENV": "development"}):
            s = Settings()
            assert s.docs_enabled is True

    def test_docs_disabled_production(self):
        """生产环境下 docs_enabled 应为 False"""
        with mock.patch.dict(os.environ, {"JWT_SECRET": "test-secret-key", "ENV": "production"}):
            s = Settings()
            assert s.docs_enabled is False

    def test_docs_force_disabled(self):
        """DISABLE_DOCS=true 应强制禁用 docs"""
        with mock.patch.dict(
            os.environ, {"JWT_SECRET": "test-secret-key", "ENV": "development", "DISABLE_DOCS": "true"}
        ):
            s = Settings()
            assert s.docs_enabled is False

    def test_redis_url_builds_correctly(self):
        """REDIS_URL 属性应正确拼接"""
        with mock.patch.dict(
            os.environ,
            {
                "JWT_SECRET": "test-secret-key",
                "REDIS_HOST": "myredis",
                "REDIS_PORT": "6380",
                "REDIS_DB": "1",
            },
        ):
            s = Settings()
            assert "myredis" in s.REDIS_URL
            assert "6380" in s.REDIS_URL

    def test_video_config_defaults(self):
        """视频上传配置默认值"""
        with mock.patch.dict(os.environ, {"JWT_SECRET": "test-secret-key"}):
            s = Settings()
            assert s.VIDEO_MAX_SIZE == 100 * 1024 * 1024
            assert "mp4" in s.VIDEO_ALLOWED_EXTENSIONS
            assert "video/mp4" in s.VIDEO_ALLOWED_MIME_TYPES

"""密钥管理器 (SecretManager) 测试 — 加密/解密 & 环境变量优先级 & 错误处理"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest


class TestSecretManagerBasics:
    """SecretManager 基础功能测试"""

    def test_get_from_environment_variable(self):
        """环境变量优先级最高 — get() 应优先返回环境变量值"""
        from key_manager import SecretManager

        secrets = SecretManager()
        with mock.patch.dict(os.environ, {"TEST_MY_KEY": "env_value"}, clear=False):
            value = secrets.get("TEST_MY_KEY", "default_value")
            assert value == "env_value"

    def test_get_returns_default_when_not_set(self):
        """密钥不存在时返回默认值"""
        from key_manager import SecretManager

        secrets = SecretManager()
        value = secrets.get("THIS_KEY_DOES_NOT_EXIST_XYZ", "my_default")
        assert value == "my_default"

    def test_get_returns_empty_string_when_no_default(self):
        """密钥不存在且无默认值时返回空字符串"""
        from key_manager import SecretManager

        secrets = SecretManager()
        value = secrets.get("THIS_KEY_ALSO_DOES_NOT_EXIST")
        assert value == ""

    def test_get_or_raise_when_not_set(self):
        """get_or_raise() 在密钥不存在时应抛出 ValueError"""
        from key_manager import SecretManager

        secrets = SecretManager()
        with pytest.raises(ValueError, match="未配置"):
            secrets.get_or_raise("NONEXISTENT_SECRET_KEY_12345")

    def test_get_or_raise_when_set(self):
        """get_or_raise() 在密钥存在时应返回值"""
        from key_manager import SecretManager

        secrets = SecretManager()
        with mock.patch.dict(os.environ, {"EXISTENT_KEY": "found_value"}, clear=False):
            value = secrets.get_or_raise("EXISTENT_KEY")
            assert value == "found_value"

    def test_env_var_priority_over_default(self):
        """环境变量优先于默认值"""
        from key_manager import SecretManager

        secrets = SecretManager()
        with mock.patch.dict(os.environ, {"PRIORITY_TEST_KEY": "from_env"}, clear=False):
            value = secrets.get("PRIORITY_TEST_KEY", "default_value")
            assert value == "from_env"


class TestSecretManagerEncryption:
    """加密/解密功能测试"""

    def test_encrypt_and_decrypt_env_file(self, tmp_path):
        """encrypt_env_file 加密后再 decrypt_env_file 解密应得到原文"""
        from key_manager import encrypt_env_file, decrypt_env_file

        master_key = "my-test-master-key-12345"
        env_path = tmp_path / ".env"
        env_path.write_text(
            "DEEPSEEK_API_KEY=sk-xxxx\nDATABASE_URL=postgresql://localhost/db\n",
            encoding="utf-8",
        )

        # 加密
        encrypted_path = encrypt_env_file(env_path, master_key)
        assert encrypted_path.exists()
        content = json.loads(encrypted_path.read_text(encoding="utf-8"))
        assert content["v"] == 1
        assert "ciphertext" in content
        assert "nonce" in content

        # 解密
        decrypted = decrypt_env_file(encrypted_path, master_key)
        assert "DEEPSEEK_API_KEY=sk-xxxx" in decrypted
        assert "DATABASE_URL=postgresql://localhost/db" in decrypted

    def test_decrypt_with_wrong_key_raises_error(self, tmp_path):
        """错误的 master_key 解密应抛出异常"""
        from key_manager import encrypt_env_file, decrypt_env_file

        env_path = tmp_path / ".env"
        env_path.write_text("MY_KEY=my_value\n", encoding="utf-8")

        encrypted_path = encrypt_env_file(env_path, "correct-master-key")
        with pytest.raises(Exception):
            decrypt_env_file(encrypted_path, "wrong-master-key")

    def test_encrypt_nonexistent_env_file_raises(self, tmp_path):
        """加密不存在的 .env 文件应抛出 FileNotFoundError"""
        from key_manager import encrypt_env_file

        nonexistent = tmp_path / "nonexistent.env"
        with pytest.raises(FileNotFoundError):
            encrypt_env_file(nonexistent, "some-key")

    def test_decrypt_nonexistent_encrypted_file_raises(self, tmp_path):
        """解密不存在的 .env.encrypted 文件应抛出 FileNotFoundError"""
        from key_manager import decrypt_env_file

        nonexistent = tmp_path / "nonexistent.env.encrypted"
        with pytest.raises(FileNotFoundError):
            decrypt_env_file(nonexistent, "some-key")

    def test_parse_env_content_simple(self):
        """_parse_env_content 正确解析 KEY=VALUE 格式"""
        from key_manager import SecretManager

        content = """DEEPSEEK_API_KEY=sk-xxxx
DATABASE_URL=postgresql://localhost:5432/db
# 这是注释
EMPTY_VALUE=
"""
        result = SecretManager._parse_env_content(content)
        assert result["DEEPSEEK_API_KEY"] == "sk-xxxx"
        assert result["DATABASE_URL"] == "postgresql://localhost:5432/db"
        assert "EMPTY_VALUE" in result
        assert result["EMPTY_VALUE"] == ""

    def test_parse_env_content_with_quotes(self):
        """_parse_env_content 正确处理引号包裹的值"""
        from key_manager import SecretManager

        content = 'KEY1="quoted_value"\nKEY2=\'single_quoted\'\nKEY3=plain'
        result = SecretManager._parse_env_content(content)
        assert result["KEY1"] == "quoted_value"
        assert result["KEY2"] == "single_quoted"
        assert result["KEY3"] == "plain"


class TestSecretManagerEncryptedFile:
    """从加密文件读取密钥的集成测试"""

    def test_get_from_encrypted_file(self, tmp_path, monkeypatch):
        """通过加密文件读取密钥"""
        from key_manager import SecretManager, encrypt_env_file

        master_key = "test-master-for-encrypted"
        # 创建 .env 并加密
        backend_dir = tmp_path / "backend"
        backend_dir.mkdir()
        env_path = backend_dir / ".env"
        env_path.write_text("DEEPSEEK_API_KEY=sk-from-encrypted\n", encoding="utf-8")

        encrypt_env_file(env_path, master_key)

        # 创建 SecretManager 指向临时目录
        monkeypatch.setenv("SECRET_MASTER_KEY", master_key)
        secrets = SecretManager(backend_dir=str(backend_dir))
        # 确保没有环境变量覆盖
        if "DEEPSEEK_API_KEY" in os.environ:
            monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

        value = secrets.get("DEEPSEEK_API_KEY", "default")
        assert value == "sk-from-encrypted"

    def test_encrypted_file_not_available_without_master_key(self, tmp_path):
        """没有 SECRET_MASTER_KEY 时无法从加密文件读取"""
        from key_manager import SecretManager

        # 确保环境变量中没有 MASTER_KEY
        with mock.patch.dict(os.environ, {}, clear=True):
            secrets = SecretManager(backend_dir=str(tmp_path))
            assert secrets.is_encrypted_available() is False

    def test_is_configured_checks_sources(self):
        """is_configured() 应检查是否有任一密钥源"""
        from key_manager import SecretManager

        # 当有 SECRET_MASTER_KEY 环境变量时
        with mock.patch.dict(os.environ, {"SECRET_MASTER_KEY": "some-key"}, clear=True):
            assert SecretManager.is_configured() is True

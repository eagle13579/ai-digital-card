"""Tests: WebhookSigner — HMAC-SHA256 签名/验证/密钥生成/篡改检测。

覆盖 10 个测试用例:
  1. sign 返回 64 字符 hex 字符串
  2. sign 使用正确密钥
  3. sign 不同 payload 产生不同签名
  4. verify 正确签名返回 True
  5. verify 错误签名返回 False (时序安全比较)
  6. verify 空字符串签名返回 False
  7. tamper: payload 篡改检测
  8. tamper: secret 篡改检测
  9. generate_secret 返回预期长度
  10. generate_secret 生成的密钥足够随机
"""

import hashlib
import hmac
import json
import string

import pytest

from app.services.webhook_signer import generate_secret, sign, verify


# ── sign ────────────────────────────────────────────────────────────────────


class TestSign:
    """sign() 函数测试 (3 用例)。"""

    def test_returns_64_char_hex(self):
        """签名结果为 64 字符的十六进制字符串。"""
        sig = sign(b'{"event": "test"}', "mysecret")
        assert isinstance(sig, str)
        assert len(sig) == 64
        # 全部是十六进制字符
        assert all(c in string.hexdigits for c in sig)

    def test_correct_key_produces_expected(self):
        """用已知输入验证 HMAC-SHA256 计算结果。"""
        payload = b"hello"
        secret = "key"
        expected = hmac.new(
            secret.encode("utf-8"), payload, hashlib.sha256
        ).hexdigest()
        assert sign(payload, secret) == expected

    def test_different_payload_different_signature(self):
        """不同 payload 产生不同的签名。"""
        s1 = sign(b'{"event": "a"}', "secret")
        s2 = sign(b'{"event": "b"}', "secret")
        assert s1 != s2

    def test_sign_rejects_non_bytes_payload(self):
        """payload 必须为 bytes 类型。"""
        with pytest.raises(TypeError, match="payload"):
            sign('{"event": "a"}', "secret")  # type: ignore

    def test_sign_rejects_non_str_secret(self):
        """secret 必须为 str 类型。"""
        with pytest.raises(TypeError, match="secret"):
            sign(b"hello", 12345)  # type: ignore

    def test_sign_empty_payload(self):
        """空 payload 也能正常签名。"""
        sig = sign(b"", "secret")
        assert len(sig) == 64

    def test_sign_empty_secret(self):
        """空密钥也能签名（但不推荐在生产使用）。"""
        sig = sign(b"hello", "")
        assert len(sig) == 64

    def test_sign_unicode_payload(self):
        """中文字符串 payload 正常签名。"""
        data = {"event": "card.created", "数据": "名片"}
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        sig = sign(body, "my-key")
        assert len(sig) == 64
        assert verify(body, sig, "my-key") is True


# ── verify ──────────────────────────────────────────────────────────────────


class TestVerify:
    """verify() 函数测试 (4 用例)。"""

    def test_valid_signature(self):
        """正确签名验证通过。"""
        payload = b'{"event": "card.created", "id": 42}'
        secret = "sk-test-123456"
        sig = sign(payload, secret)
        assert verify(payload, sig, secret) is True

    def test_invalid_signature(self):
        """错误签名验证不通过。"""
        payload = b"valid message"
        secret = "correct-secret"
        wrong_sig = "a" * 64  # 全部是 'a'
        assert verify(payload, wrong_sig, secret) is False

    def test_empty_signature(self):
        """空签名验证不通过。"""
        assert verify(b"data", "", "secret") is False

    def test_none_signature(self):
        """None 签名验证不通过。"""
        assert verify(b"data", None, "secret") is False  # type: ignore


# ── Tamper 检测 ─────────────────────────────────────────────────────────────


class TestTamperDetection:
    """篡改检测测试 (2 用例)。"""

    def test_tampered_payload(self):
        """payload 被篡改后验证失败。"""
        secret = "supersecret"
        original = b'{"event": "card.created", "amount": 100}'
        sig = sign(original, secret)

        # 篡改 payload
        tampered = b'{"event": "card.created", "amount": 99999}'
        assert verify(tampered, sig, secret) is False

    def test_wrong_secret(self):
        """使用错误密钥验证失败。"""
        payload = b"confidential data"
        sig = sign(payload, "correct-key")
        assert verify(payload, sig, "wrong-key") is False


# ── generate_secret ─────────────────────────────────────────────────────────


class TestGenerateSecret:
    """generate_secret() 测试 (3 用例)。"""

    def test_default_length(self):
        """默认 32 字节 = 64 hex 字符。"""
        secret = generate_secret()
        assert isinstance(secret, str)
        assert len(secret) == 64
        assert all(c in string.hexdigits for c in secret)

    @pytest.mark.parametrize("byte_len, expected_hex_len", [
        (16, 32),
        (24, 48),
        (32, 64),
        (64, 128),
    ])
    def test_custom_length(self, byte_len, expected_hex_len):
        """指定字节长度，hex 长度 = byte_len * 2。"""
        secret = generate_secret(byte_len)
        assert len(secret) == expected_hex_len

    def test_rejects_short_length(self):
        """拒绝小于 16 字节的密钥。"""
        with pytest.raises(ValueError, match="密钥长度"):
            generate_secret(8)

    def test_secrets_are_random(self):
        """多次调用生成的密钥不同（随机性验证）。"""
        secrets = {generate_secret() for _ in range(100)}
        # 极低概率碰撞，100 次全部不同
        assert len(secrets) == 100


# ── End-to-end 集成式 ──────────────────────────────────────────────────────


class TestEndToEnd:
    """端到端测试 (1 用例)。"""

    def test_full_workflow(self):
        """完整流程: 生成密钥 → 签名 → 验证 → 篡改检测。"""
        # 生成密钥
        secret = generate_secret()

        # 构造 payload
        payload = json.dumps(
            {"event": "card.created", "timestamp": "2026-07-01T12:00:00Z", "data": {"id": 1}},
            ensure_ascii=False,
        ).encode("utf-8")

        # 签名
        sig = sign(payload, secret)

        # 验证 (正确)
        assert verify(payload, sig, secret) is True

        # 篡改检测 (错误 payload)
        tampered = payload + b"x"
        assert verify(tampered, sig, secret) is False

        # 篡改检测 (错误密钥)
        assert verify(payload, sig, generate_secret()) is False

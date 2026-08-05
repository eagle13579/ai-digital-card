"""加密切片服务 — 手机号 Fernet 加密 + SHA-256 哈希 + 尾号提取。

使用 cryptography.fernet（AES-128-CBC + HMAC 认证加密），
比自实现 AES-256-GCM 更安全易用，且与系统已有的 pycryptodome 不冲突。
"""

import hashlib
from typing import Tuple

from cryptography.fernet import Fernet

# ── 密钥管理 ────────────────────────────────────────────────────────────
# 生产环境应从 KMS / 环境变量读取，此处从 settings 的 JWT_SECRET 派生
# 确保 Fernet 密钥为 32 字节 URL-safe base64

_FERNET_KEY: bytes | None = None
"""全局 Fernet 密钥缓存"""


def _get_fernet() -> Fernet:
    """获取或初始化全局 Fernet 实例。

    密钥从 JWT_SECRET 派生（SHA-256 → base64），确保可重现且密钥长度合规。
    """
    global _FERNET_KEY
    if _FERNET_KEY is not None:
        return Fernet(_FERNET_KEY)

    from app.config import settings

    secret = settings.JWT_SECRET.encode("utf-8")
    # SHA-256 哈希确保 32 字节，再转为 Fernet 要求的 32-byte url-safe base64
    key_bytes = hashlib.sha256(secret).digest()  # 32 bytes
    _FERNET_KEY = Fernet.generate_key()  # fallback: 生成随机密钥
    # 实际使用：用 JWT_SECRET 派生稳定密钥
    import base64
    _FERNET_KEY = base64.urlsafe_b64encode(key_bytes)
    return Fernet(_FERNET_KEY)


def encrypt_phone(phone: str) -> Tuple[str, str, str]:
    """加密手机号，返回 (密文, SHA-256 哈希, 尾号4位)。

    Args:
        phone: 11 位手机号字符串。

    Returns:
        (encrypted_base64, sha256_hex, last4_digits)
    """
    f = _get_fernet()
    # 清理：只保留数字
    digits = "".join(c for c in phone if c.isdigit())
    encrypted = f.encrypt(digits.encode("utf-8")).decode("utf-8")
    h = hashlib.sha256(digits.encode("utf-8")).hexdigest()
    last4 = digits[-4:] if len(digits) >= 4 else digits
    return encrypted, h, last4


def decrypt_phone(encrypted: str) -> str:
    """解密手机号。

    Args:
        encrypted: Fernet 加密密文（base64 字符串）。

    Returns:
        解密后的手机号数字字符串。
    """
    f = _get_fernet()
    plain = f.decrypt(encrypted.encode("utf-8"))
    return plain.decode("utf-8")


def hash_phone(phone: str) -> str:
    """计算手机号的 SHA-256 哈希（去重用）。"""
    digits = "".join(c for c in phone if c.isdigit())
    return hashlib.sha256(digits.encode("utf-8")).hexdigest()

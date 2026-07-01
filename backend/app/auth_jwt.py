"""
JWT 工具模块 — 支持 RS256（非对称）+ HS256（对称）双算法。

设计原则：
- 签发 token 优先使用 RS256（更安全），开发环境自动生成 RSA 密钥对。
- 验证 token 时尝试 RS256 → HS256 回退，确保新旧 token 均能通过。
- 无单点故障：即使 RSA 密钥不可用，自动降级到 HS256。
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import JWTError, jwt

from app.config import settings

logger = logging.getLogger(__name__)

# ── RSA 密钥加载 / 自动生成 ──────────────────────────────────────────────

_rsa_private_key: Optional[str] = None
_rsa_public_key: Optional[str] = None


def _ensure_data_dir(path: str) -> Path:
    """确保文件所在目录存在。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _generate_rsa_keypair(private_path: str, public_path: str) -> None:
    """生成 2048 位 RSA 密钥对并写入 PEM 文件。"""
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    priv_path = _ensure_data_dir(private_path)
    priv_path.write_bytes(private_pem)
    logger.info("RSA 私钥已生成 → %s", priv_path)

    pub_path = Path(public_path)
    pub_path.write_bytes(public_pem)
    logger.info("RSA 公钥已生成 → %s", pub_path)


def load_rsa_keys() -> tuple[Optional[str], Optional[str]]:
    """加载 RSA 密钥对。开发环境自动生成，生产环境从配置路径读取。"""
    global _rsa_private_key, _rsa_public_key

    if _rsa_private_key is not None and _rsa_public_key is not None:
        return _rsa_private_key, _rsa_public_key

    private_path = settings.RSA_PRIVATE_KEY_PATH
    public_path = settings.RSA_PUBLIC_KEY_PATH

    # 检查密钥文件是否已存在
    priv_file = Path(private_path)
    pub_file = Path(public_path)

    if not priv_file.exists() or not pub_file.exists():
        # 开发环境：自动生成
        if not os.getenv("RSA_PRIVATE_KEY_PATH") and not os.getenv("RSA_PUBLIC_KEY_PATH"):
            logger.info("RSA 密钥对不存在，自动生成（开发模式）…")
            try:
                _generate_rsa_keypair(private_path, public_path)
            except Exception as exc:
                logger.warning("RSA 密钥对生成失败 %s，将使用 HS256 降级", exc)
                return None, None
        else:
            logger.warning(
                "RSA 密钥路径已配置但文件不存在: %s / %s",
                private_path, public_path,
            )
            return None, None

    # 读取密钥
    try:
        _rsa_private_key = priv_file.read_text()
        _rsa_public_key = pub_file.read_text()
        logger.info("RSA 密钥对加载成功")
    except Exception as exc:
        logger.warning("RSA 密钥读取失败 %s，将使用 HS256 降级", exc)
        return None, None

    return _rsa_private_key, _rsa_public_key


# ── JWT 签发 ────────────────────────────────────────────────────────────


def create_access_token(data: dict) -> str:
    """签发 JWT token。

    优先使用 RS256（非对称签名），若 RSA 密钥不可用则降级到 HS256（对称签名）。

    Args:
        data: 需要编码到 token 中的用户数据（必须包含 "sub" 字段）。

    Returns:
        签发的 JWT token 字符串。
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    # 尝试 RS256
    private_key, _ = load_rsa_keys()
    if private_key:
        try:
            return jwt.encode(to_encode, private_key, algorithm="RS256")
        except Exception as exc:
            logger.warning("RS256 签名失败 %s，降级到 HS256", exc)

    # 降级 HS256
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)


# ── JWT 验证 ────────────────────────────────────────────────────────────


def decode_access_token(token: str) -> dict:
    """解码并验证 JWT token。

    验证顺序：
    1. RS256（使用 RSA 公钥）
    2. HS256（使用 JWT_SECRET，向后兼容已有 token）

    Args:
        token: JWT token 字符串。

    Returns:
        解码后的 payload（dict）。

    Raises:
        JWTError: 所有算法均验证失败。
    """
    # 1. 尝试 RS256
    _, public_key = load_rsa_keys()
    if public_key:
        try:
            payload = jwt.decode(token, public_key, algorithms=["RS256"])
            return payload
        except JWTError:
            pass  # 不是 RS256 签名，继续尝试 HS256

    # 2. 尝试 HS256（向后兼容）
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except JWTError:
        raise JWTError("JWT 验证失败: 已尝试 RS256 和 HS256，均未通过")


# ── 公钥端点辅助 ────────────────────────────────────────────────────────


def get_jwt_public_key_pem() -> Optional[str]:
    """获取 RSA 公钥 PEM（用于 /.well-known/jwks.json 等端点）。"""
    _, public_key = load_rsa_keys()
    return public_key

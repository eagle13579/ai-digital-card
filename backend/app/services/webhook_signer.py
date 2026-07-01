"""Webhook HMAC-SHA256 签名服务。

纯 Python stdlib 实现，无额外依赖。
提供 sign / verify / generate_secret 三个核心函数。

用法:
    from app.services.webhook_signer import sign, verify, generate_secret

    secret = generate_secret()
    payload = b'{"event":"card.created","data":{}}'
    signature = sign(payload, secret)
    assert verify(payload, signature, secret)

签名格式: HMAC-SHA256 hex 编码 (64 位小写十六进制字符串)。
"""

import hashlib
import hmac
import secrets


def sign(payload: bytes, secret: str) -> str:
    """对 payload 使用 HMAC-SHA256 签名，返回 hex 字符串。

    参数:
        payload: 待签名的消息体（UTF-8 编码的 bytes）
        secret:  签名密钥（字符串）

    返回:
        64 字符的 HMAC-SHA256 hex 摘要
    """
    if not isinstance(payload, bytes):
        raise TypeError(f"payload 必须是 bytes，收到 {type(payload).__name__}")
    if not isinstance(secret, str):
        raise TypeError(f"secret 必须是 str，收到 {type(secret).__name__}")

    key = secret.encode("utf-8")
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


def verify(payload: bytes, signature: str, secret: str) -> bool:
    """验证 payload 的 HMAC-SHA256 签名是否匹配。

    使用 hmac.compare_digest 进行常量时间比较，防止时序攻击。

    参数:
        payload:   原始消息体 bytes
        signature: 待验证的签名 hex 字符串
        secret:    签名密钥

    返回:
        签名有效返回 True，否则 False
    """
    expected = sign(payload, secret)
    # 常量时间比较，防止时序侧信道攻击
    return hmac.compare_digest(expected, signature)


def generate_secret(length: int = 32) -> str:
    """生成安全的随机密钥，适用于 Webhook HMAC-SHA256 签名。

    使用 secrets.token_hex (密码学安全随机数生成器)，返回 hex 字符串。
    默认长度 32 字节 = 64 hex 字符，提供 256 位熵。

    参数:
        length: 随机字节数（默认 32），输出字符串长度 = length * 2

    返回:
        Hex 编码的安全随机字符串
    """
    if length < 16:
        raise ValueError(f"密钥长度不能小于 16 字节，收到 {length}")
    return secrets.token_hex(length)

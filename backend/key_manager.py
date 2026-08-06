"""
AI数智名片 — 密钥管理器 (SecretManager)
=========================================
职责:
  1. 从系统环境变量 (os.environ) 优先加载密钥
  2. 回退到加密的 .env.encrypted 文件 (AES-256-GCM)
  3. 支持通过 SECRET_MASTER_KEY 环境变量解密
  4. 提供加密/解密 .env 的辅助方法

用法:
  from key_manager import SecretManager
  secrets = SecretManager()
  api_key = secrets.get("DEEPSEEK_API_KEY")
"""

import base64
import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── 加密配置 ──────────────────────────────────────────────────────────────
ENCRYPTED_ENV_FILE = ".env.encrypted"
"""加密密钥存储文件路径 (相对于 backend/)"""

MASTER_KEY_ENV_VAR = "SECRET_MASTER_KEY"
"""用于解密 .env.encrypted 的主密钥环境变量名"""


# ═══════════════════════════════════════════════════════════════════════════
# 加密原语 — AES-256-GCM
# ═══════════════════════════════════════════════════════════════════════════

def _derive_key(master_key: str) -> bytes:
    """将主密钥字符串 (任意长度) 通过 SHA-256 派生为 32 字节 AES 密钥。"""
    import hashlib
    return hashlib.sha256(master_key.encode("utf-8")).digest()


def _encrypt_env_file(env_path: Path, master_key: str) -> str:
    """
    读取 .env 文件内容 → AES-256-GCM 加密 → 返回 Base64 编码密文。

    返回格式 (JSON):
      {
        "v": 1,
        "ciphertext": "<base64>",
        "nonce": "<base64>",
        "tag": "<base64>"
      }
    """
    from cryptography.fernet import Fernet
    raise NotImplementedError("加密请使用 EncryptEnvTool 或 encrypt_env_file() 函数")


def encrypt_env_file(env_path: Path, master_key: str, output_path: Optional[Path] = None) -> Path:
    """
    加密 .env 文件并写入 .env.encrypted。

    Args:
        env_path: .env 文件路径
        master_key: 主密钥 (任意长度字符串)
        output_path: 输出路径, 默认与 env_path 同目录的 .env.encrypted

    Returns:
        加密文件路径
    """
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    if not env_path.exists():
        raise FileNotFoundError(f".env 文件不存在: {env_path}")

    if output_path is None:
        output_path = env_path.parent / ENCRYPTED_ENV_FILE

    env_content = env_path.read_bytes()
    key = _derive_key(master_key)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # GCM 推荐 12 字节 nonce
    ciphertext = aesgcm.encrypt(nonce, env_content, None)

    payload = {
        "v": 1,
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
        "nonce": base64.b64encode(nonce).decode("ascii"),
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_path.chmod(0o600)  # 仅 owner 可读写
    logger.info("✅ .env 已加密 → %s (AES-256-GCM)", output_path)
    return output_path


def decrypt_env_file(encrypted_path: Path, master_key: str) -> str:
    """
    解密 .env.encrypted 文件并返回明文内容。

    Returns:
        解密后的 .env 文件内容字符串
    """
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    if not encrypted_path.exists():
        raise FileNotFoundError(f"加密文件不存在: {encrypted_path}")

    payload = json.loads(encrypted_path.read_text(encoding="utf-8"))
    ciphertext = base64.b64decode(payload["ciphertext"])
    nonce = base64.b64decode(payload["nonce"])
    key = _derive_key(master_key)

    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")


# ═══════════════════════════════════════════════════════════════════════════
# SecretManager — 密钥访问门面
# ═══════════════════════════════════════════════════════════════════════════

class SecretManager:
    """
    密钥管理器 — 统一的密钥访问入口。

    优先级:
      1. 系统环境变量 (os.environ) — 生产环境优先
      2. 加密的 .env.encrypted 文件 — 通过 SECRET_MASTER_KEY 解密
      3. 默认值 (如果提供)

    用法:
        secrets = SecretManager()
        api_key = secrets.get("DEEPSEEK_API_KEY")
        # 或带默认值
        db_url = secrets.get("DATABASE_URL", "sqlite:///./test.db")
    """

    def __init__(self, backend_dir: Optional[str] = None):
        self._backend_dir = Path(backend_dir) if backend_dir else Path(__file__).parent.resolve()
        self._encrypted_path = self._backend_dir / ENCRYPTED_ENV_FILE
        self._master_key: Optional[str] = os.environ.get(MASTER_KEY_ENV_VAR)
        self._decrypted_cache: Optional[dict[str, str]] = None

    # ── 公共接口 ──────────────────────────────────────────────────────────

    def get(self, key: str, default: str = "") -> str:
        """
        获取密钥值。

        查找顺序:
          1. os.environ (系统环境变量, 最优先)
          2. .env.encrypted (加密文件, 通过 SECRET_MASTER_KEY 解密)
          3. default (兜底默认值)

        Args:
            key: 密钥名称 (如 "DEEPSEEK_API_KEY")
            default: 兜底默认值

        Returns:
            密钥值字符串, 未找到则返回 default
        """
        # 1) 系统环境变量优先
        value = os.environ.get(key)
        if value is not None:
            return value

        # 2) 尝试从加密文件解密
        value = self._get_from_encrypted(key)
        if value is not None:
            return value

        # 3) 兜底默认值
        return default

    def get_or_raise(self, key: str) -> str:
        """
        获取密钥值, 未找到则抛出 ValueError。

        Raises:
            ValueError: 密钥在所有源中均未找到
        """
        value = self.get(key)
        if not value:
            raise ValueError(
                f"❌ 密钥 '{key}' 未配置。\n"
                f"   请通过环境变量或加密文件设置。"
            )
        return value

    def is_encrypted_available(self) -> bool:
        """检查加密文件是否存在且可解密 (仅当 SECRET_MASTER_KEY 已设置)。"""
        if not self._master_key:
            return False
        if not self._encrypted_path.exists():
            return False
        try:
            decrypt_env_file(self._encrypted_path, self._master_key)
            return True
        except Exception:
            return False

    # ── 内部方法 ──────────────────────────────────────────────────────────

    def _get_from_encrypted(self, key: str) -> Optional[str]:
        """从加密的 .env.encrypted 文件中读取密钥。"""
        if not self._master_key:
            return None

        if self._decrypted_cache is None:
            try:
                plaintext = decrypt_env_file(self._encrypted_path, self._master_key)
                self._decrypted_cache = self._parse_env_content(plaintext)
                logger.debug("🔓 .env.encrypted 解密成功, 加载 %d 个密钥", len(self._decrypted_cache))
            except FileNotFoundError:
                logger.debug("ℹ️  %s 不存在, 跳过加密文件", self._encrypted_path)
                self._decrypted_cache = {}
                return None
            except Exception as exc:
                logger.warning("⚠️  .env.encrypted 解密失败: %s (SECRET_MASTER_KEY 不正确?)", exc)
                self._decrypted_cache = {}
                return None

        return self._decrypted_cache.get(key)

    @staticmethod
    def _parse_env_content(content: str) -> dict[str, str]:
        """解析 .env 格式的内容为键值字典。"""
        result = {}
        for line in content.splitlines():
            line = line.strip()
            # 跳过注释和空行
            if not line or line.startswith("#"):
                continue
            # 只处理 KEY=VALUE 格式
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # 去除引号包裹
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            if key:
                result[key] = value
        return result

    @staticmethod
    def is_configured() -> bool:
        """快速检查是否至少有一个密钥源可用。"""
        return bool(os.environ.get(MASTER_KEY_ENV_VAR)) or Path(ENCRYPTED_ENV_FILE).exists()


# ═══════════════════════════════════════════════════════════════════════════
# 命令行入口 — 用于加密当前 .env
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """CLI: python key_manager.py [encrypt|decrypt|check]"""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if len(sys.argv) < 2:
        print("用法: python key_manager.py <encrypt|decrypt|check>")
        print("  环境变量 SECRET_MASTER_KEY 必须已设置")
        sys.exit(1)

    command = sys.argv[1]
    backend_dir = Path(__file__).parent.resolve()
    master_key = os.environ.get(MASTER_KEY_ENV_VAR)

    if command == "encrypt":
        if not master_key:
            print(f"❌ 请先设置环境变量 {MASTER_KEY_ENV_VAR}")
            print(f"   Windows (CMD):  set {MASTER_KEY_ENV_VAR}=your-strong-random-key")
            print(f"   Windows (PS):   $env:{MASTER_KEY_ENV_VAR}=\"your-strong-random-key\"")
            print(f"   Linux/Mac:      export {MASTER_KEY_ENV_VAR}=your-strong-random-key")
            sys.exit(1)

        env_path = backend_dir / ".env"
        if not env_path.exists():
            print(f"❌ .env 文件不存在: {env_path}")
            sys.exit(1)

        output = encrypt_env_file(env_path, master_key)
        print(f"✅ 加密完成 → {output}")
        print(f"⚠️  建议将原 .env 移出仓库或加入 .gitignore")

    elif command == "decrypt":
        if not master_key:
            print(f"❌ 请先设置环境变量 {MASTER_KEY_ENV_VAR}")
            sys.exit(1)

        encrypted_path = backend_dir / ENCRYPTED_ENV_FILE
        try:
            plaintext = decrypt_env_file(encrypted_path, master_key)
            # 只显示密钥名称, 不显示值!
            keys = SecretManager._parse_env_content(plaintext)
            print(f"✅ 解密成功! 共 {len(keys)} 个密钥:")
            for k in sorted(keys.keys()):
                val = keys[k]
                masked = val[:4] + "****" if len(val) > 8 else "****"
                print(f"   {k}={masked}")
        except Exception as exc:
            print(f"❌ 解密失败: {exc}")
            sys.exit(1)

    elif command == "check":
        encrypted_path = backend_dir / ENCRYPTED_ENV_FILE
        print(f"  SECRET_MASTER_KEY:     {'✅ 已设置' if master_key else '❌ 未设置'}")
        print(f"  .env.encrypted 文件:   {'✅ 存在' if encrypted_path.exists() else '❌ 不存在'}")
        if master_key and encrypted_path.exists():
            try:
                plaintext = decrypt_env_file(encrypted_path, master_key)
                keys = SecretManager._parse_env_content(plaintext)
                print(f"  可解密密钥数:         {len(keys)}")
                print(f"  状态:                 ✅ 正常")
            except Exception:
                print(f"  状态:                 ❌ 解密失败 (SECRET_MASTER_KEY 不匹配?)")
        else:
            print(f"  状态:                 ⚠️  不可用")

    else:
        print(f"未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()

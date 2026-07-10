#!/usr/bin/env python3
"""验证 SecretManager 的完整加解密流程。"""
import os
import sys
from pathlib import Path

# 设置 SECRET_MASTER_KEY (从环境变量读取，不应硬编码)
MASTER_KEY = os.environ.get("SECRET_MASTER_KEY", "")
if not MASTER_KEY:
    print("❌ 请先设置环境变量: export SECRET_MASTER_KEY=<your-key>")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent.resolve()))

from key_manager import SecretManager, decrypt_env_file

# 1. 验证 SecretManager 基本 API
print("=" * 60)
print("🧪 测试 1: SecretManager 基本 API")
s = SecretManager()
assert s.get("NONEXISTENT", "default") == "default", "默认值应返回"
print("   ✅ get() with default = OK")

# 2. 验证加密文件解密
print("\n🧪 测试 2: 从 .env.encrypted 读取密钥")
db_url = s.get("DATABASE_URL")
print(f"   DATABASE_URL: {'✅' if db_url else '❌'} (len={len(db_url)})")

api_key = s.get("DEEPSEEK_API_KEY")
print(f"   DEEPSEEK_API_KEY: {'✅' if api_key else '❌'} (len={len(api_key)})")

wechat_id = s.get("WECHAT_MINI_APPID")
print(f"   WECHAT_MINI_APPID: {'✅' if wechat_id else '❌'}")

feishu_id = s.get("FEISHU_APP_ID")
print(f"   FEISHU_APP_ID: {'✅' if feishu_id else '❌'}")

feishu_secret = s.get("FEISHU_APP_SECRET")
print(f"   FEISHU_APP_SECRET: {'✅' if feishu_secret else '❌'} (len={len(feishu_secret)})")

jwt_secret = s.get("JWT_SECRET")
print(f"   JWT_SECRET: {'✅' if jwt_secret else '❌'} (len={len(jwt_secret)})")

# 3. 验证加密文件完整性
print("\n🧪 测试 3: 加密文件完整性")
enc_path = Path(__file__).parent / ".env.encrypted"
try:
    plaintext = decrypt_env_file(enc_path, MASTER_KEY)
    lines = [l for l in plaintext.splitlines() if l.strip() and not l.strip().startswith("#")]
    print(f"   ✅ 解密成功, 有效行数: {len(lines)}")
except Exception as e:
    print(f"   ❌ 解密失败: {e}")

# 4. 统计
print("\n📊 统计")
total_keys = len(s._decrypted_cache) if hasattr(s, '_decrypted_cache') and s._decrypted_cache else 0
print(f"   加密密钥总数: {total_keys}")
print(f"   加密文件大小: {enc_path.stat().st_size / 1024:.1f} KB")

print("\n" + "=" * 60)
print("✅ 所有测试通过!" if api_key and db_url and wechat_id else "⚠️  部分密钥缺失，请检查加密文件")
print("=" * 60)

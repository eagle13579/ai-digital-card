#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BUG-034 存量数据迁移脚本 — users.phone 明文 → phone_hash / phone_enc / phone_last4 加密存储。

【背景】
    用户手机号此前以明文存储于 users.phone（String(20) UNIQUE NOT NULL）。
    本脚本读取存量明文手机号，复用业务侧 crypto_service（Fernet 密钥由 JWT_SECRET 派生），
    生成 SHA-256 哈希 + Fernet 密文 + 尾号4位，回填至新增三列。

【用法】（在 backend 目录下执行）
    python scripts/migrate_phone_encryption.py             # 执行迁移（幂等，可重复执行）
    python scripts/migrate_phone_encryption.py --dry-run   # 只预览将要迁移的行数，不写入
    python scripts/migrate_phone_encryption.py --verify    # 仅校验迁移结果，不写入

【兼容性】
    - 数据库：SQLite（开发）与 PostgreSQL（生产）均支持，连接复用 app.database 同步引擎，
      DATABASE_URL 从环境变量读取（默认 sqlite+aiosqlite:///./data/digital_brochure.db）。
    - 加密密钥：与业务代码完全一致（crypto_service 从 JWT_SECRET 派生 Fernet 密钥），
      迁移后 phone_enc 可被既有解密逻辑正常解密。

【安全边界（铁律）】
    - 只新增/回填三列，绝不删除、改写 users.phone 列，保证过渡期内登录
      （phone 唯一索引查询）与既有查询不受影响。
    - phone_hash 建立唯一索引（多行 NULL 不冲突），供第二阶段切换登录查询使用。
    - 第二阶段（本脚本范围外）：代码全量切换登录查询到 phone_hash 后，
      通过 Alembic 删除 phone 列，完成明文彻底清除。
"""

import argparse
import base64
import hashlib
import os
import sys
from typing import List, Tuple

# ── 路径引导：确保从 backend 根目录可导入 app 包 ─────────────────────────────
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from sqlalchemy import text  # noqa: E402
from sqlalchemy.engine import Connection  # noqa: E402

# 注意：不能 import app.services.crypto_service —— app.services.__init__ 会级联
# 导入 email_campaign → crm → routers 等重模块，且当前仓库存在与本次修复无关的
# 既有导入链问题（gaia_router 中 require_role 协程注册报错）。
# 因此此处内联实现与 crypto_service 完全一致的加密逻辑（密钥均由 JWT_SECRET 派生），
# 保证迁移后的 phone_enc 可被业务侧 decrypt_phone 正常解密。
from app.config import settings  # noqa: E402
from app.database import sync_engine  # noqa: E402


# ── 加密切片（与 app/services/crypto_service.py 逐行等价） ──────────────────

def _get_fernet():
    """获取 Fernet 实例：JWT_SECRET → SHA-256（32字节）→ url-safe base64。"""
    from cryptography.fernet import Fernet

    secret = settings.JWT_SECRET.encode("utf-8")
    key_bytes = hashlib.sha256(secret).digest()  # 32 bytes
    return Fernet(base64.urlsafe_b64encode(key_bytes))


def _encrypt_phone(phone: str) -> Tuple[str, str, str]:
    """加密手机号，返回 (密文, SHA-256 哈希, 尾号4位)。"""
    digits = "".join(c for c in (phone or "") if c.isdigit())
    encrypted = _get_fernet().encrypt(digits.encode("utf-8")).decode("utf-8")
    h = hashlib.sha256(digits.encode("utf-8")).hexdigest()
    last4 = digits[-4:] if len(digits) >= 4 else digits
    return encrypted, h, last4


def _decrypt_phone(encrypted: str) -> str:
    """解密手机号（Fernet 密文 → 数字串）。"""
    plain = _get_fernet().decrypt(encrypted.encode("utf-8"))
    return plain.decode("utf-8")

# 目标列定义（与 app/models/user.py 保持一致）
NEW_COLUMNS = [
    ("phone_hash", "VARCHAR(64)"),
    ("phone_enc", "TEXT"),
    ("phone_last4", "VARCHAR(4) NOT NULL DEFAULT ''"),
]
UNIQUE_INDEX_NAME = "uq_users_phone_hash"


# ── 数据库方言工具 ──────────────────────────────────────────────────────────

def _is_sqlite(conn: Connection) -> bool:
    return conn.dialect.name == "sqlite"


def get_existing_columns(conn: Connection) -> set:
    """返回 users 表现有列名集合（兼容 SQLite / PostgreSQL）。"""
    if _is_sqlite(conn):
        rows = conn.execute(text("PRAGMA table_info(users)")).fetchall()
        return {r[1] for r in rows}
    rows = conn.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'users'"
        )
    ).fetchall()
    return {r[0] for r in rows}


def ensure_columns(conn: Connection) -> List[str]:
    """为 users 表补充缺失的新列，返回实际新增的列名列表。"""
    existing = get_existing_columns(conn)
    added = []
    for col_name, col_ddl in NEW_COLUMNS:
        if col_name in existing:
            continue
        conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_ddl}"))
        added.append(col_name)
    if added:
        conn.commit()
    return added


def ensure_phone_hash_unique_index(conn: Connection) -> bool:
    """确保 phone_hash 上有唯一索引；已存在则跳过。返回是否新建。"""
    if _is_sqlite(conn):
        # SQLite: 检查唯一索引是否覆盖 phone_hash
        indexes = conn.execute(text("PRAGMA index_list(users)")).fetchall()
        for idx in indexes:
            # idx: (seq, name, unique, origin, partial)
            if not idx[2]:
                continue
            cols = conn.execute(
                text(f"PRAGMA index_info('{idx[1]}')")
            ).fetchall()
            if any(c[2] == "phone_hash" for c in cols):
                return False
    else:
        # PostgreSQL: 检查唯一约束 / 唯一索引是否覆盖 phone_hash
        cons = conn.execute(
            text(
                "SELECT tc.constraint_name FROM information_schema.table_constraints tc "
                "JOIN information_schema.constraint_column_usage ccu "
                "ON tc.constraint_name = ccu.constraint_name "
                "WHERE tc.table_name = 'users' AND tc.constraint_type = 'UNIQUE' "
                "AND ccu.column_name = 'phone_hash'"
            )
        ).fetchall()
        if cons:
            return False
        idxs = conn.execute(
            text(
                "SELECT indexname FROM pg_indexes WHERE tablename = 'users' "
                "AND indexdef LIKE '%phone_hash%' AND indexdef LIKE '%UNIQUE%'"
            )
        ).fetchall()
        if idxs:
            return False
    conn.execute(
        text(f"CREATE UNIQUE INDEX IF NOT EXISTS {UNIQUE_INDEX_NAME} ON users (phone_hash)")
    )
    conn.commit()
    return True


def _normalize_phone(raw: str) -> str:
    """只保留数字位。"""
    return "".join(c for c in (raw or "") if c.isdigit())


# ── 迁移主流程 ──────────────────────────────────────────────────────────────

def collect_pending(conn: Connection) -> List[Tuple[int, str]]:
    """找出待迁移行：(id, 明文手机号数字串)。已回填 phone_hash 的行跳过。"""
    rows = conn.execute(
        text(
            "SELECT id, phone FROM users "
            "WHERE phone IS NOT NULL AND trim(phone) <> ''"
        )
    ).fetchall()
    pending: List[Tuple[int, str]] = []
    for row in rows:
        digits = _normalize_phone(row[1])
        if not digits:
            continue
        has_hash = conn.execute(
            text("SELECT 1 FROM users WHERE id = :id AND phone_hash IS NOT NULL AND phone_hash <> ''"),
            {"id": row[0]},
        ).scalar()
        if has_hash:
            continue
        pending.append((row[0], digits))
    return pending


def run_migration(conn: Connection, dry_run: bool, batch_size: int) -> dict:
    """执行回填。返回统计信息。dry_run 模式完全只读。"""
    existing_cols = get_existing_columns(conn)
    added_cols: List[str] = []
    created_index = False

    if dry_run:
        # 只读预览：报告缺列与缺索引情况，不执行任何 DDL
        missing_cols = [c for c, _ in NEW_COLUMNS if c not in existing_cols]
        return {
            "added_columns": missing_cols,  # 预览：这些列将被新增
            "created_unique_index": None,
            "pending_rows": len(collect_pending(conn)),
            "migrated_rows": 0,
            "roundtrip_mismatch": 0,
            "duplicate_hash": 0,
            "missing_after": 0,
            "dry_run_note": f"DRY-RUN：以下列将被新增 {missing_cols}；未执行任何 DDL/DML",
        }

    added_cols = ensure_columns(conn)
    created_index = ensure_phone_hash_unique_index(conn)
    pending = collect_pending(conn)

    stats = {
        "added_columns": added_cols,
        "created_unique_index": created_index,
        "pending_rows": len(pending),
        "migrated_rows": 0,
        "roundtrip_mismatch": 0,
        "duplicate_hash": 0,
        "missing_after": 0,
    }

    if dry_run:
        return stats

    for i, (user_id, digits) in enumerate(pending, start=1):
        encrypted, h, last4 = _encrypt_phone(digits)
        conn.execute(
            text(
                "UPDATE users SET phone_hash = :h, phone_enc = :e, phone_last4 = :l4 "
                "WHERE id = :id"
            ),
            {"h": h, "e": encrypted, "l4": last4, "id": user_id},
        )
        if i % batch_size == 0:
            conn.commit()
    conn.commit()
    stats["migrated_rows"] = len(pending)

    # ── 迁移后自校验 ──
    stats["missing_after"] = conn.execute(
        text(
            "SELECT COUNT(*) FROM users "
            "WHERE phone IS NOT NULL AND trim(phone) <> '' "
            "AND (phone_hash IS NULL OR phone_hash = '' "
            "     OR phone_enc IS NULL OR phone_enc = '')"
        )
    ).scalar() or 0

    dup_rows = conn.execute(
        text(
            "SELECT phone_hash, COUNT(*) AS c FROM users "
            "WHERE phone_hash IS NOT NULL GROUP BY phone_hash HAVING COUNT(*) > 1"
        )
    ).fetchall()
    stats["duplicate_hash"] = len(dup_rows)

    # 密文 round-trip 校验：解密 phone_enc 必须等于明文数字串
    enc_rows = conn.execute(
        text(
            "SELECT phone, phone_enc FROM users "
            "WHERE phone_enc IS NOT NULL AND phone_enc <> ''"
        )
    ).fetchall()
    mismatch = 0
    for row in enc_rows:
        try:
            decrypted = _decrypt_phone(row[1])
        except Exception:
            mismatch += 1
            continue
        if decrypted != _normalize_phone(row[0]):
            mismatch += 1
    stats["roundtrip_mismatch"] = mismatch
    return stats


def run_verify(conn: Connection) -> dict:
    """只校验迁移结果，不写入。"""
    added_cols = get_existing_columns(conn)
    stats = {
        "columns_present": [c for c, _ in NEW_COLUMNS if c in added_cols],
        "columns_missing": [c for c, _ in NEW_COLUMNS if c not in added_cols],
        "total_users": conn.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0,
        "missing_enc": conn.execute(
            text(
                "SELECT COUNT(*) FROM users "
                "WHERE phone IS NOT NULL AND trim(phone) <> '' "
                "AND (phone_hash IS NULL OR phone_hash = '' "
                "     OR phone_enc IS NULL OR phone_enc = '')"
            )
        ).scalar() or 0,
        "missing_last4": conn.execute(
            text(
                "SELECT COUNT(*) FROM users "
                "WHERE phone IS NOT NULL AND trim(phone) <> '' "
                "AND (phone_last4 IS NULL OR phone_last4 = '')"
            )
        ).scalar() or 0,
        "duplicate_hash": 0,
        "roundtrip_mismatch": 0,
    }
    dup_rows = conn.execute(
        text(
            "SELECT phone_hash, COUNT(*) AS c FROM users "
            "WHERE phone_hash IS NOT NULL GROUP BY phone_hash HAVING COUNT(*) > 1"
        )
    ).fetchall()
    stats["duplicate_hash"] = len(dup_rows)

    enc_rows = conn.execute(
        text(
            "SELECT phone, phone_enc FROM users "
            "WHERE phone_enc IS NOT NULL AND phone_enc <> ''"
        )
    ).fetchall()
    mismatch = 0
    for row in enc_rows:
        try:
            decrypted = _decrypt_phone(row[1])
        except Exception:
            mismatch += 1
            continue
        if decrypted != _normalize_phone(row[0]):
            mismatch += 1
    stats["roundtrip_mismatch"] = mismatch

    # 明文残留扫描：找出已知手机号明文出现在其他业务表（除 users.phone 过渡列）
    residue = []
    try:
        crm_phones = conn.execute(
            text(
                "SELECT phone FROM crm_contacts "
                "WHERE phone IS NOT NULL AND trim(phone) <> ''"
            )
        ).fetchall()
        user_phones = {
            _normalize_phone(r[0])
            for r in conn.execute(text("SELECT phone FROM users")).fetchall()
        }
        hit = [p[0] for p in crm_phones if _normalize_phone(p[0]) in user_phones]
        if hit:
            residue.append(("crm_contacts.phone", len(hit)))
    except Exception:
        pass  # crm_contacts 表不存在时忽略
    stats["residue"] = residue
    return stats


# ── 验证 SQL 输出（供报告与人工复核） ───────────────────────────────────────

VERIFY_SQL = """\
-- ═══════════ BUG-034 迁移验证 SQL ═══════════
-- ① 完整性：有明文但缺加密字段的行数（应为 0）
SELECT COUNT(*) AS missing_enc
FROM users
WHERE phone IS NOT NULL AND trim(phone) <> ''
  AND (phone_hash IS NULL OR phone_hash = ''
       OR phone_enc IS NULL OR phone_enc = '');

-- ② 尾号回填：有明文但缺 phone_last4 的行数（应为 0）
SELECT COUNT(*) AS missing_last4
FROM users
WHERE phone IS NOT NULL AND trim(phone) <> ''
  AND (phone_last4 IS NULL OR phone_last4 = '');

-- ③ 哈希唯一性：重复 phone_hash（应为 0 行）
SELECT phone_hash, COUNT(*) AS c
FROM users
WHERE phone_hash IS NOT NULL
GROUP BY phone_hash
HAVING COUNT(*) > 1;

-- ④ 密文可解密且与明文一致（round-trip 由脚本执行，SQL 无法解密）
--    脚本内逐行 decrypt(phone_enc) == digits(phone)，不一致计数应 = 0

-- ⑤ 明文残留扫描（过渡期预期仅 users.phone 命中，属计划内保留列）
--    已知遗留：crm_contacts.phone 明文（后续 BUG 跟踪，不在本 BUG 范围）
SELECT phone FROM crm_contacts
WHERE phone IS NOT NULL AND trim(phone) <> '';

-- ⑥ 新列元数据确认
PRAGMA table_info(users);          -- SQLite
-- SELECT column_name FROM information_schema.columns WHERE table_name='users';  -- PostgreSQL
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="BUG-034 用户手机号存量加密迁移")
    parser.add_argument("--dry-run", action="store_true", help="只预览待迁移行数，不写入")
    parser.add_argument("--verify", action="store_true", help="仅校验迁移结果，不写入")
    parser.add_argument("--batch-size", type=int, default=200, help="批量提交行数（默认 200）")
    args = parser.parse_args()

    print("=" * 72)
    print("BUG-034 用户手机号存量加密迁移")
    print(f"数据库: {sync_engine.url}")
    print(f"模式: {'DRY-RUN（预览）' if args.dry_run else 'VERIFY（仅校验）' if args.verify else 'MIGRATE（执行迁移）'}")
    print("=" * 72)

    with sync_engine.connect() as conn:
        if args.verify:
            stats = run_verify(conn)
        else:
            stats = run_migration(conn, dry_run=args.dry_run, batch_size=args.batch_size)

    print("\n── 迁移结果 ──")
    if "dry_run_note" in stats:
        print(f"新增列（预览）: {stats['added_columns'] or '无（已存在）'}")
        print(f"待迁移行数: {stats['pending_rows']}")
        print(stats["dry_run_note"])
    elif "added_columns" in stats:
        print(f"新增列: {stats['added_columns'] or '无（已存在）'}")
        print(f"phone_hash 唯一索引: {'已新建' if stats['created_unique_index'] else '已存在'}")
        print(f"待迁移行数: {stats['pending_rows']}")
        print(f"已迁移行数: {stats['migrated_rows']}")
        print(f"迁移后缺失加密字段行数: {stats['missing_after']}（应为 0）")
        print(f"重复 phone_hash 组数: {stats['duplicate_hash']}（应为 0）")
        print(f"密文 round-trip 不一致: {stats['roundtrip_mismatch']}（应为 0）")
    else:
        print(f"总用户数: {stats['total_users']}")
        print(f"新列存在: {stats['columns_present']}")
        print(f"新列缺失: {stats['columns_missing'] or '无'}")
        print(f"缺失加密字段行数: {stats['missing_enc']}（应为 0）")
        print(f"缺失尾号行数: {stats['missing_last4']}（应为 0）")
        print(f"重复 phone_hash 组数: {stats['duplicate_hash']}（应为 0）")
        print(f"密文 round-trip 不一致: {stats['roundtrip_mismatch']}（应为 0）")
        if stats["residue"]:
            print(f"明文残留（已知遗留）: {stats['residue']}")
        else:
            print("明文残留扫描: 未发现（除 users.phone 过渡列外）")

    print("\n── 验证 SQL（可复制到数据库客户端复核） ──")
    print(VERIFY_SQL)
    return 0


if __name__ == "__main__":
    sys.exit(main())

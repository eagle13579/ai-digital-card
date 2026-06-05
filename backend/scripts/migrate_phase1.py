"""
Phase 1 数据库迁移脚本

为已存在的数据库添加：
1. users 表新增会员相关字段
2. 创建 unlock_records 表

用法：python scripts/migrate_phase1.py
"""

import os
import sys

# 将项目根目录加入 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String, DateTime,
    inspect, text,
)
from app.config import settings


def migrate():
    engine = create_engine(settings.DATABASE_URL, echo=True)
    inspector = inspect(engine)
    metadata = MetaData()

    # 检查 users 表是否存在
    if "users" in inspector.get_table_names():
        existing_columns = {c["name"] for c in inspector.get_columns("users")}
        print(f"[迁移] users 表现有字段: {existing_columns}")

        with engine.connect() as conn:
            # 新增会员字段
            new_columns = {
                "membership_tier": "VARCHAR(16) NOT NULL DEFAULT 'free'",
                "membership_expires_at": "DATETIME",
                "membership_synced_at": "DATETIME",
                "unlock_quota": "INTEGER NOT NULL DEFAULT 0",
                "quota_reset_at": "DATETIME",
            }
            for col_name, col_type in new_columns.items():
                if col_name not in existing_columns:
                    print(f"[迁移] 添加 users.{col_name} ({col_type})")
                    conn.execute(text(
                        f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"
                    ))
            conn.commit()
            print("[迁移] users 表迁移完成 ✅")
    else:
        print("[迁移] users 表不存在，跳过")

    # 创建 unlock_records 表
    if "unlock_records" not in inspector.get_table_names():
        print("[迁移] 创建 unlock_records 表...")
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE unlock_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    target_user_id INTEGER NOT NULL,
                    match_record_id INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
        print("[迁移] unlock_records 表创建完成 ✅")
    else:
        print("[迁移] unlock_records 表已存在，跳过")

    print("=" * 50)
    print("Phase 1 数据库迁移完成！")
    print("=" * 50)


if __name__ == "__main__":
    migrate()

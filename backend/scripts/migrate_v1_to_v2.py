#!/usr/bin/env python3
"""
数据迁移脚本：将旧 digital_brochure.db（单体SQLite）的数据迁移到新ORM结构

用法：
    python scripts/migrate_v1_to_v2.py

旧数据库文件路径：backend/old_data/digital_brochure.db
新数据库文件路径：backend/data/digital_brochure.db

迁移内容：
  - brochures 表 → Brochure + Page 模型
  - users 表 → User 模型
  - trust_network 表 → TrustNetwork 模型
  - match_records 表 → MatchRecord 模型
  - visitor_logs 表 → VisitorLog 模型
"""

import json
import os
import sqlite3
import sys

# 确保项目根目录在路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.brochure import Brochure, Page
from app.models.tag import UserTag, MatchRecord
from app.models.visitor import VisitorLog
from app.models.trust import TrustNetwork

# ── 配置 ───────────────────────────────────────────
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD_DB_PATH = os.path.join(BACKEND_DIR, "old_data", "digital_brochure.db")
NEW_DB_PATH = os.path.join(BACKEND_DIR, "data", "digital_brochure.db")

# 如果旧库在本目录，也尝试查找
FALLBACK_PATHS = [
    os.path.join(BACKEND_DIR, "..", "digital_brochure.db"),
    os.path.join(BACKEND_DIR, "..", "..", "digital_brochure.db"),
]


def find_old_db() -> str | None:
    """查找旧的 digital_brochure.db"""
    if os.path.exists(OLD_DB_PATH):
        return OLD_DB_PATH
    for p in FALLBACK_PATHS:
        resolved = os.path.abspath(p)
        if os.path.exists(resolved):
            return resolved
    return None


def get_old_conn(db_path: str) -> sqlite3.Connection:
    """连接旧数据库"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def migrate_users(old_conn, new_session):
    """迁移用户数据"""
    try:
        rows = old_conn.execute("SELECT * FROM users").fetchall()
    except sqlite3.OperationalError:
        print("  ⚠️ users 表不存在，跳过")
        return

    count = 0
    for row in rows:
        try:
            data = json.loads(row["data"]) if isinstance(row["data"], str) else {}
        except (json.JSONDecodeError, TypeError):
            data = {}

        user = User(
            username=data.get("username", ""),
            phone=data.get("phone", f"138{row['user_id'][-8:] if len(row['user_id']) >= 8 else '00000001'}"),
            password_hash=data.get("password_hash", data.get("password", "default_password")),
            wechat_openid=data.get("wechat_openid"),
            name=data.get("name", data.get("nickname", f"用户_{row['user_id'][-6:]}")),
            company=data.get("company", ""),
            title=data.get("position", data.get("title", "")),
            intro=data.get("bio", data.get("intro", "")),
            avatar=data.get("avatar", ""),
        )
        new_session.add(user)
        count += 1

    new_session.commit()
    print(f"  ✅ 迁移 {count} 条用户")


def migrate_brochures(old_conn, new_session):
    """迁移画册数据 → Brochure + Page"""
    try:
        rows = old_conn.execute("SELECT * FROM brochures").fetchall()
    except sqlite3.OperationalError:
        print("  ⚠️ brochures 表不存在，跳过")
        return

    count = 0
    for row in rows:
        try:
            data = json.loads(row["data"]) if isinstance(row["data"], str) else {}
        except (json.JSONDecodeError, TypeError):
            data = {}

        # 查找 user_id 对应的用户
        user = new_session.query(User).filter(User.phone == data.get("phone")).first()
        if user is None:
            # 尝试创建默认用户
            user = User(
                phone=f"138{row['user_id'][-8:] if len(row['user_id']) >= 8 else '00000001'}",
                password_hash="migrated",
                name=data.get("name", "已迁移用户"),
                company=data.get("company", ""),
                title=data.get("position", ""),
                intro=data.get("bio", ""),
                avatar=data.get("avatar", ""),
            )
            new_session.add(user)
            new_session.flush()

        tags = data.get("tags", [])
        trust_list = data.get("trust_network", [])

        # 创建 Brochure
        brochure = Brochure(
            user_id=user.id,
            title=data.get("title", f"{data.get('name', '未知')}的名片"),
            cover=data.get("cover", data.get("avatar", "")),
            pages_count=1,
            status="published",
            view_count=0,
        )
        new_session.add(brochure)
        new_session.flush()

        # 创建 Page（主要信息作为第一页）
        bio_text = data.get("bio", "")
        content_parts = []
        if data.get("company"):
            content_parts.append(f"公司：{data['company']}")
        if data.get("position"):
            content_parts.append(f"职位：{data['position']}")
        if data.get("phone"):
            content_parts.append(f"电话：{data['phone']}")
        if data.get("email"):
            content_parts.append(f"邮箱：{data['email']}")
        if data.get("wechat"):
            content_parts.append(f"微信：{data['wechat']}")
        if bio_text:
            content_parts.append(f"\n简介：{bio_text}")

        page = Page(
            brochure_id=brochure.id,
            sort_order=0,
            content_type="cover",
            content="\n".join(content_parts),
            image_url=data.get("avatar", ""),
            ai_summary=bio_text[:100] if bio_text else "",
        )
        new_session.add(page)

        # 迁移标签
        for tag_data in tags:
            tag = UserTag(
                user_id=user.id,
                tag_type=tag_data.get("tag_type", "provide"),
                tag=tag_data.get("tag", ""),
                weight=tag_data.get("weight", 1.0),
                source=tag_data.get("source", "import"),
            )
            new_session.add(tag)

        # 迁移信任网络（先创建信任记录，等迁移完所有用户后再关联）
        for trusted_id in trust_list:
            trusted_user = new_session.query(User).filter(User.phone.like(f"%{trusted_id[-4:]}%")).first()
            if trusted_user:
                trust = TrustNetwork(
                    user_id=user.id,
                    trusted_user_id=trusted_user.id,
                )
                new_session.add(trust)

        count += 1

    new_session.commit()
    print(f"  ✅ 迁移 {count} 条画册")


def migrate_match_records(old_conn, new_session):
    """迁移匹配记录"""
    try:
        rows = old_conn.execute("SELECT * FROM match_records").fetchall()
    except sqlite3.OperationalError:
        print("  ⚠️ match_records 表不存在，跳过")
        return

    count = 0
    for row in rows:
        try:
            common_tags = json.loads(row["common_tags"]) if isinstance(row["common_tags"], str) else []
        except (json.JSONDecodeError, TypeError):
            common_tags = []

        # 查找用户（通过旧ID中存储的phone或name信息）
        user_a = new_session.query(User).filter(User.phone.like(f"%{row['user_a'][-4:]}%")).first()
        user_b = new_session.query(User).filter(User.phone.like(f"%{row['user_b'][-4:]}%")).first()

        if user_a and user_b:
            record = MatchRecord(
                user_a_id=user_a.id,
                user_b_id=user_b.id,
                match_score=row["score"],
                status=row.get("status", "matched"),
                common_tags=json.dumps(common_tags, ensure_ascii=False),
                source="auto",
            )
            new_session.add(record)
            count += 1

    new_session.commit()
    print(f"  ✅ 迁移 {count} 条匹配记录")


def migrate_visitor_logs(old_conn, new_session):
    """迁移访客日志"""
    try:
        rows = old_conn.execute("SELECT * FROM visitor_logs").fetchall()
    except sqlite3.OperationalError:
        print("  ⚠️ visitor_logs 表不存在，跳过")
        return

    count = 0
    for row in rows:
        # 查找 brochure（通过旧ID）
        brochure = new_session.query(Brochure).filter(
            Brochure.title.like(f"%{row['brochure_id'][-6:]}%")
        ).first()

        if brochure:
            log = VisitorLog(
                brochure_id=brochure.id,
                visitor_id=row.get("visitor_name", ""),
                visitor_ip=row.get("visitor_ip", ""),
                visitor_name=row.get("visitor_name", ""),
                source=row.get("source", "direct"),
            )
            new_session.add(log)
            count += 1

    new_session.commit()
    print(f"  ✅ 迁移 {count} 条访客日志")


def main():
    print("=" * 60)
    print("  AI数字名片 数据迁移 v1 → v2")
    print("=" * 60)

    # 1. 查找旧库
    old_db = find_old_db()
    if not old_db:
        print("\n❌ 未找到旧数据库文件 digital_brochure.db")
        print("   请将其放在以下路径之一：")
        print(f"   - {OLD_DB_PATH}")
        for p in FALLBACK_PATHS:
            print(f"   - {os.path.abspath(p)}")
        return

    print(f"\n📂 旧数据库: {old_db}")
    print(f"📂 新数据库: {NEW_DB_PATH}")

    # 2. 连接新旧库
    old_conn = get_old_conn(old_db)

    # 确保新库目录存在
    os.makedirs(os.path.dirname(NEW_DB_PATH), exist_ok=True)

    # 3. 创建新表
    Base.metadata.create_all(bind=engine)
    print("\n✅ 新数据库表已创建")

    # 4. 执行迁移
    new_session = SessionLocal()
    try:
        print("\n📦 迁移用户...")
        migrate_users(old_conn, new_session)

        print("\n📦 迁移画册...")
        migrate_brochures(old_conn, new_session)

        print("\n📦 迁移匹配记录...")
        migrate_match_records(old_conn, new_session)

        print("\n📦 迁移访客日志...")
        migrate_visitor_logs(old_conn, new_session)

        print("\n" + "=" * 60)
        print("  🎉 数据迁移完成！")
        print("=" * 60)
        print(f"\n新数据库位置: {NEW_DB_PATH}")
        print("你可以通过 `python main.py` 启动新服务")

    except Exception as e:
        new_session.rollback()
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        old_conn.close()
        new_session.close()


if __name__ == "__main__":
    main()

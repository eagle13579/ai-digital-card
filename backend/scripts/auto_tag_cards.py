#!/usr/bin/env python3
"""
自动为AI数智名片补充行业标签和供需数据
========================================
基于公司名和职位自动推断行业标签和供需标签，为现有名片补充数据。

规则:
  - AI/科技类 → tags: AI/大数据/软件, provide: AI技术, need: 企业客户/市场渠道
  - 能源类 → tags: 新能源/储能, provide: 能源产品, need: 采购/合作
  - 物流/供应链 → tags: 物流/供应链, provide: 物流服务, need: 企业客户/技术
  - 制造/精密 → tags: 智能制造/精密制造, provide: 智能设备, need: 投资/客户
  - 设计/创意 → tags: 品牌设计/创意, provide: 设计服务, need: 企业客户
  - 投资/金融 → tags: 投资/金融, provide: 投资资金, need: 优质项目
  - 电商/跨境 → tags: 电商/跨境电商, provide: 电商渠道, need: 优质产品
  - 传媒/营销 → tags: 传媒/营销, provide: 媒体资源, need: 品牌合作
  - 法律 → tags: 法律/合规服务, provide: 法律服务, need: 企业客户
  - 财税 → tags: 财税/审计服务, provide: 财税服务, need: 企业客户
  - 咨询 → tags: 管理咨询/战略, provide: 咨询服务, need: 企业客户
  - 自由职业/开发 → tags: 软件开发/IT服务, provide: 技术开发, need: 项目合作
  - 纺织 → tags: 纺织制造, provide: 纺织产品, need: 采购渠道

可重复运行（幂等）— 不会破坏已有数据，不会重复插入已有标签。
"""

import sqlite3
import os
import shutil
from datetime import datetime

# ── 路径 ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "digital_brochure.db")
BACKUP_PATH = DB_PATH + ".bak"

# ── 行业规则 ──────────────────────────────────────────────────────────
# 每条规则: (关键字列表, 行业标签, 补充provide标签列表, 补充need标签列表)
# 注意: 只补充"尚不存在"的标签，不会覆盖已有的
# 规则按 specificity 从高到低排列，更具体的放在前面
INDUSTRY_RULES = [
    # ── 纺织（最具体，优先匹配公司名关键词） ──
    (
        ["大成纺织", "纺织"],
        "纺织制造",
        ["纺织产品", "生产制造", "供应链资源"],
        ["采购渠道", "品牌合作", "技术升级"],
    ),
    # ── 法律/合规 ──
    (
        ["明达律师", "律师事务所", "合伙人律师"],
        "法律/合规服务",
        ["法律服务", "合规咨询", "股权设计"],
        ["企业客户", "科技公司", "创业团队"],
    ),
    # ── 财税/审计 ──
    (
        ["锐创会计", "会计师事务所", "资深审计师", "CPA"],
        "财税/审计服务",
        ["财税服务", "审计服务", "税务筹划"],
        ["企业客户", "高新企业", "创业团队"],
    ),
    # ── 管理咨询 ──
    (
        ["瑞麟管理", "管理咨询", "首席顾问", "麦肯锡"],
        "管理咨询/战略",
        ["咨询服务", "战略规划", "企业转型"],
        ["企业客户", "出海企业", "战略合作"],
    ),
    # ── 投资/金融（优先于 AI 规则，因为红杉/鼎晖有 AI 相关描述） ──
    (
        ["鼎晖资本", "红杉中国", "投资总监", "投资经理", "投资基金"],
        "投资/金融",
        ["投资资金", "资本运作", "投融资服务"],
        ["优质项目", "创业团队", "行业人脉"],
    ),
    # ── 电商/跨境电商 ──
    (
        ["世纪互联电商", "互联电商", "跨境电商", "电商采购"],
        "电商/跨境电商",
        ["电商渠道", "电商运营", "海外渠道"],
        ["优质产品", "品牌合作", "供应链资源"],
    ),
    # ── 传媒/营销 ──
    (
        ["星辉传媒", "传媒集团", "商务总监", "传媒"],
        "传媒/营销",
        ["媒体资源", "品牌营销", "内容创作"],
        ["品牌合作", "跨界联名", "企业客户"],
    ),
    # ── 物流/供应链 ──
    (
        ["华联供应链", "供应链管理", "采购总监", "物流"],
        "物流/供应链",
        ["物流服务", "供应链管理", "仓储配送"],
        ["企业客户", "技术升级", "合作伙伴"],
    ),
    # ── 精密制造/智能制造 ──
    (
        ["精诚精密", "精密制造", "精密零部件", "董事长"],
        "智能制造/精密制造",
        ["智能设备", "精密制造", "生产加工"],
        ["投资合作", "企业客户", "技术升级"],
    ),
    # ── 新能源/储能 ──
    (
        ["绿能新能源", "储能技术", "新能源"],
        "新能源/储能",
        ["能源产品", "储能技术", "新能源方案"],
        ["投资合作", "企业客户", "技术合作"],
    ),
    # ── 设计/创意 ──
    (
        ["思创设计", "设计事务所", "首席设计师", "红点奖"],
        "品牌设计/创意",
        ["设计服务", "品牌设计", "视觉创意"],
        ["企业客户", "品牌合作", "市场推广"],
    ),
    # ── 自由职业/开发 ──
    (
        ["自由职业", "全栈开发", "自由开发者"],
        "软件开发/IT服务",
        ["技术开发", "软件开发", "系统架构"],
        ["项目合作", "创业团队", "远程工作"],
    ),
    # ── AI/科技/软件（放在最后作为通用 fallback，避免误匹配） ──
    (
        ["明远科技", "雅信电子", "电子科技", "CEO/创始人", "CTO", "销售总监",
         "大数据", "人工智能", "AI技术"],
        "AI/大数据/软件",
        ["AI技术", "大数据", "软件开发"],
        ["企业客户", "市场渠道", "技术合作"],
    ),
]


def backup_database():
    """备份数据库（如已有备份则跳过）"""
    if os.path.exists(BACKUP_PATH):
        # 如果已有备份，用时间戳创建差异备份
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        alt_backup = f"{BACKUP_PATH}.{ts}"
        shutil.copy2(DB_PATH, alt_backup)
        print(f"📦 差异备份: {alt_backup}")
    else:
        shutil.copy2(DB_PATH, BACKUP_PATH)
        print(f"📦 首次备份: {BACKUP_PATH}")
    return BACKUP_PATH


def get_existing_tags(cursor):
    """获取所有已有标签集合（用于幂等判断）"""
    cursor.execute("SELECT user_id, tag_type, tag FROM user_tags")
    existing = set()
    for row in cursor.fetchall():
        existing.add((row[0], row[1], row[2]))
    return existing


def get_all_users(cursor):
    """获取所有有公司/职位信息的用户"""
    cursor.execute(
        "SELECT id, name, company, title, intro FROM users ORDER BY id"
    )
    return cursor.fetchall()


def match_industry(name, company, title, intro):
    """
    根据公司名、职位、简介匹配行业规则。
    匹配优先级: 公司名 > 职位 > 简介
    规则按 specificity 从高到低排列。
    返回匹配到的第一个规则索引，或 None。
    """
    fields = [company, title, intro]

    for idx, (keywords, _, _, _) in enumerate(INDUSTRY_RULES):
        for kw in keywords:
            kw_lower = kw.lower()
            for field in fields:
                if kw_lower in field.lower():
                    return idx

    return None


def is_test_user(name, company):
    """判断是否为测试用户"""
    return not company.strip() or name in ("Final", "Done", "FixTester")


def auto_tag():
    """主流程：自动补充标签"""
    print("=" * 60)
    print("  AI数智名片 — 自动标签补充工具")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. 备份
    backup_database()

    # 2. 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 3. 获取已有数据
    existing_tags = get_existing_tags(cur)
    users = get_all_users(cur)

    print(f"\n📋 用户总数: {len(users)}")
    print(f"🏷️  已有标签数: {len(existing_tags)}")

    # 4. 逐用户处理
    stats = {"matched": 0, "skipped_test": 0, "skipped_nomatch": 0, "added": 0}
    added_records = []

    for user in users:
        uid, name, company, title, intro = user

        # 跳过测试用户
        if is_test_user(name, company):
            stats["skipped_test"] += 1
            continue

        # 匹配行业规则
        rule_idx = match_industry(name, company, title, intro)
        if rule_idx is None:
            stats["skipped_nomatch"] += 1
            print(f"  ⚠️  [{uid:2d}] {name:8s} ({company}) — 未匹配到规则，跳过")
            continue

        keywords, industry_tag, supply_tags, need_tags = INDUSTRY_RULES[rule_idx]
        user_added = 0

        # 添加行业标签（作为 provide 类型，表示该用户所属行业领域）
        tag_key = (uid, "provide", industry_tag)
        if tag_key not in existing_tags:
            cur.execute(
                "INSERT INTO user_tags (user_id, tag_type, tag, weight, source) VALUES (?, ?, ?, ?, ?)",
                (uid, "provide", industry_tag, 0.85, "ai"),
            )
            existing_tags.add(tag_key)
            user_added += 1
            added_records.append((uid, "provide", industry_tag, 0.85, "ai"))
            print(f"  ✅ [{uid:2d}] {name:8s} → 行业标签(provide): {industry_tag}")

        # 补充 supply 标签（如果尚不存在）
        for tag in supply_tags:
            tag_key = (uid, "provide", tag)
            if tag_key not in existing_tags:
                cur.execute(
                    "INSERT INTO user_tags (user_id, tag_type, tag, weight, source) VALUES (?, ?, ?, ?, ?)",
                    (uid, "provide", tag, 0.75, "ai"),
                )
                existing_tags.add(tag_key)
                user_added += 1
                added_records.append((uid, "provide", tag, 0.75, "ai"))
                print(f"  ➕ [{uid:2d}] {name:8s} → supply标签: {tag}")

        # 补充 need 标签（如果尚不存在）
        for tag in need_tags:
            tag_key = (uid, "need", tag)
            if tag_key not in existing_tags:
                cur.execute(
                    "INSERT INTO user_tags (user_id, tag_type, tag, weight, source) VALUES (?, ?, ?, ?, ?)",
                    (uid, "need", tag, 0.75, "ai"),
                )
                existing_tags.add(tag_key)
                user_added += 1
                added_records.append((uid, "need", tag, 0.75, "ai"))
                print(f"  ➕ [{uid:2d}] {name:8s} → need标签: {tag}")

        if user_added > 0:
            stats["added"] += user_added
            stats["matched"] += 1
        else:
            print(f"  🔄 [{uid:2d}] {name:8s} — 标签已完备，无新增")
            stats["matched"] += 1

    # 5. 提交
    conn.commit()
    conn.close()

    # 6. 统计输出
    print("\n" + "=" * 60)
    print(f"  📊 处理统计:")
    print(f"     - 匹配成功: {stats['matched']} 位用户")
    print(f"     - 跳过测试用户: {stats['skipped_test']} 位")
    print(f"     - 未匹配到规则: {stats['skipped_nomatch']} 位")
    print(f"     - 新增标签: {stats['added']} 条")
    if added_records:
        print(f"\n  📝 新增标签明细:")
        for r in added_records:
            print(f"     user_id={r[0]:2d} | {r[1]:8s} | {r[2]:20s} | weight={r[3]:.2f} | source={r[4]}")
    print("=" * 60)
    return stats


if __name__ == "__main__":
    auto_tag()

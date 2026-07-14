"""生产部署清理脚本 — 删除垃圾匹配记录 + 运行增强"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'digital_brochure.db')

def main():
    if not os.path.exists(DB_PATH):
        print(f"数据库不存在: {DB_PATH}")
        return

    db = sqlite3.connect(DB_PATH)
    
    # 统计
    total = db.execute("SELECT COUNT(*) FROM match_records").fetchone()[0]
    garbage = db.execute(
        "SELECT COUNT(*) FROM match_records WHERE source='v2_auto_enhance' AND (common_tags='[]' OR common_tags='')"
    ).fetchone()[0]
    print(f"匹配记录总数: {total}")
    print(f"空标签垃圾: {garbage}")
    
    # 删除
    cursor = db.execute(
        "DELETE FROM match_records WHERE source='v2_auto_enhance' AND (common_tags='[]' OR common_tags='')"
    )
    db.commit()
    print(f"已删除 {cursor.rowcount} 条垃圾记录")
    
    remaining = db.execute("SELECT COUNT(*) FROM match_records").fetchone()[0]
    print(f"剩余匹配记录: {remaining}")
    
    # 按来源统计
    rows = db.execute("SELECT source, status, COUNT(*) FROM match_records GROUP BY source, status").fetchall()
    for r in rows:
        print(f"  [{r[0]}] {r[1]}: {r[2]}")
    
    db.close()
    print("\n清理完成。现在运行增强脚本...")

if __name__ == "__main__":
    main()

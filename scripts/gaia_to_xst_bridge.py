"""
芯森态 ← 盖娅大脑 逆向桥接脚本
将盖娅大脑的 AI 洞察/策略写入芯森态数据库
可被 cron 每6h触发
"""
import json, logging, os, sqlite3
from datetime import datetime

PALACE_ROOT = r"D:\向海容的知识库\wiki\wiki\记忆宫殿"
GAIA_DB = os.path.join(PALACE_ROOT, "brain_daemon", "knowledge_models.db")
XINSENTAI_DB = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                             "api", "data", "xinsentai.db")
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), os.pardir, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("gaia_to_xst")
if not logger.handlers:
    fh = logging.FileHandler(os.path.join(LOG_DIR, "gaia_to_xst.log"), encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(fh)
    logger.addHandler(logging.StreamHandler())

def bridge():
    """从盖娅大脑读取AI洞察，写入芯森态"""
    results = {"read": 0, "written": 0, "insights": []}
    
    if not os.path.exists(GAIA_DB):
        logger.warning("盖娅大脑数据库不存在，跳过")
        return results
    
    # Read recent insights from gaia
    gc = sqlite3.connect(GAIA_DB)
    try:
        rows = gc.execute("""
            SELECT title, content, category, source, created_at
            FROM knowledge_models
            WHERE category LIKE '%xinsentai%' OR category LIKE '%招商%' OR category LIKE '%recommend%'
            ORDER BY created_at DESC LIMIT 20
        """).fetchall()
        results["read"] = len(rows)
        
        if rows:
            xc = sqlite3.connect(XINSENTAI_DB)
            try:
                xc.execute("""
                    CREATE TABLE IF NOT EXISTS gaia_insights (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        content TEXT,
                        category TEXT,
                        source TEXT,
                        applied INTEGER DEFAULT 0,
                        created_at TEXT,
                        bridged_at TEXT DEFAULT (datetime('now'))
                    )
                """)
                for r in rows:
                    xc.execute(
                        "INSERT OR IGNORE INTO gaia_insights (title, content, category, source, created_at) VALUES (?,?,?,?,?)",
                        (r[0], r[1], r[2], r[3], r[4])
                    )
                    results["written"] += 1
                    results["insights"].append(r[0])
                xc.commit()
            finally:
                xc.close()
    finally:
        gc.close()
    
    logger.info(f"盖娅→芯森态桥接: 读取{results['read']}条, 写入{results['written']}条")
    return results

if __name__ == "__main__":
    r = bridge()
    print(json.dumps(r, ensure_ascii=False, indent=2))

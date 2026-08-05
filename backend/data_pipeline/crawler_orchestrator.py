"""
统一爬虫调度器 — 管理所有数据源采集任务
P1升级：接入真实引擎（cloak_scraper, crawler, feedback_loop）
"""
import os
import sys
import json
import time
import datetime
import logging
import subprocess
from typing import Dict, List, Optional

# 路径修复
BACKEND_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BACKEND_DIR)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("CrawlerOrchestrator")

REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "data_source_registry.json")
STATE_PATH = os.path.join(os.path.dirname(__file__), ".crawler_state.json")
RAW_DATA_DIR = os.path.join(BACKEND_DIR, "data", "raw")


class CrawlerOrchestrator:
    """
    爬虫调度器 — 按数据源注册表调度所有采集任务
    Phase 1: 接入真实引擎（httpx/requests爬取）
    Phase 2: 全数据源覆盖
    """

    def __init__(self):
        self._registry = self._load_registry()
        self._state: Dict[str, dict] = self._load_state()
        self._results: List[dict] = []
        os.makedirs(RAW_DATA_DIR, exist_ok=True)

    def _load_registry(self) -> dict:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_state(self) -> dict:
        if os.path.exists(STATE_PATH):
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"last_collected": {}, "total_items": 0, "last_run": ""}

    def _save_state(self):
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(self._state, f, ensure_ascii=False, indent=2)

    def should_collect(self, source_id: str) -> bool:
        sources = self._registry.get("sources", {})
        source = sources.get(source_id)
        if not source or not source.get("enabled", False):
            return False
        freq_min = source.get("frequency_min", 60)
        last = self._state["last_collected"].get(source_id, 0)
        now = time.time()
        return (now - last) >= freq_min * 60

    def collect_all_due(self) -> List[dict]:
        """采集所有到期的数据源 → 写文件到 data/raw/ """
        results = []
        sources = self._registry.get("sources", {})

        for source_id, source in sources.items():
            if not source.get("enabled", False):
                continue
            if not self.should_collect(source_id):
                logger.info(f"⏭️ {source_id} 未到期，跳过")
                continue

            logger.info(f"🔄 开始采集: {source_id} ({source.get('name', '')})")
            try:
                result = self._collect_single(source_id, source)
                results.append(result)
                self._state["last_collected"][source_id] = time.time()
                self._state["total_items"] += result.get("items_count", 0)
                logger.info(f"✅ {source_id} 采集完成: {result.get('items_count', 0)} 条 → {result.get('output_file', 'N/A')}")
            except Exception as e:
                logger.error(f"❌ {source_id} 采集失败: {e}")
                results.append({
                    "source_id": source_id,
                    "status": "error",
                    "error": str(e),
                    "items_count": 0,
                    "timestamp": datetime.datetime.utcnow().isoformat()
                })

        self._state["last_run"] = datetime.datetime.utcnow().isoformat()
        self._save_state()
        self._results = results
        return results

    def _collect_single(self, source_id: str, source: dict) -> dict:
        """采集单个数据源 — 调真实引擎"""
        engine_key = source.get("engine", "")

        # 引擎名→方法名映射
        engine_method_map = {
            "cloak_scraper": "cloak_scraper",
            "crawler": "crawler",
            "xiaohongshu-openclaw": "xiaohongshu",
            "qichacha_client": "qichacha_client",
            "web_search": "web_search",
            "feedback_loop": "feedback_loop",
            "crm_pipeline": "crm_data",
            "knowledge_service": "knowledge_base",
            "knowledge_model_service": "knowledge_base",
            "rag_pipeline": "web_content",
            "user_behavior": "user_behavior",
        }

        method_name = engine_method_map.get(engine_key, "fallback")
        method = getattr(self, f"_engine_{method_name}", self._engine_fallback)

        if method:
            items, output_file = method(source_id, source)
        else:
            items, output_file = self._engine_fallback(source_id, source)

        return {
            "source_id": source_id,
            "status": "success" if items >= 0 else "error",
            "items_count": max(0, items),
            "output_file": output_file or "",
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

    # ─── 引擎实现 ───────────────────────────────────────────────

    def _engine_cloak_scraper(self, source_id: str, source: dict) -> tuple:
        """引擎: CloakBrowser智能爬虫 — 从真实URL抓取企业信息"""
        logger.info(f"  [cloak_scraper] 调用企业网站采集...")
        # 导入真实cloak_scraper模块（同步模式）
        try:
            from app.services.cloak_scraper import SmartScraperService
            import asyncio

            service = SmartScraperService()
            # 用示例URL列表（真实场景可由外部配置提供）
            sample_urls = [
                "https://www.qichacha.com",
                "https://www.tianyancha.com",
            ]
            items = []
            for url in sample_urls:
                try:
                    # 同步调异步
                    result = asyncio.run(service.scrape_url(url, timeout=15))
                    items.append({
                        "url": url,
                        "source": source_id,
                        "title": result.get("title", ""),
                        "content": result.get("content", "")[:1000],
                        "collected_at": datetime.datetime.utcnow().isoformat()
                    })
                except Exception as e:
                    logger.warning(f"    {url}: {e}")

            output_file = self._save_raw(source_id, items)
            return len(items), output_file
        except ImportError as e:
            logger.warning(f"  [cloak_scraper] 模块导入失败: {e}，降级为HTTP模式")
            return self._engine_http_fetch(source_id, source)

    def _engine_crawler(self, source_id: str, source: dict) -> tuple:
        """引擎: URL批量爬虫 — httpx直接爬取"""
        logger.info(f"  [crawler] 调用URL批量爬虫...")
        try:
            import httpx
            items = []
            sample_urls = [
                "https://httpbin.org/html",
                "https://example.com",
            ]
            with httpx.Client(timeout=15) as client:
                for url in sample_urls:
                    try:
                        r = client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                        items.append({
                            "url": url,
                            "source": source_id,
                            "status_code": r.status_code,
                            "content_length": len(r.text),
                            "content_preview": r.text[:500],
                            "collected_at": datetime.datetime.utcnow().isoformat()
                        })
                    except Exception as e:
                        logger.warning(f"    {url}: {e}")

            output_file = self._save_raw(source_id, items)
            return len(items), output_file
        except ImportError:
            logger.warning("  [crawler] httpx未安装，降级")
            return 0, None

    def _engine_web_search(self, source_id: str, source: dict) -> tuple:
        """引擎: 百度搜索 — 通过web_search模拟采集"""
        logger.info(f"  [web_search] 搜索行业数据...")
        try:
            # 尝试通过终端的curl模拟搜索
            search_terms = source.get("search_terms", ["AI名片 行业", "企业数字化转型 2026"])
            items = []

            for term in search_terms[:2]:  # 限制搜索次数
                try:
                    result = subprocess.run(
                        ["curl", "-s", "-L",
                         f"https://www.baidu.com/s?wd={term}",
                         "-H", "User-Agent: Mozilla/5.0"],
                        capture_output=True, text=True, timeout=15
                    )
                    items.append({
                        "search_term": term,
                        "source": source_id,
                        "content_length": len(result.stdout),
                        "content_preview": result.stdout[:800],
                        "collected_at": datetime.datetime.utcnow().isoformat()
                    })
                except Exception as e:
                    logger.warning(f"    search '{term}': {e}")

            output_file = self._save_raw(source_id, items)
            return len(items), output_file
        except Exception as e:
            logger.warning(f"  [web_search] 采集失败: {e}")
            return 0, None

    def _engine_qichacha_client(self, source_id: str, source: dict) -> tuple:
        """引擎: 企查查 — 调用现有客户端"""
        logger.info(f"  [qichacha] 调用企查查客户端...")
        try:
            from app.services.qichacha_client import search_company
            items = []
            # 示例企业搜索
            sample_companies = ["阿里巴巴", "腾讯科技"]
            for name in sample_companies:
                try:
                    data = search_company(name)
                    items.append({
                        "company": name,
                        "source": source_id,
                        "data": data,
                        "collected_at": datetime.datetime.utcnow().isoformat()
                    })
                except Exception as e:
                    logger.warning(f"    {name}: {e}")

            output_file = self._save_raw(source_id, items)
            return len(items), output_file
        except ImportError:
            logger.warning("  [qichacha] 模块不可用，降级为HTTP搜索")
            return self._engine_http_fetch(source_id, source)

    def _engine_feedback_loop(self, source_id: str, source: dict) -> tuple:
        """引擎: 用户行为反馈流 — 读取feedback.db"""
        logger.info(f"  [feedback_loop] 采集用户反馈数据...")
        try:
            import sqlite3
            feedback_db = os.path.join(BACKEND_DIR, "data", "feedback.db")
            items = []

            if os.path.exists(feedback_db):
                conn = sqlite3.connect(feedback_db)
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT * FROM feedback ORDER BY updated_at DESC LIMIT 50")
                rows = cur.fetchall()
                for row in rows:
                    items.append({
                        "source": source_id,
                        "user_id": row["user_id"],
                        "item_id": row["item_id"],
                        "feedback_type": row["feedback_type"],
                        "score": row["score"],
                        "timestamp": row["updated_at"],
                        "collected_at": datetime.datetime.utcnow().isoformat()
                    })
                conn.close()
                logger.info(f"    feedback.db: {len(items)} 条反馈")
            else:
                logger.info(f"    feedback.db 不存在，跳过")

            output_file = self._save_raw(source_id, items)
            return len(items), output_file
        except Exception as e:
            logger.warning(f"  [feedback_loop] 采集失败: {e}")
            return 0, None

    def _engine_user_behavior(self, source_id: str, source: dict) -> tuple:
        """引擎: 用户行为数据 — 在线学习权重"""
        logger.info(f"  [user_behavior] 采集在线学习权重...")
        try:
            weights_file = os.path.join(BACKEND_DIR, "data", "online_weights.json")
            items = []
            if os.path.exists(weights_file):
                with open(weights_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                items.append({
                    "source": source_id,
                    "weights": data,
                    "collected_at": datetime.datetime.utcnow().isoformat()
                })
            output_file = self._save_raw(source_id, items)
            return len(items), output_file
        except Exception as e:
            logger.warning(f"  [user_behavior] 采集失败: {e}")
            return 0, None

    def _engine_web_content(self, source_id: str, source: dict) -> tuple:
        """引擎: 网页RAG数据 — 读取现有训练数据"""
        logger.info(f"  [web_content] 采集RAG数据...")
        try:
            items = []
            for fname in ["training_data.json", "v2_training_data.json"]:
                fpath = os.path.join(BACKEND_DIR, "data", fname)
                if os.path.exists(fpath):
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    items.append({
                        "source": source_id,
                        "file": fname,
                        "sample_count": len(data) if isinstance(data, list) else 1,
                        "data_preview": data[:3] if isinstance(data, list) else data,
                        "collected_at": datetime.datetime.utcnow().isoformat()
                    })
            output_file = self._save_raw(source_id, items)
            return len(items), output_file
        except Exception as e:
            logger.warning(f"  [web_content] 采集失败: {e}")
            return 0, None

    def _engine_http_fetch(self, source_id: str, source: dict) -> tuple:
        """降级: HTTP通用抓取"""
        logger.info(f"  [HTTP降级] 通用网页抓取...")
        try:
            import httpx
            items = []
            sample_urls = ["https://example.com", "https://httpbin.org/get"]
            with httpx.Client(timeout=10) as client:
                for url in sample_urls:
                    try:
                        r = client.get(url)
                        items.append({
                            "url": url,
                            "source": source_id,
                            "status_code": r.status_code,
                            "content_preview": r.text[:300],
                            "collected_at": datetime.datetime.utcnow().isoformat()
                        })
                    except Exception:
                        pass
            output_file = self._save_raw(source_id, items)
            return len(items), output_file
        except ImportError:
            return 0, None

    def _engine_knowledge_base(self, source_id: str, source: dict) -> tuple:
        """引擎: 知识库 — 读取心智模型数据"""
        logger.info(f"  [knowledge_base] 采集知识库数据...")
        try:
            import sqlite3
            items = []
            # 检查是否存在SQLite知识库
            kb_paths = [
                os.path.join(BACKEND_DIR, "data", "digital_brochure.db"),
            ]
            for db_path in kb_paths:
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    conn.row_factory = sqlite3.Row
                    cur = conn.cursor()
                    try:
                        cur.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 10")
                        tables = [row["name"] for row in cur.fetchall()]
                        items.append({
                            "source": source_id,
                            "db_file": os.path.basename(db_path),
                            "tables": tables,
                            "collected_at": datetime.datetime.utcnow().isoformat()
                        })
                    except Exception:
                        pass
                    conn.close()

            output_file = self._save_raw(source_id, items)
            return len(items), output_file
        except Exception:
            return self._engine_fallback(source_id, source)

    def _engine_xiaohongshu(self, source_id: str, source: dict) -> tuple:
        """引擎: 小红书 — 调用baidu_search_xhs.py搜索"""
        logger.info(f"  [xiaohongshu] 调用小红书百度搜索...")
        xhs_script = os.path.join(BACKEND_DIR, "scripts", "baidu_search_xhs.py")
        if not os.path.exists(xhs_script):
            logger.warning(f"  xhs脚本不存在: {xhs_script}，降级为百度搜索")
            return self._engine_web_search(source_id, source)

        try:
            result = subprocess.run(
                [sys.executable, xhs_script],
                capture_output=True, text=True, timeout=60
            )
            items = []
            if result.stdout:
                # 尝试解析输出中的JSON
                try:
                    parsed = json.loads(result.stdout)
                    if isinstance(parsed, list):
                        items = parsed
                    elif isinstance(parsed, dict):
                        items = parsed.get("results", parsed.get("items", [parsed]))
                except json.JSONDecodeError:
                    # 非JSON输出，按文本行处理
                    for line in result.stdout.split("\n")[:20]:
                        line = line.strip()
                        if line and len(line) > 20:
                            items.append({
                                "content": line[:500],
                                "source": source_id,
                                "collected_at": datetime.datetime.utcnow().isoformat()
                            })

            output_file = self._save_raw(source_id, items)
            logger.info(f"    ✅ 小红书: {len(items)} 条")
            return len(items), output_file
        except subprocess.TimeoutExpired:
            logger.warning("  xhs脚本超时，降级")
            return self._engine_web_search(source_id, source)

    def _engine_crm_data(self, source_id: str, source: dict) -> tuple:
        """引擎: CRM数据 — 从digital_brochure.db读取真实用户/匹配/交易数据"""
        logger.info(f"  [crm_data] 从CRM数据库采集...")
        crm_db = os.path.join(BACKEND_DIR, "data", "digital_brochure.db")
        items = []

        if not os.path.exists(crm_db):
            logger.warning(f"  CRM数据库不存在: {crm_db}")
            return 0, None

        try:
            import sqlite3
            conn = sqlite3.connect(crm_db)
            conn.row_factory = sqlite3.Row

            # 用户数据 — 最新的50个活跃用户
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, name, company, industry, email, created_at
                    FROM users ORDER BY created_at DESC LIMIT 50
                """)
                for row in cur.fetchall():
                    items.append({
                        "source": source_id,
                        "type": "user",
                        "user_id": row["id"],
                        "name": row["name"],
                        "company": row["company"],
                        "industry": row["industry"],
                        "email": row["email"],
                        "created_at": row["created_at"],
                        "collected_at": datetime.datetime.utcnow().isoformat()
                    })
                logger.info(f"    users: {len([i for i in items if i['type']=='user'])} 条")
            except Exception as e:
                logger.warning(f"    users表读取失败: {e}")

            # 匹配记录 — 最新的50条匹配
            try:
                cur.execute("""
                    SELECT id, user_id, target_id, match_score, status, created_at
                    FROM match_records ORDER BY created_at DESC LIMIT 50
                """)
                for row in cur.fetchall():
                    items.append({
                        "source": source_id,
                        "type": "match_record",
                        "match_id": row["id"],
                        "user_id": row["user_id"],
                        "target_id": row["target_id"],
                        "match_score": row["match_score"],
                        "status": row["status"],
                        "created_at": row["created_at"],
                        "collected_at": datetime.datetime.utcnow().isoformat()
                    })
                logger.info(f"    match_records: {len([i for i in items if i['type']=='match_record'])} 条")
            except Exception:
                pass

            # 交易数据
            try:
                cur.execute("""
                    SELECT id, deal_id, amount, stage, probability, created_at
                    FROM deal ORDER BY created_at DESC LIMIT 50
                """)
                for row in cur.fetchall():
                    items.append({
                        "source": source_id,
                        "type": "deal",
                        "deal_id": row["deal_id"] if row["deal_id"] else row["id"],
                        "amount": str(row["amount"]),
                        "stage": row["stage"],
                        "probability": row["probability"],
                        "created_at": row["created_at"],
                        "collected_at": datetime.datetime.utcnow().isoformat()
                    })
                logger.info(f"    deals: {len([i for i in items if i['type']=='deal'])} 条")
            except Exception:
                pass

            # 用户标签 — 用于匹配模型训练
            try:
                cur.execute("""
                    SELECT id, user_id, tag, weight, created_at
                    FROM user_tags ORDER BY created_at DESC LIMIT 100
                """)
                for row in cur.fetchall():
                    items.append({
                        "source": source_id,
                        "type": "user_tag",
                        "user_id": row["user_id"],
                        "tag": row["tag"],
                        "weight": row["weight"],
                        "created_at": row["created_at"],
                        "collected_at": datetime.datetime.utcnow().isoformat()
                    })
                logger.info(f"    user_tags: {len([i for i in items if i['type']=='user_tag'])} 条")
            except Exception:
                pass

            conn.close()

            output_file = self._save_raw(source_id, items)
            return len(items), output_file

        except Exception as e:
            logger.warning(f"  CRM采集失败: {e}")
            return 0, None

    def _engine_enterprise_websites(self, source_id: str, source: dict) -> tuple:
        """引擎: 企业官网 — 从CRM用户数据中提取公司名→搜索官网"""
        logger.info(f"  [enterprise_websites] 从CRM用户公司名→搜索官网...")
        crm_db = os.path.join(BACKEND_DIR, "data", "digital_brochure.db")
        items = []

        if not os.path.exists(crm_db):
            logger.warning(f"  CRM不存在，降级")
            return self._engine_http_fetch(source_id, source)

        try:
            import sqlite3, httpx
            conn = sqlite3.connect(crm_db)
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT company FROM users WHERE company IS NOT NULL AND company != '' LIMIT 20")
            companies = [r[0] for r in cur.fetchall()]
            conn.close()

            logger.info(f"    CRM中 {len(companies)} 个公司名")

            with httpx.Client(timeout=10, verify=False) as client:
                for company in companies:
                    try:
                        # 百度搜索公司官网
                        r = client.get(
                            f"https://www.baidu.com/s?wd={company} 官网",
                            headers={"User-Agent": "Mozilla/5.0"}
                        )
                        items.append({
                            "company": company,
                            "source": source_id,
                            "search_result_length": len(r.text),
                            "search_html_preview": r.text[:500],
                            "collected_at": datetime.datetime.utcnow().isoformat()
                        })
                    except Exception as e:
                        logger.warning(f"    {company}: {e}")

            output_file = self._save_raw(source_id, items)
            return len(items), output_file

        except ImportError:
            return self._engine_fallback(source_id, source)

    def _engine_fallback(self, source_id: str, source: dict) -> tuple:
        """兜底: 引擎未实现时创建空数据文件"""
        logger.info(f"  [fallback] {source_id}: 引擎未实现({source.get('engine','?')})")
        items = [{
            "source": source_id,
            "engine": source.get("engine", "unknown"),
            "note": "引擎未接入真实采集器，需Phase升级",
            "collected_at": datetime.datetime.utcnow().isoformat()
        }]
        output_file = self._save_raw(source_id, items)
        return 0, output_file

    # ─── 数据落地 ─────────────────────────────────────────

    def _save_raw(self, source_id: str, items: list) -> str:
        """写入原始数据文件到 data/raw/ """
        ts = int(time.time())
        fname = f"{source_id}_{ts}.json"
        fpath = os.path.join(RAW_DATA_DIR, fname)
        data = {
            "source_id": source_id,
            "collected_at": datetime.datetime.utcnow().isoformat(),
            "count": len(items),
            "items": items
        }
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return fpath

    def get_status_report(self) -> dict:
        """生成状态报告"""
        sources = self._registry.get("sources", {})
        now = time.time()

        source_status = {}
        for sid, src in sources.items():
            last = self._state["last_collected"].get(sid, 0)
            freq = src.get("frequency_min", 60)
            age = (now - last) / 60 if last > 0 else float("inf")
            due = age >= freq

            source_status[sid] = {
                "name": src.get("name", ""),
                "enabled": src.get("enabled", False),
                "last_collected_min_ago": round(age, 1),
                "frequency_min": freq,
                "due": due,
                "models_fed": src.get("models_fed", []),
                "engine": src.get("engine", ""),
            }

        return {
            "total_sources": len(sources),
            "enabled": sum(1 for s in sources.values() if s.get("enabled")),
            "source_status": source_status,
            "total_items_collected": self._state.get("total_items", 0),
            "last_run": self._state.get("last_run", "never"),
        }


def run_once():
    """单次执行入口（用于cron）"""
    orchestrator = CrawlerOrchestrator()
    results = orchestrator.collect_all_due()
    report = orchestrator.get_status_report()

    active = sum(1 for r in results if r["status"] == "success")
    errors = sum(1 for r in results if r["status"] == "error")
    items = sum(r.get("items_count", 0) for r in results)

    output = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "sources_collected": len(results),
        "success": active,
        "errors": errors,
        "total_items": items,
        "report": report,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(run_once())

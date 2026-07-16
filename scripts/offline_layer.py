#!/usr/bin/env python3
"""
offline_layer.py — 三明治架构离线层：744B大模型增强匹配

=== 核心功能 ===
1. 连接 Mac Mini 744B 大模型（GLM-5.2 Colibri），进行深度语义理解
2. 对名片数据做增强匹配（结合向量 + 大模型推理）
3. 双模式：744B 可用时用大模型增强，不可用时自动降级到纯 embedding 匹配
4. 可通过 CLI 运行增强任务，也可作为模块被 FastAPI 后端导入

=== 配置 ===
环境变量或直接修改 COLIBRI_API:
  OFFLINE_744B_URL=http://192.168.1.233:9091/v1/completions
  OFFLINE_MODEL=glm-5.2-colibri

=== API 端点（由 backend/app/routers/offline_router.py 提供） ===
  POST /api/matching/enhance-match  — 增强匹配
  GET  /api/matching/offline-status  — 离线层状态

=== CLI 使用 ===
  python offline_layer.py --enhance-all          # 全部增强
  python offline_layer.py --enhance-match ...     # 单条匹配
  python offline_layer.py --status                # 查看状态
"""

import argparse
import json
import logging
import os
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── 配置 ──────────────────────────────────────────────────────────────────
OFFLINE_744B_URL = os.environ.get(
    "OFFLINE_744B_URL",
    "http://192.168.1.233:9091/v1/completions"
)
"""Mac Mini 744B Colibri 推理 API"""

OFFLINE_MODEL = os.environ.get("OFFLINE_MODEL", "glm-5.2-colibri")
"""744B 模型名称"""

OFFLINE_TIMEOUT = int(os.environ.get("OFFLINE_TIMEOUT", "600"))
"""744B API 超时（秒）"""

OFFLINE_FALLBACK_EMBEDDING = os.environ.get(
    "OFFLINE_FALLBACK_EMBEDDING", "BAAI/bge-m3"
)
"""降级时使用的 embedding 模型"""

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent  # D:/AI数智名片
DATA_DIR = PROJECT_ROOT / "training_data"
STATE_FILE = DATA_DIR / "offline_layer_state.json"


# ── 744B API 客户端 ──────────────────────────────────────────────────────

class ColibriClient:
    """Mac Mini 744B Colibri 推理 API 客户端

    支持双模式：
    - 正常模式：调用 744B 大模型做深度语义理解
    - 降级模式：744B 不可用时，基于规则/统计做基础分析
    """

    def __init__(self, api_url: str = None, model: str = None,
                 timeout: int = None):
        self.api_url = api_url or OFFLINE_744B_URL
        self.model = model or OFFLINE_MODEL
        self.timeout = timeout or OFFLINE_TIMEOUT
        self._available = None  # None = 未检测, True/False = 已检测

    def check_health(self, timeout: int = 5) -> bool:
        """检测 744B 服务是否可用"""
        base = self.api_url.rstrip("/")
        # colibri 常见的健康端点
        health_urls = [
            base.replace("/v1/completions", "/health"),
            base.replace("/v1/completions", "/v1/health"),
            base.replace("/v1/completions", ""),
        ]
        for url in health_urls:
            try:
                req = urllib.request.Request(url, method="GET")
                resp = urllib.request.urlopen(req, timeout=timeout)
                if resp.status == 200:
                    self._available = True
                    return True
            except Exception:
                continue
        # fallback: 尝试发一个极简请求
        try:
            data = json.dumps({
                "model": self.model,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1,
            }).encode()
            req = urllib.request.Request(
                self.api_url, data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=timeout)
            self._available = True
            return True
        except Exception:
            self._available = False
            return False

    @property
    def is_available(self) -> Optional[bool]:
        """返回服务可用性状态（None=未检测）"""
        return self._available

    def analyze(self, text: str, max_tokens: int = 512,
                temperature: float = 0.1) -> dict:
        """调用 744B 对名片/资料做深度语义分析

        Args:
            text: 名片文本（名称、描述、标签等）
            max_tokens: 最大生成 token 数
            temperature: 温度参数（越低越确定）

        Returns:
            dict: {
                "success": True/False,
                "analysis": "分析结果文本" or "",
                "keywords": [...],  # 提取的关键词列表
                "categories": [...],  # 业务分类
                "match_score": 0-100,  # 置信度
                "error": "错误信息" or None,
            }
        """
        prompt = f"""你是一位专业的商业智能分析师。请分析以下客户/供应商/经销商名片资料，输出结构化分析结果。

分析要求：
1. 提取核心业务关键词（5-10个）
2. 判断所属业务领域和行业分类
3. 评估资料完整性和可信度（0-100分）
4. 总结该实体的核心需求和价值主张

资料：
{text[:3000]}

请以JSON格式输出（不要包含markdown代码块标记）：
{{
  "keywords": ["关键词1", "关键词2", ...],
  "categories": ["类别1", "类别2", ...],
  "summary": "一句话总结（30字内）",
  "detail_analysis": "详细分析（100字内）",
  "match_score": 0-100的整数,
  "completeness": 0-100的整数
}}"""

        try:
            data = json.dumps({
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }).encode()

            req = urllib.request.Request(
                self.api_url, data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=self.timeout)
            result = json.loads(resp.read())
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

            # 尝试从回复中提取 JSON
            analysis_data = self._extract_json(content)
            if analysis_data:
                return {
                    "success": True,
                    "analysis": content,
                    "keywords": analysis_data.get("keywords", []),
                    "categories": analysis_data.get("categories", []),
                    "summary": analysis_data.get("summary", ""),
                    "detail_analysis": analysis_data.get("detail_analysis", ""),
                    "match_score": int(analysis_data.get("match_score", 50)),
                    "completeness": int(analysis_data.get("completeness", 50)),
                    "error": None,
                }

            # JSON 解析失败，返回原始内容
            return {
                "success": True,
                "analysis": content,
                "keywords": [],
                "categories": [],
                "summary": "",
                "detail_analysis": content[:200],
                "match_score": 50,
                "completeness": 50,
                "error": "response_parse_failed",
            }

        except urllib.error.HTTPError as e:
            error_msg = f"744B HTTP {e.code}: {e.read().decode(errors='ignore')[:200]}"
            logger.warning(f"[744B] {error_msg}")
            return {"success": False, "analysis": "", "keywords": [],
                    "categories": [], "summary": "", "detail_analysis": "",
                    "match_score": 0, "completeness": 0, "error": error_msg}
        except Exception as e:
            error_msg = f"744B 调用失败: {e}"
            logger.warning(f"[744B] {error_msg}")
            return {"success": False, "analysis": "", "keywords": [],
                    "categories": [], "summary": "", "detail_analysis": "",
                    "match_score": 0, "completeness": 0, "error": error_msg}

    def enhance_match(self, query: str, candidates: list[dict],
                      top_k: int = 5) -> list[dict]:
        """对候选匹配结果做 744B 增强排序

        Args:
            query: 用户搜索/查询文本
            candidates: 候选匹配结果列表，每项含 {id, name, text, score, ...}
            top_k: 返回前 K 个结果

        Returns:
            list[dict]: 增强排序后的结果，每项含原始信息 + 744B 分析
        """
        if not candidates:
            return []

        # 取前 20 个候选给 744B 做深度排序（限制输入长度）
        sorted_candidates = sorted(candidates, key=lambda x: x.get("score", 0), reverse=True)
        top_candidates = sorted_candidates[:20]

        # 构建 prompt
        candidate_texts = []
        for i, c in enumerate(top_candidates):
            name = c.get("name", c.get("text", f"候选{i+1}"))
            desc = c.get("text", c.get("description", ""))
            candidate_texts.append(f"#{i+1} {name}：{desc[:150]}")

        prompt = f"""你是一位专业的商业匹配分析师。请根据用户的查询，对候选结果进行重新排序和评分。

用户查询：{query[:500]}

候选列表：
{chr(10).join(candidate_texts)}

分析要求：
1. 理解用户查询的真实需求和意图
2. 逐个评估每个候选与查询的匹配程度
3. 考虑业务领域互补性、合作潜力
4. 输出重新排序后的评分

请以JSON格式输出（不要包含markdown代码块标记）：
{{
  "rankings": [
    {{"rank": 1, "candidate_index": 0-based索引, "score": 0-100整数, "reason": "匹配理由"}},
    ...
  ],
  "query_intent": "用户查询意图分析",
  "suggestion": "进一步匹配建议"
}}"""

        try:
            data = json.dumps({
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1024,
                "temperature": 0.1,
            }).encode()

            req = urllib.request.Request(
                self.api_url, data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=self.timeout)
            result = json.loads(resp.read())
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

            analysis_data = self._extract_json(content)
            if analysis_data and "rankings" in analysis_data:
                rankings = analysis_data["rankings"]
                # 应用 744B 排评分到候选结果
                for r in rankings:
                    idx = r.get("candidate_index", -1)
                    if 0 <= idx < len(top_candidates):
                        top_candidates[idx]["llm_score"] = r.get("score", 50)
                        top_candidates[idx]["llm_reason"] = r.get("reason", "")
                        top_candidates[idx]["enhanced_score"] = round(
                            0.4 * top_candidates[idx].get("score", 0) +
                            0.6 * r.get("score", 50) / 100.0,
                            4
                        )
                # 按 enhanced_score 重新排序
                scored = [c for c in top_candidates if "enhanced_score" in c]
                unscored = [c for c in top_candidates if "enhanced_score" not in c]
                scored.sort(key=lambda x: x["enhanced_score"], reverse=True)
                result_list = scored + unscored
                return result_list[:top_k]

            # JSON 解析失败，返回原始排序
            return sorted_candidates[:top_k]

        except Exception as e:
            logger.warning(f"[744B] enhance_match 调用失败，使用原始排序: {e}")
            return sorted_candidates[:top_k]

    @staticmethod
    def _extract_json(text: str) -> Optional[dict]:
        """从 LLM 回复中提取 JSON 对象"""
        import re
        # 尝试直接解析
        text = text.strip()
        if text.startswith("{"):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
        # 尝试从代码块中提取
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass
        # 尝试从 ``` 到 ``` 或文本中提取最外层 {}
        brace_match = re.search(r'\{[\s\S]*\}', text)
        if brace_match:
            try:
                return json.loads(brace_match.group())
            except json.JSONDecodeError:
                pass
        return None


# ── Embedding 降级服务 ──────────────────────────────────────────────────

class EmbeddingFallbackService:
    """当 744B 不可用时的降级 embedding 匹配服务"""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or OFFLINE_FALLBACK_EMBEDDING
        self._model = None
        self._dim = 768

    def _load(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            test_vec = self._model.encode(["测试"], normalize_embeddings=True)
            self._dim = test_vec.shape[-1]
        except Exception as e:
            logger.warning(f"[Fallback] Embedding model 加载失败: {e}")
            self._model = None

    def embed(self, text: str) -> list[float]:
        """生成 embedding 向量"""
        self._load()
        if self._model:
            vec = self._model.encode([text], normalize_embeddings=True)[0]
            return vec.tolist()
        # 最坏情况：基于 hash 的伪随机向量
        import hashlib
        import numpy as np
        rng = np.random.RandomState(
            int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        )
        vec = rng.randn(self._dim).astype(np.float32)
        norm = np.linalg.norm(vec)
        if norm > 1e-8:
            vec = vec / norm
        return vec.tolist()

    def cosine_similarity(self, vec_a: list[float], vec_b: list[float]) -> float:
        """计算余弦相似度"""
        import numpy as np
        a = np.array(vec_a, dtype=np.float32)
        b = np.array(vec_b, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a < 1e-8 or norm_b < 1e-8:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def match(self, query: str, candidates: list[dict],
              top_k: int = 5) -> list[dict]:
        """纯 embedding 匹配（降级模式）"""
        query_vec = self.embed(query)
        scored = []
        for c in candidates:
            text = c.get("name", "") + "：" + c.get("text", c.get("description", ""))
            cand_vec = self.embed(text)
            score = self.cosine_similarity(query_vec, cand_vec)
            scored.append({**c, "embedding_score": round(score, 4),
                          "enhanced_score": round(score, 4),
                          "llm_score": 0, "llm_reason": "fallback_embedding"})
        scored.sort(key=lambda x: x["embedding_score"], reverse=True)
        return scored[:top_k]


# ── 增强匹配核心 ────────────────────────────────────────────────────────

class OfflineLayer:
    """离线层核心 — 协调 744B 大模型与 embedding 降级"""

    def __init__(self):
        self._colibri = None
        self._fallback = None
        self._colibri_available = None

    @property
    def colibri(self) -> ColibriClient:
        if self._colibri is None:
            self._colibri = ColibriClient()
        return self._colibri

    @property
    def fallback(self) -> EmbeddingFallbackService:
        if self._fallback is None:
            self._fallback = EmbeddingFallbackService()
        return self._fallback

    def _check_colibri(self) -> bool:
        """检查 744B 是否可用，结果缓存"""
        if self._colibri_available is None:
            self._colibri_available = self.colibri.check_health()
        return self._colibri_available

    def get_status(self) -> dict:
        """获取离线层整体状态"""
        # 检测 744B 状态
        colibri_ok = self._check_colibri()

        # 加载保存的状态
        last_run = None
        last_results = []
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE) as f:
                    state = json.load(f)
                last_run = state.get("last_run")
                last_results = state.get("results", [])
            except Exception:
                pass

        return {
            "colibri_744b": {
                "url": OFFLINE_744B_URL,
                "model": OFFLINE_MODEL,
                "available": colibri_ok,
                "mode": "llm_enhanced" if colibri_ok else "embedding_fallback",
            },
            "last_enhance": {
                "time": last_run,
                "results": last_results,
            },
        }

    def enhance_match(self, query: str, candidates: list[dict],
                      top_k: int = 5, force_fallback: bool = False) -> dict:
        """增强匹配 — 自动选择 744B 或 embedding 降级

        Args:
            query: 用户查询
            candidates: 候选结果列表 [{id, name, text/description, score, ...}]
            top_k: 返回前 K 个
            force_fallback: 强制使用降级模式（跳过 744B）

        Returns:
            {
                "mode": "llm_enhanced" | "embedding_fallback",
                "results": [...],
                "query_intent": "...",
                "suggestion": "...",
                "latency_ms": 123.45,
            }
        """
        t0 = time.time()

        # 尝试 744B 模式
        if not force_fallback and self._check_colibri():
            logger.info("[OfflineLayer] 使用 744B 增强模式")
            try:
                enhanced_results = self.colibri.enhance_match(query, candidates, top_k)
                latency = round((time.time() - t0) * 1000, 2)
                return {
                    "mode": "llm_enhanced",
                    "results": enhanced_results,
                    "latency_ms": latency,
                }
            except Exception as e:
                logger.warning(f"[OfflineLayer] 744B 增强失败，降级: {e}")

        # 降级到 embedding
        logger.info("[OfflineLayer] 使用 Embedding 降级模式")
        fallback_results = self.fallback.match(query, candidates, top_k)
        latency = round((time.time() - t0) * 1000, 2)
        return {
            "mode": "embedding_fallback",
            "results": fallback_results,
            "latency_ms": latency,
        }

    def enhance_business_card(self, card_data: dict) -> dict:
        """对单条名片做深度分析（用于增强 embedding 存储）

        Args:
            card_data: {id, name, description, text, tags, ...}

        Returns:
            {enhanced_text, analysis, embedding, ...}
        """
        # 构建分析文本
        name = card_data.get("name", card_data.get("title", ""))
        desc = card_data.get("desc", card_data.get("description", card_data.get("text", "")))
        tags = card_data.get("tags", [])
        tag_str = "、".join(tags) if isinstance(tags, list) else str(tags)
        text = f"{name}：{desc}"
        if tag_str:
            text += f"\n标签：{tag_str}"

        # 调用 744B 分析
        if self._check_colibri():
            analysis = self.colibri.analyze(text, max_tokens=256)
            if analysis.get("success"):
                enhanced_text = (
                    f"{text}\n\n"
                    f"[744B分析]\n"
                    f"关键词：{', '.join(analysis.get('keywords', []))}\n"
                    f"分类：{', '.join(analysis.get('categories', []))}\n"
                    f"总结：{analysis.get('summary', '')}\n"
                    f"详细：{analysis.get('detail_analysis', '')}"
                )
                return {
                    "enhanced_text": enhanced_text,
                    "analysis": analysis,
                    "embedding_source": "llm_enhanced",
                }

        # 降级
        return {
            "enhanced_text": text,
            "analysis": {"summary": "", "keywords": [],
                        "categories": [], "match_score": 50},
            "embedding_source": "raw_text",
        }


# ── 全局单例 ────────────────────────────────────────────────────────────

_global_offline_layer: Optional[OfflineLayer] = None


def get_offline_layer() -> OfflineLayer:
    """获取 OfflineLayer 全局单例"""
    global _global_offline_layer
    if _global_offline_layer is None:
        _global_offline_layer = OfflineLayer()
    return _global_offline_layer


# ── CLI 入口 ─────────────────────────────────────────────────────────────

def cmd_status(args):
    """查看离线层状态"""
    layer = get_offline_layer()
    status = layer.get_status()
    print(f"\n{'='*50}")
    print("📊 离线层状态")
    print(f"{'='*50}")
    colibri = status["colibri_744b"]
    icon = "✅" if colibri["available"] else "❌"
    print(f"  744B服务: {icon}")
    print(f"  地址: {colibri['url']}")
    print(f"  模型: {colibri['model']}")
    print(f"  当前模式: {colibri['mode']}")
    last = status["last_enhance"]
    if last["time"]:
        print(f"  最后增强: {last['time']}")
        for r in last.get("results", []):
            print(f"    {r}")
    else:
        print(f"  最后增强: 从未运行")
    print(f"{'='*50}")


def cmd_enhance_all(args):
    """增强所有集合（调用 744B 重新生成增强 embedding）"""
    from app.ai.embedding_service import get_embedding_service
    from app.ai.vector_store import get_vector_store

    layer = get_offline_layer()
    emb_svc = get_embedding_service()
    store = get_vector_store()

    collections = ["customers", "suppliers", "dealers"]
    labels = {"customers": "客户", "suppliers": "供应商", "dealers": "经销商"}
    results = []

    print(f"\n{'='*50}")
    print("🚀 离线层批量增强开始")
    print(f"{'='*50}")

    for col_name in collections:
        print(f"\n📦 {labels.get(col_name, col_name)} ({col_name}):")
        try:
            # 读取现有数据
            collection = store._get_or_create_collection(col_name)
            existing = collection.get()
            if not existing or not existing["ids"]:
                print(f"  ⚠️ 空集合")
                results.append({"collection": col_name, "count": 0, "enhanced": 0})
                continue

            ids = existing["ids"]
            metadatas = existing.get("metadatas", [{}] * len(ids))
            documents = existing.get("documents", [""] * len(ids))

            count = len(ids)
            enhanced = 0
            for i, (doc_id, meta, doc) in enumerate(zip(ids, metadatas, documents)):
                name = meta.get("name", doc_id) if meta else doc_id
                print(f"    [{i+1}/{count}] {str(name)[:30]}...", end=" ", flush=True)

                if args.dry_run:
                    print("跳过(试运行)")
                    continue

                card_data = {
                    "id": doc_id,
                    "name": name,
                    "text": doc,
                }
                result = layer.enhance_business_card(card_data)
                if result["embedding_source"] == "llm_enhanced":
                    enhanced += 1
                    print("✅")
                else:
                    print("⬇️ 降级")
                time.sleep(0.1)  # 避免 API 限流

            results.append({"collection": col_name, "count": count, "enhanced": enhanced})
            print(f"  -> {enhanced}/{count} 条增强")

        except Exception as e:
            logger.error(f"[OfflineLayer] {col_name} 增强失败: {e}")
            results.append({"collection": col_name, "count": 0, "enhanced": 0, "error": str(e)})

    # 保存状态
    os.makedirs(DATA_DIR, exist_ok=True)
    state = {
        "last_run": datetime.now().isoformat(),
        "results": results,
        "dry_run": args.dry_run,
    }
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print("📊 增强报告")
    for r in results:
        print(f"  {r['collection']:15s} {r.get('enhanced',0):3d}/{r.get('count',0):3d} 条")
    print(f"{'='*50}")


def cmd_enhance_match(args):
    """测试单条匹配（CLI 调试用）"""
    query = args.query or "跨境支付东南亚"
    candidates = [
        {"id": "1", "name": "深圳前海跨境支付科技", "text": "专注东南亚跨境支付解决方案，支持Shopee/Lazada收款"},
        {"id": "2", "name": "杭州区块链数据服务", "text": "区块链供应链金融平台，服务跨境电商"},
        {"id": "3", "name": "上海AI客服系统集成商", "text": "多语言AI客服系统，支持中英日韩"},
        {"id": "4", "name": "广州国际物流报关行", "text": "中韩物流专线，通关一体化服务"},
        {"id": "5", "name": "北京数字营销机构", "text": "韩国市场数字营销，Naver/Kakao广告代理"},
    ]
    if args.candidates:
        try:
            candidates = json.loads(args.candidates)
        except json.JSONDecodeError:
            print("⚠️ candidates JSON 解析失败，使用默认数据")

    layer = get_offline_layer()
    result = layer.enhance_match(query, candidates, top_k=args.top_k,
                                 force_fallback=args.fallback)

    print(f"\n{'='*50}")
    print(f"🔍 查询: {query}")
    print(f"模式: {result['mode']}")
    print(f"延迟: {result.get('latency_ms', 0):.1f}ms")
    print(f"{'='*50}")
    for i, r in enumerate(result.get("results", [])):
        llm_score = r.get("llm_score", 0)
        embed_score = r.get("embedding_score", r.get("score", 0))
        enhanced = r.get("enhanced_score", embed_score)
        reason = r.get("llm_reason", "")
        print(f"\n  #{i+1} {r.get('name', '?')}")
        print(f"     增强分: {enhanced:.4f}  |  向量分: {embed_score:.4f}  |  LLM分: {llm_score}")
        if reason:
            print(f"     理由: {reason[:120]}")
    print(f"{'='*50}")


def main():
    parser = argparse.ArgumentParser(
        description="三明治架构离线层 — 744B大模型增强匹配",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python offline_layer.py --status                   # 查看状态
  python offline_layer.py --enhance-all               # 全部增强
  python offline_layer.py --enhance-all --dry-run     # 试运行
  python offline_layer.py --enhance-match             # 测试匹配
  python offline_layer.py --enhance-match --query "找做跨境支付的供应商"
        """,
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="试运行（不实际调用744B）")

    # 匹配参数
    parser.add_argument("--enhance-match", action="store_true",
                        help="测试单条匹配")
    parser.add_argument("--query", type=str, default="",
                        help="查询文本")
    parser.add_argument("--candidates", type=str, default="",
                        help="候选JSON（可选）")
    parser.add_argument("--top-k", type=int, default=5,
                        help="返回前K个结果")
    parser.add_argument("--fallback", action="store_true",
                        help="强制使用embedding降级模式")

    args = parser.parse_args()

    if args.enhance_match:
        cmd_enhance_match(args)
    elif args.dry_run or args.__dict__.get("enhance_all"):
        cmd_enhance_all(args)
    else:
        cmd_status(args)


# ── 动态添加 subparsers 兼容 ──────────────────────────────────────────
# 支持 python offline_layer.py --status 和 python offline_layer.py status 两种风格
if "--status" in sys.argv or "-s" in sys.argv:
    sys.argv = [a for a in sys.argv if a not in ("--status", "-s")]
    sys.argv.insert(1, "--status")

if __name__ == "__main__":
    # 临时支持旧的调用风格
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        sys.argv[1] = "--status"
    elif len(sys.argv) > 1 and sys.argv[1] == "enhance-all":
        sys.argv[1] = "--enhance-all"
    elif len(sys.argv) > 1 and sys.argv[1] == "enhance-match":
        sys.argv[1] = "--enhance-match"
    main()

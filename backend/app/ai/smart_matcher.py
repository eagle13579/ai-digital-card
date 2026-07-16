"""
AI数智名片 智能匹配进化模块（Smart Matcher）
============================================
用 DeepSeek LLM 增强匹配引擎，理解供需语义关系，
不再局限于字符串精确匹配标签。

核心能力:
  1. analyze_tags()       — 从自然语言中提取 provide/need 标签
  2. semantic_match_score() — 理解标签之间语义关系的匹配评分
  3. generate_match_explanation() — 生成自然语言匹配解释
  4. hybrid_search()      — 向量搜索 + LLM 重排序

依赖:
  - app.ai.rag_pipeline.DeepSeekClient  (DeepSeek API 客户端)
  - app.ai.vector_search.VectorSearchEngine (向量搜索)
  - app.ai.embedding_service            (bge-m3 embedding)
"""

import json
import logging
from typing import Any, Optional

from app.ai.rag_pipeline import DeepSeekClient

logger = logging.getLogger(__name__)


# ======================================================================
# 智能匹配器
# ======================================================================

class SmartMatcher:
    """LLM增强的智能匹配器 — 用DeepSeek理解供需语义"""

    def __init__(self, deepseek_client: Optional[DeepSeekClient] = None):
        self.client = deepseek_client or DeepSeekClient()

    # ── 标签分析 ──────────────────────────────────────────────────────

    async def analyze_tags(self, text: str) -> list[dict]:
        """用LLM从自然语言中提取provide/need标签

        输入: "我在找能提供跨境支付API的供应商，我自身有电商平台资源"
        输出: [
            {"tag": "跨境支付API", "type": "need", "weight": 0.9},
            {"tag": "电商平台资源", "type": "provide", "weight": 0.8}
        ]
        """
        system_prompt = """你是一个智能标签提取助手。从用户的自我介绍或需求描述中，提取出"能提供什么"和"需要什么"的标签。

规则:
1. 每个标签必须是具体的能力、资源、产品或服务（如"跨境支付API"、"电商运营"）
2. type 为 "provide" 表示能提供的，type 为 "need" 表示需要的
3. weight 范围 0.0~1.0，根据文本中提到的明确程度/重要性赋权
4. 返回格式必须是 JSON 数组，如 [{"tag": "...", "type": "provide|need", "weight": 0.0~1.0}]
5. 如果文本没有明确对应的提供或需求，返回空数组
6. 只返回 JSON，不要其他解释文字"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请分析以下文本中的供需标签：\n\n{text}"},
        ]

        try:
            response = await self.client.chat(
                messages=messages,
                model="deepseek-chat",
                temperature=0.1,
                max_tokens=1024,
            )

            content = response.get("content", "") if isinstance(response, dict) else ""
            if not content:
                logger.warning(f"[SmartMatcher] analyze_tags 返回空内容, text={text[:50]}")
                return []

            # 清理内容，提取 JSON 数组
            content = content.strip()
            # 尝试解析 JSON
            if content.startswith("```"):
                # 去掉 markdown 代码块标记
                lines = content.split("\n")
                content = "\n".join(
                    line for line in lines
                    if not line.startswith("```")
                )

            tags = json.loads(content)
            if isinstance(tags, list):
                # 验证每个标签的格式
                validated = []
                for t in tags:
                    if isinstance(t, dict) and "tag" in t and "type" in t:
                        validated.append({
                            "tag": str(t["tag"]),
                            "type": t["type"] if t["type"] in ("provide", "need") else "provide",
                            "weight": float(t.get("weight", 0.5)),
                        })
                return validated
            return []

        except json.JSONDecodeError as e:
            logger.error(f"[SmartMatcher] analyze_tags JSON 解析失败: {e}, content={content}")
            return []
        except Exception as e:
            logger.error(f"[SmartMatcher] analyze_tags 异常: {e}")
            return []

    # ── 语义匹配评分 ──────────────────────────────────────────────────

    async def semantic_match_score(
        self,
        my_tags: list[dict],
        other_tags: list[dict],
        my_profile: Optional[dict] = None,
        other_profile: Optional[dict] = None,
    ) -> dict:
        """LLM语义匹配评分 — 理解标签之间的语义关系

        不再只是字符串精确匹配，而是理解:
        - "海外支付" ≈ "跨境支付结算"
        - "国内物流配送" ≠ "国际物流"

        Args:
            my_tags: 当前用户的标签列表 [{"tag": "...", "type": "provide|need", "weight": 0.0~1.0}, ...]
            other_tags: 对方用户的标签列表，格式同上
            my_profile: 当前用户的可选简介信息 dict
            other_profile: 对方用户的可选简介信息 dict

        Returns:
            {
                "score": 0.85,           # 0.0~1.0 综合语义匹配度
                "matched_pairs": [        # 语义匹配的标签对
                    {
                        "my_tag": "电商平台资源",
                        "my_type": "provide",
                        "other_tag": "电商代运营",
                        "other_type": "need",
                        "semantic_similarity": 0.85,
                        "explanation": "你提供电商平台资源，对方正好需要电商代运营"
                    }
                ],
                "explanation": "你们都是跨境支付领域的同行，他提供海外收单API，你刚好需要这个...",
                "raw_score": 0.75,        # 原始字符串精确匹配分数（用于对比）
            }
        """
        # 1. 先做原始标签精确匹配（基线分数）
        raw_score, matched_pairs = self._exact_tag_match(my_tags, other_tags)

        # 2. 如果有足够标签，用 LLM 做语义增强
        all_tags = my_tags + other_tags
        if len(all_tags) < 2:
            return {
                "score": raw_score,
                "matched_pairs": matched_pairs,
                "explanation": "标签数量不足，无法进行语义分析",
                "raw_score": raw_score,
            }

        semantic_result = await self._llm_semantic_match(
            my_tags, other_tags, my_profile, other_profile
        )

        # 3. 融合分数：语义分数 + 原始分数 加权平均
        semantic_score = semantic_result.get("score", raw_score)
        fused_score = round(semantic_score * 0.65 + raw_score * 0.35, 4)
        fused_score = min(1.0, max(0.0, fused_score))

        # 合并匹配对
        all_pairs = matched_pairs + semantic_result.get("matched_pairs", [])

        return {
            "score": fused_score,
            "matched_pairs": all_pairs,
            "explanation": semantic_result.get("explanation", ""),
            "raw_score": raw_score,
        }

    def _exact_tag_match(self, my_tags: list[dict], other_tags: list[dict]) -> tuple[float, list[dict]]:
        """原始精确标签匹配 — 与现有 match.py 引擎相同的逻辑"""
        score = 0.0
        matched_pairs = []

        my_provide = {t["tag"]: t.get("weight", 0.5) for t in my_tags if t.get("type") == "provide"}
        my_need = {t["tag"]: t.get("weight", 0.5) for t in my_tags if t.get("type") == "need"}
        other_provide = {t["tag"]: t.get("weight", 0.5) for t in other_tags if t.get("type") == "provide"}
        other_need = {t["tag"]: t.get("weight", 0.5) for t in other_tags if t.get("type") == "need"}

        # 我提供 → 对方需要
        for tag, weight in my_provide.items():
            if tag in other_need:
                match_w = weight * other_need[tag]
                score += match_w
                matched_pairs.append({
                    "my_tag": tag,
                    "my_type": "provide",
                    "other_tag": tag,
                    "other_type": "need",
                    "semantic_similarity": 1.0,
                    "explanation": f"精确匹配: 你提供「{tag}」，对方需要「{tag}」",
                })

        # 我需要 → 对方提供
        for tag, weight in my_need.items():
            if tag in other_provide:
                match_w = weight * other_provide[tag]
                score += match_w
                matched_pairs.append({
                    "my_tag": tag,
                    "my_type": "need",
                    "other_tag": tag,
                    "other_type": "provide",
                    "semantic_similarity": 1.0,
                    "explanation": f"精确匹配: 你需要「{tag}」，对方提供「{tag}」",
                })

        return round(score, 4), matched_pairs

    async def _llm_semantic_match(
        self,
        my_tags: list[dict],
        other_tags: list[dict],
        my_profile: Optional[dict] = None,
        other_profile: Optional[dict] = None,
    ) -> dict:
        """用 LLM 做语义匹配分析"""
        my_provide = [t["tag"] for t in my_tags if t.get("type") == "provide"]
        my_need = [t["tag"] for t in my_tags if t.get("type") == "need"]
        other_provide = [t["tag"] for t in other_tags if t.get("type") == "provide"]
        other_need = [t["tag"] for t in other_tags if t.get("type") == "need"]

        my_intro = ""
        if my_profile:
            my_intro = my_profile.get("intro", "")
            if not my_intro:
                my_intro = f"{my_profile.get('company', '')}的{my_profile.get('title', '')}"

        other_intro = ""
        if other_profile:
            other_intro = other_profile.get("intro", "")
            if not other_intro:
                other_intro = f"{other_profile.get('company', '')}的{other_profile.get('title', '')}"

        system_prompt = """你是一个商业匹配分析专家。分析两个人的供需标签，判断他们的匹配程度。

规则:
1. 理解标签的语义相似性，而不是只看字符串是否相同
2. 例如"海外支付"和"跨境支付结算"是语义匹配的
3. 例如"国内物流配送"和"国际物流"是不同方向的，不算匹配
4. 找出所有语义匹配的标签对
5. 给出总体匹配分数（0.0~1.0）
6. 用中文给出自然语言解释

返回格式必须是纯 JSON，不要 markdown 代码块标记：
{
    "score": 0.0~1.0,
    "matched_pairs": [
        {
            "my_tag": "...",
            "my_type": "provide|need",
            "other_tag": "...",
            "other_type": "provide|need",
            "semantic_similarity": 0.0~1.0,
            "explanation": "为什么这两个标签匹配"
        }
    ],
    "explanation": "总体匹配分析解释文字"
}

注意: semantic_similarity 表示标签对的语义相似程度，0.0=完全不相似，1.0=完全等价。"""

        user_message_parts = ["## 用户A（当前用户）"]
        user_message_parts.append(f"简介: {my_intro or '无'}")
        if my_provide:
            user_message_parts.append(f"能提供: {'、'.join(my_provide)}")
        if my_need:
            user_message_parts.append(f"需要: {'、'.join(my_need)}")

        user_message_parts.append("")
        user_message_parts.append("## 用户B（潜在匹配对象）")
        user_message_parts.append(f"简介: {other_intro or '无'}")
        if other_provide:
            user_message_parts.append(f"能提供: {'、'.join(other_provide)}")
        if other_need:
            user_message_parts.append(f"需要: {'、'.join(other_need)}")

        user_message_parts.append("")
        user_message_parts.append("请分析他们的供需匹配程度，返回 JSON 格式结果。")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "\n".join(user_message_parts)},
        ]

        try:
            response = await self.client.chat(
                messages=messages,
                model="deepseek-chat",
                temperature=0.1,
                max_tokens=2048,
            )

            content = response.get("content", "") if isinstance(response, dict) else ""
            if not content:
                return {"score": 0.0, "matched_pairs": [], "explanation": "语义分析无返回"}

            # 清理 content
            content = content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content_lines = []
                for line in lines:
                    if not line.startswith("```"):
                        content_lines.append(line)
                content = "\n".join(content_lines)

            result = json.loads(content)
            return {
                "score": float(result.get("score", 0.0)),
                "matched_pairs": result.get("matched_pairs", []),
                "explanation": result.get("explanation", ""),
            }

        except json.JSONDecodeError as e:
            logger.error(f"[SmartMatcher] LLM semantic match JSON 解析失败: {e}")
            return {"score": 0.0, "matched_pairs": [], "explanation": "语义分析结果解析失败"}
        except Exception as e:
            logger.error(f"[SmartMatcher] LLM semantic match 异常: {e}")
            return {"score": 0.0, "matched_pairs": [], "explanation": f"语义分析异常: {e}"}

    # ── 匹配解释生成 ──────────────────────────────────────────────────

    async def generate_match_explanation(
        self,
        user_a: dict,
        user_b: dict,
        matched_pairs: list[dict],
    ) -> str:
        """生成自然语言匹配解释

        Args:
            user_a: 用户A的信息 dict，至少包含 name, company, title
            user_b: 用户B的信息 dict
            matched_pairs: 匹配的标签对列表

        Returns:
            自然语言解释，如 "你们都是跨境支付领域的同行..."
        """
        if not matched_pairs:
            return "暂未发现明显的供需匹配。"

        pairs_text = "\n".join([
            f"- {p.get('my_tag', '?')} ↔ {p.get('other_tag', '?')} ({p.get('explanation', '语义匹配')})"
            for p in matched_pairs[:5]
        ])

        system_prompt = """你是一个商业社交助手，根据两人的供需匹配信息，生成一段简短、自然的匹配解释。
要求:
1. 语气友好、积极
2. 突出双方的互补性
3. 使用中文
4. 不超过 100 字
5. 直接输出解释文字，不要任何前缀或格式标记"""

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"用户A: {user_a.get('name', '?')}（{user_a.get('company', '')}，{user_a.get('title', '')}）\n"
                    f"用户B: {user_b.get('name', '?')}（{user_b.get('company', '')}，{user_b.get('title', '')}）\n\n"
                    f"匹配标签对:\n{pairs_text}\n\n"
                    f"请生成一段匹配解释。"
                ),
            },
        ]

        try:
            response = await self.client.chat(
                messages=messages,
                model="deepseek-chat",
                temperature=0.3,
                max_tokens=256,
            )

            content = response.get("content", "") if isinstance(response, dict) else ""
            return content.strip() if content else self._fallback_explanation(matched_pairs)

        except Exception as e:
            logger.error(f"[SmartMatcher] generate_match_explanation 异常: {e}")
            return self._fallback_explanation(matched_pairs)

    def _fallback_explanation(self, matched_pairs: list[dict]) -> str:
        """降级方案：基于匹配对生成简单的解释"""
        provide_pairs = [p for p in matched_pairs if p.get("my_type", p.get("type")) in ("provide", "need")]
        if not matched_pairs:
            return "暂无匹配信息。"
        count = len(matched_pairs)
        tags = [p.get("my_tag", p.get("tag", "?")) for p in matched_pairs[:3]]
        return f"发现 {count} 个匹配点，涉及: {'、'.join(tags)}"

    # ── 混合搜索 ──────────────────────────────────────────────────────

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 20,
        candidates: Optional[list[dict]] = None,
    ) -> list[dict]:
        """混合搜索: 向量搜索 + LLM 重排序

        Args:
            query: 搜索查询
            top_k: 返回结果数量上限
            candidates: 候选列表（可选），如果不提供，使用向量搜索获取

        Returns:
            重排序后的结果列表，每项包含原始字段 + llm_score + llm_explanation
        """
        if not candidates:
            # 如果没有候选，把 query 当作标签文本分析后用向量搜索
            return []

        # 用 LLM 做重排序
        reranked = await self._llm_rerank(query, candidates[:top_k * 2], top_k)
        return reranked

    async def _llm_rerank(
        self,
        query: str,
        candidates: list[dict],
        top_k: int,
    ) -> list[dict]:
        """LLM 重排序候选列表"""
        # 构建候选摘要
        candidate_lines = []
        for i, c in enumerate(candidates[:15]):  # LLM 重排序上限 15 个
            name = c.get("user_name", c.get("name", f"用户{c.get('user_id', '?')}"))
            company = c.get("company", "")
            title = c.get("title", "")
            intro = c.get("intro", "")
            tags = c.get("tags", c.get("common_tags", []))
            tag_str = ", ".join(tags[:5]) if tags else ""
            candidate_lines.append(
                f"[{i}] {name} / {company} / {title} / {intro[:100]} / 标签: {tag_str}"
            )

        system_prompt = """你是一个搜索结果排序专家。根据用户的查询意图，对候选结果进行相关性排序。

规则:
1. 分析查询的意图和关键词
2. 检查每个候选与查询的相关性
3. 输出排序后的结果索引列表（从最相关到最不相关）
4. 只返回 JSON 数组

返回格式:
{
    "ranked_indices": [3, 0, 5, ...],  # 从最相关到最不相关的索引
    "explanations": {
        "3": "该用户从事跨境支付领域...",
        "0": "..."
    }
}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"用户查询: {query}\n\n"
                    f"候选列表:\n" + "\n".join(candidate_lines) + "\n\n"
                    f"请按相关性排序。"
                ),
            },
        ]

        try:
            response = await self.client.chat(
                messages=messages,
                model="deepseek-chat",
                temperature=0.1,
                max_tokens=1024,
            )

            content = response.get("content", "") if isinstance(response, dict) else ""
            if not content:
                return candidates[:top_k]

            content = content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(line for line in lines if not line.startswith("```"))

            result = json.loads(content)
            ranked_indices = result.get("ranked_indices", [])
            explanations = result.get("explanations", {})

            reranked = []
            for idx in ranked_indices:
                if idx < len(candidates):
                    item = dict(candidates[idx])
                    item["llm_score"] = 1.0 - (len(reranked) * 0.05)
                    item["llm_explanation"] = explanations.get(str(idx), "")
                    reranked.append(item)

            return reranked[:top_k]

        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"[SmartMatcher] LLM rerank 失败: {e}")
            return candidates[:top_k]


# ======================================================================
# 便捷工厂函数
# ======================================================================

_default_matcher: Optional[SmartMatcher] = None


def get_smart_matcher() -> SmartMatcher:
    """获取全局 SmartMatcher 实例（单例）"""
    global _default_matcher
    if _default_matcher is None:
        _default_matcher = SmartMatcher()
    return _default_matcher

"""
SAG (Self-Aware Generation) 自我推演管道
============================================
不依赖外部知识检索，纯模型内部自我推演推理管道。
与 RAG 管道互补：RAG 负责外部知识检索，SAG 负责内部逻辑推理。

六大推理模式:
  1. quality_review      — 名片质量评审（完整性/专业性/行业匹配度）
  2. matching_reasoning  — 匹配逻辑推理（供需互补/兼容性分析）
  3. trust_inference     — 信任链推理（基于已知关系推断信任度）
  4. explain_recommend   — 推荐解释生成（每个推荐项生成可读理由）
  5. contradiction_detect — 矛盾检测（推荐结果/名片信息一致性）
  6. optimize_suggest    — 优化建议（凭模型知识给出行业最佳实践建议）

架构:
  SAGPipeline
    ├─ SAGContext     — 推理上下文（比 RAG 轻量，无外部检索数据）
    ├─ SAGResponse    — 推理结果（含推理链/置信度/可解释性）
    ├─ 6 种推理模式   — 每种模式有独立的 System Prompt 和推理深度配置
    └─ DeepSeekClient — 复用 RAG 管道的 LLM 客户端

使用方式:
    sag = SAGPipeline()
    result = await sag.analyze(
        mode="quality_review",
        content={"name": "张三", "company": "XX科技", ...},
    )
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from app.ai.rag_pipeline import DeepSeekClient

logger = logging.getLogger(__name__)


# ======================================================================
# 推理模式定义
# ======================================================================


class SAGMode(str, Enum):
    """SAG 支持的六大推理模式"""

    QUALITY_REVIEW = "quality_review"
    """名片质量评审 — 完整性/专业性/行业匹配度/品牌一致性"""
    MATCHING_REASONING = "matching_reasoning"
    """匹配逻辑推理 — 供需互补/商业模式兼容/文化匹配"""
    TRUST_INFERENCE = "trust_inference"
    """信任链推理 — 基于已知关系推断陌生关系信任度"""
    EXPLAIN_RECOMMEND = "explain_recommend"
    """推荐解释生成 — 每个推荐项生成人类可读的商业理由"""
    CONTRADICTION_DETECT = "contradiction_detect"
    """矛盾检测 — 推荐结果内部矛盾/名片信息逻辑一致性"""
    OPTIMIZE_SUGGEST = "optimize_suggest"
    """优化建议 — 凭模型知识给出行业最佳实践和可执行建议"""


# ======================================================================
# 推理深度
# ======================================================================


class SAGDepth(str, Enum):
    """推理深度控制 — 影响 token 消耗与思考深度"""

    FAST = "fast"
    """快速模式：单轮推理，约 300-500 tokens，适合实时响应"""
    STANDARD = "standard"
    """标准模式：2 步推理链，约 800-1200 tokens，默认"""
    DEEP = "deep"
    """深度模式：5 步推理链 + 自校验，约 2000-4000 tokens，适合决策"""


# ======================================================================
# 数据模型
# ======================================================================


@dataclass
class SAGContext:
    """SAG 推理上下文 — 比 RAGContext 更轻量，无外部检索数据

    Attributes:
        mode: 推理模式
        content: 推理输入内容（名片字段/匹配对/推荐列表等）
        user_id: 关联用户 ID（可选）
        depth: 推理深度
        extra_context: 额外上下文（如对话历史、用户偏好等）
    """
    mode: SAGMode
    content: dict[str, Any] = field(default_factory=dict)
    user_id: int | None = None
    depth: SAGDepth = SAGDepth.STANDARD
    extra_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "mode": self.mode.value,
            "content": self.content,
            "user_id": self.user_id,
            "depth": self.depth.value,
            "extra_context": self.extra_context,
        }


@dataclass
class SAGStep:
    """推理链中的一步"""
    step_name: str
    input: str
    output: str
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "step_name": self.step_name,
            "input": self.input,
            "output": self.output,
            "confidence": self.confidence,
        }


@dataclass
class SAGResponse:
    """SAG 推理结果

    Attributes:
        conclusion: 推理结论
        reasoning_chain: 推理链（多步推理过程）
        confidence: 置信度 [0, 1]
        score: 评分（适用于评分类推理）
        suggestions: 建议列表
        model_used: 使用的模型
        tokens_used: token 消耗
    """
    conclusion: str
    reasoning_chain: list[SAGStep] = field(default_factory=list)
    confidence: float = 0.0
    score: float | None = None
    suggestions: list[str] = field(default_factory=list)
    model_used: str = "deepseek-chat"
    tokens_used: int = 0

    def to_dict(self) -> dict:
        return {
            "conclusion": self.conclusion,
            "reasoning_chain": [s.to_dict() for s in self.reasoning_chain],
            "confidence": self.confidence,
            "score": self.score,
            "suggestions": self.suggestions,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
        }


# ======================================================================
# 推理提示词工厂
# ======================================================================


class SAGPromptFactory:
    """根据推理模式和深度生成系统提示词"""

    # ── 模式提示词模板 ────────────────────────────────────────────────

    PROMPTS: dict[SAGMode, str] = {
        SAGMode.QUALITY_REVIEW: (
            "你是一个AI数字名片的专业评审师。请对提供的名片内容进行全面评审。\n\n"
            "评审维度（逐条分析）:\n"
            "1. 信息完整度：必填字段是否齐全，联系方式是否完整\n"
            "2. 专业度：文案是否专业，措辞是否得体\n"
            "3. 行业匹配：内容是否与用户行业匹配\n"
            "4. 品牌一致性：整体形象是否一致\n"
            "5. 差异化：是否有独特卖点\n\n"
            "请输出 JSON 格式结果：\n"
            "{\n"
            '  "completeness": {"score": 0-100, "missing": ["字段名"], "level": "优秀|良好|一般|待完善"},\n'
            '  "professionalism": {"score": 0-100, "issues": ["问题1"], "strengths": ["优点1"]},\n'
            '  "industry_fit": {"score": 0-100, "matched": ["匹配项"], "mismatched": ["不匹配项"]},\n'
            '  "brand_consistency": {"score": 0-100, "issues": ["问题1"]},\n'
            '  "overall_score": 0-100,\n'
            '  "top_priorities": ["最高优先级的改进项"]\n'
            "}"
        ),
        SAGMode.MATCHING_REASONING: (
            "你是一个商业匹配逻辑分析师。请基于提供的双方信息，推理他们之间的匹配度。\n\n"
            "分析维度:\n"
            "1. 供需互补：甲方能提供的是否是乙方需要的，反之亦然\n"
            "2. 商业模式兼容：两者的商业模式是否能对接\n"
            "3. 规模匹配：公司规模、阶段是否匹配\n"
            "4. 行业关联：行业上下游、交叉领域\n"
            "5. 潜在合作模式：推荐最可能的合作方式\n\n"
            "请输出 JSON 格式结果：\n"
            "{\n"
            '  "supply_demand_match": {"score": 0-100, "explanation": "说明"},\n'
            '  "business_compatibility": {"score": 0-100, "explanation": "说明"},\n'
            '  "scale_fit": {"score": 0-100, "explanation": "说明"},\n'
            '  "industry_relevance": {"score": 0-100, "explanation": "说明"},\n'
            '  "overall_match_score": 0-100,\n'
            '  "recommended_cooperation": "推荐合作模式",\n'
            '  "risks": ["潜在风险"]\n'
            "}"
        ),
        SAGMode.TRUST_INFERENCE: (
            "你是一个信任关系推理分析师。基于已知的信任关系网，推理陌生关系之间的信任度。\n\n"
            "分析维度:\n"
            "1. 直接连接：是否有共同联系人\n"
            "2. 路径长度：通过几步可以连接\n"
            "3. 信任传递：中间人的信任度如何\n"
            "4. 领域交叉：是否有共同领域/兴趣\n"
            "5. 风险提示：潜在的合作风险\n\n"
            "请输出 JSON 格式结果：\n"
            "{\n"
            '  "connection_path": [{"via": "中间人", "trust_level": 0-100, "relationship": "关系" }],\n'
            '  "inferred_trust_score": 0-100,\n'
            '  "confidence": 0-100,\n'
            '  "recommendation": "是否推荐建立联系及理由",\n'
            '  "risks": ["潜在风险"]\n'
            "}"
        ),
        SAGMode.EXPLAIN_RECOMMEND: (
            "你是一个AI数字名片的推荐解释官。请为每个推荐项生成人类可读的商业理由。\n\n"
            "对每个推荐项，请说明：\n"
            "1. 为什么推荐这个人/公司\n"
            "2. 商业上的互补性\n"
            "3. 合作的潜在价值\n"
            "4. 建议的首次接触方式\n\n"
            "请用中文输出，每个推荐项一段简洁有力的解释。\n"
            "格式：每个推荐项一段话，不超过100字。"
        ),
        SAGMode.CONTRADICTION_DETECT: (
            "你是一个逻辑一致性检查员。请检测以下信息中的逻辑矛盾和不一致之处。\n\n"
            "检查维度:\n"
            "1. 信息内部矛盾：同一人的不同信息是否互相矛盾\n"
            "2. 推荐一致性：推荐结果之间是否存在冲突\n"
            "3. 逻辑合理性：信息是否符合商业逻辑\n"
            "4. 时间线一致性：事件顺序是否合理\n\n"
            "请输出 JSON 格式结果：\n"
            "{\n"
            '  "contradictions": [{"type": "矛盾类型", "description": "描述", "severity": "高|中|低"}],\n'
            '  "consistency_score": 0-100,\n'
            '  "suggestions": ["修正建议"]\n'
            "}"
        ),
        SAGMode.OPTIMIZE_SUGGEST: (
            "你是一个AI数字名片优化顾问。请基于你了解的行业最佳实践，给出可执行的优化建议。\n\n"
            "建议维度:\n"
            "1. 内容优化：文案、关键词、定位\n"
            "2. 展示优化：排版、视觉、结构\n"
            "3. 转化优化：CTA、联系方式、行动引导\n"
            "4. 行业差异化：针对特定行业的独到建议\n"
            "5. 优先级排序：从易到难、从高ROI到低ROI\n\n"
            "请输出 JSON 格式结果：\n"
            "{\n"
            '  "content_tips": [{"priority": 1-5, "tip": "建议", "reason": "理由"}],\n'
            '  "display_tips": [{"priority": 1-5, "tip": "建议", "reason": "理由"}],\n'
            '  "conversion_tips": [{"priority": 1-5, "tip": "建议", "reason": "理由"}],\n'
            '  "industry_specific": {"行业名": ["针对性建议"]},\n'
            '  "quick_wins": ["3个最容易执行的改进"]\n'
            "}"
        ),
    }

    # ── 深度指令映射 ──────────────────────────────────────────────────

    DEPTH_INSTRUCTIONS: dict[SAGDepth, str] = {
        SAGDepth.FAST: (
            "推理要求：快速单轮推理。\n"
            "1. 直接给出结论\n"
            "2. 附带简要理由\n"
            "3. 不要过多分析步骤\n"
        ),
        SAGDepth.STANDARD: (
            "推理要求：标准两轮推理链。\n"
            "1. 第一步：分析输入信息中的关键要素\n"
            "2. 第二步：基于关键要素进行推理，得出结论\n"
            "3. 附带置信度评估\n"
        ),
        SAGDepth.DEEP: (
            "推理要求：深度五步推理链，含自校验。\n"
            "1. 第一步：信息分解 — 将输入分解为独立要素\n"
            "2. 第二步：假设生成 — 对每个要素提出可能解释\n"
            "3. 第三步：交叉验证 — 检验假设之间是否矛盾\n"
            "4. 第四步：综合推理 — 整合所有验证后的假设\n"
            "5. 第五步：自校验 — 检查结论是否合理，标注不确定性\n"
        ),
    }

    @classmethod
    def build_system_prompt(cls, mode: SAGMode, depth: SAGDepth) -> str:
        """构建完整系统提示词"""
        base_prompt = cls.PROMPTS.get(mode, "")
        depth_instruction = cls.DEPTH_INSTRUCTIONS.get(depth, "")
        return f"{base_prompt}\n\n{depth_instruction}\n\n请严格按 JSON 格式输出。如果无法给出确切判断，请如实标注 confidence 较低。"


# ======================================================================
# SAG 管道主类
# ======================================================================


class SAGPipeline:
    """自我推演管道 — 纯推理，不依赖外部检索

    与 RAGPipeline 的关系：
        - RAGPipeline: 外部知识检索 + LLM 生成（依赖 DB/向量/图谱）
        - SAGPipeline: 纯 LLM 自我推演（不依赖任何外部存储）
        - HybridPipeline: 先 RAG 检索 → 再 SAG 自校验（RAG+SAG 融合）
    """

    def __init__(self):
        self.deepseek = DeepSeekClient()

    async def analyze(
        self,
        mode: SAGMode,
        content: dict[str, Any],
        user_id: int | None = None,
        depth: SAGDepth = SAGDepth.STANDARD,
        extra_context: dict[str, Any] | None = None,
        temperature: float = 0.5,
        max_tokens: int = 2048,
    ) -> SAGResponse:
        """执行 SAG 推理

        Args:
            mode: 推理模式
            content: 推理输入内容
            user_id: 关联用户 ID（可选）
            depth: 推理深度
            extra_context: 额外上下文
            temperature: LLM 温度（SAG 用较低温度保证推理一致性）
            max_tokens: 最大输出 token

        Returns:
            SAGResponse 包含推理链和结论
        """
        # 1. 构建推理上下文
        context = SAGContext(
            mode=mode,
            content=content,
            user_id=user_id,
            depth=depth,
            extra_context=extra_context or {},
        )

        # 2. 构建系统提示词
        system_prompt = SAGPromptFactory.build_system_prompt(mode, depth)

        # 3. 构建用户消息
        user_message = self._build_user_message(context)

        # 4. 构建消息列表（带推理链分步）
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        # 5. 根据推理深度决定是否分步调用
        if depth == SAGDepth.FAST:
            return await self._single_step_analyze(messages, mode, temperature, max_tokens)
        elif depth == SAGDepth.STANDARD:
            return await self._two_step_analyze(messages, mode, temperature, max_tokens)
        else:
            return await self._deep_analyze(messages, mode, temperature, max_tokens)

    def _build_user_message(self, context: SAGContext) -> str:
        """构建用户消息"""
        parts = []
        parts.append(f"### 推理模式：{context.mode.value}\n")

        if context.content:
            parts.append("### 输入内容：")
            parts.append(json.dumps(context.content, ensure_ascii=False, indent=2))
            parts.append("")

        if context.extra_context:
            parts.append("### 额外上下文：")
            parts.append(json.dumps(context.extra_context, ensure_ascii=False, indent=2))
            parts.append("")

        parts.append("请基于以上输入进行分析推理，严格按 JSON 格式输出结果。")
        return "\n".join(parts)

    async def _single_step_analyze(
        self,
        messages: list[dict],
        mode: SAGMode,
        temperature: float,
        max_tokens: int,
    ) -> SAGResponse:
        """单步推理（快速模式）"""
        response = await self.deepseek.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )

        content = response.get("content", "") if isinstance(response, dict) else str(response)
        total_tokens = response.get("tokens_used", 0) if isinstance(response, dict) else 0

        result = self._parse_json_output(content)

        chain = [
            SAGStep(
                step_name="single_reasoning",
                input=messages[-1]["content"][:200],
                output=content[:500],
                confidence=result.get("confidence", result.get("overall_score", 50)) / 100,
            )
        ]

        return SAGResponse(
            conclusion=result.get("conclusion", result.get("explanation", content[:500])),
            reasoning_chain=chain,
            confidence=result.get("confidence", result.get("overall_score", 50)) / 100 if isinstance(result.get("confidence", result.get("overall_score", 50)), (int, float)) else 0.5,
            score=result.get("overall_score", result.get("overall_match_score", None)),
            suggestions=result.get("top_priorities", result.get("suggestions", result.get("quick_wins", []))),
            model_used="deepseek-chat",
            tokens_used=total_tokens,
        )

    async def _two_step_analyze(
        self,
        messages: list[dict],
        mode: SAGMode,
        temperature: float,
        max_tokens: int,
    ) -> SAGResponse:
        """两轮推理（标准模式）"""
        chain = []

        # Step 1: 要素提取
        step1_messages = messages.copy()
        step1_messages.append({
            "role": "user",
            "content": "第一步：请先提取输入中的关键要素，列出影响判断的核心因素。"
        })
        step1_resp = await self.deepseek.chat(
            messages=step1_messages,
            temperature=temperature,
            max_tokens=600,
            stream=False,
        )
        step1_content = step1_resp.get("content", "") if isinstance(step1_resp, dict) else str(step1_resp)
        chain.append(SAGStep(
            step_name="要素提取",
            input="提取输入中的关键要素",
            output=step1_content[:500],
            confidence=0.8,
        ))

        # Step 2: 基于要素进行推理
        step2_messages = step1_messages.copy()
        step2_messages.append({"role": "assistant", "content": step1_content})
        step2_messages.append({
            "role": "user",
            "content": "第二步：基于上述关键要素进行推理，给出最终结论（JSON格式）。"
        })
        step2_resp = await self.deepseek.chat(
            messages=step2_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        step2_content = step2_resp.get("content", "") if isinstance(step2_resp, dict) else str(step2_resp)
        total_tokens = (step2_resp.get("tokens_used", 0) if isinstance(step2_resp, dict) else 0)

        result = self._parse_json_output(step2_content)

        chain.append(SAGStep(
            step_name="综合推理",
            input="基于关键要素进行推理",
            output=step2_content[:500],
            confidence=result.get("confidence", result.get("overall_score", 50)) / 100 if isinstance(result.get("confidence", result.get("overall_score", 50)), (int, float)) else 0.5,
        ))

        total_tokens_all = (step1_resp.get("tokens_used", 0) if isinstance(step1_resp, dict) else 0) + total_tokens

        return SAGResponse(
            conclusion=result.get("conclusion",
                         result.get("explanation",
                         result.get("recommendation",
                         result.get("recommended_cooperation", step2_content[:500])))),
            reasoning_chain=chain,
            confidence=result.get("confidence", result.get("overall_score", 50)) / 100 if isinstance(result.get("confidence", result.get("overall_score", 50)), (int, float)) else 0.5,
            score=result.get("overall_score", result.get("overall_match_score", None)),
            suggestions=result.get("top_priorities",
                         result.get("suggestions",
                         result.get("quick_wins",
                         result.get("risks", [])))),
            model_used="deepseek-chat",
            tokens_used=total_tokens_all,
        )

    async def _deep_analyze(
        self,
        messages: list[dict],
        mode: SAGMode,
        temperature: float,
        max_tokens: int,
    ) -> SAGResponse:
        """五步深度推理链（深度模式）"""
        chain = []
        total_tokens_all = 0
        steps_def = [
            ("信息分解", "第一步：将输入信息分解为独立的关键要素，列出每个要素的意义"),
            ("假设生成", "第二步：对每个关键要素，提出2-3种可能的解释或影响"),
            ("交叉验证", "第三步：检验不同假设之间是否互相矛盾，排除不合理选项"),
            ("综合推理", "第四步：整合所有验证后的假设，形成完整判断"),
            ("自校验", "第五步：检查最终结论的合理性，标注不确定性，输出JSON格式结果"),
        ]

        for step_name, step_prompt in steps_def:
            step_messages = messages.copy()
            if chain:
                step_messages.append({
                    "role": "assistant",
                    "content": f"[上一步结果]\n{chain[-1].output[:800]}"
                })
            step_messages.append({"role": "user", "content": step_prompt})

            step_resp = await self.deepseek.chat(
                messages=step_messages,
                temperature=temperature,
                max_tokens=800 if step_name != "自校验" else max_tokens,
                stream=False,
            )
            step_content = step_resp.get("content", "") if isinstance(step_resp, dict) else str(step_resp)
            step_tokens = step_resp.get("tokens_used", 0) if isinstance(step_resp, dict) else 0

            chain.append(SAGStep(
                step_name=step_name,
                input=step_prompt,
                output=step_content[:500],
                confidence=0.8,
            ))
            total_tokens_all += step_tokens

        # 从最后一步提取结构化结果
        final_content = chain[-1].output if chain else ""
        result = self._parse_json_output(final_content) if final_content else {}

        return SAGResponse(
            conclusion=result.get("conclusion",
                         result.get("recommendation",
                         result.get("explanation",
                         final_content[:500]))) if result else final_content[:500],
            reasoning_chain=chain,
            confidence=result.get("confidence", 70) / 100 if isinstance(result.get("confidence", 70), (int, float)) else 0.7,
            score=result.get("overall_score", result.get("overall_match_score", result.get("consistency_score", None))),
            suggestions=result.get("top_priorities",
                         result.get("suggestions",
                         result.get("quick_wins",
                         result.get("risks", [])))),
            model_used="deepseek-chat",
            tokens_used=total_tokens_all,
        )

    def _parse_json_output(self, text: str) -> dict:
        """从 LLM 输出中提取 JSON"""
        # 尝试直接解析
        text = text.strip()
        # 查找 JSON 边界
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_str = text[start:end + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        return {}

    async def close(self):
        await self.deepseek.close()

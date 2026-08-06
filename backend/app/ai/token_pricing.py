"""
Token双重计费定价模型
=====================
区分 internal（自有模型/内容）和 external（第三方 LLM）两类调用，
按不同定价策略计算费用。

定价架构:
  - internal: 固定平台价（覆盖服务器折旧+电费+维护）
  - external: 第三方模型成本 × (1 + 加价率) + 平台费

使用方式:
    from app.ai.token_pricing import TokenPricing
    cost = TokenPricing.calculate_cost(
        model_type="external",
        model_name="deepseek-chat",
        prompt_tokens=800,
        completion_tokens=300,
    )
"""

from __future__ import annotations

from typing import Literal

# ── 汇率 ────────────────────────────────────────────────────
USD_TO_CNY: float = 7.25  # 美元→人民币汇率（可调）

# ==================================================================
# 内部模型定价（¥/1K tokens）— 覆盖服务器成本
# ==================================================================
# 这些是自有/自部署模型，不产生第三方 API 费用
INTERNAL_PRICING: dict[str, dict[str, float]] = {
    # 本地 embedding 模型
    "m3e": {
        "embedding": 0.001,  # M3E base 本地推理，仅电费
    },
    "numpy": {
        "embedding": 0.0005,  # 降级方案，零依赖
    },
    # 本地 MLX 推理服务（Mac mini 自建）
    "mlx": {
        "generation": 0.005,
        "embedding": 0.003,
    },
    # 知识图谱查询
    "knowledge_graph": {
        "query": 0.002,
    },
    # 规则引擎
    "rule_engine": {
        "rule": 0.001,
    },
    # 本地向量搜索（SQLite 索引）
    "vector_search": {
        "search": 0.002,
    },
    # sbert（本地 sentence-transformers 降级）
    "sentence_transformer": {
        "embedding": 0.001,
    },
}

# ==================================================================
# 外部模型成本价（USD/1K tokens）
# ==================================================================
# 来源: DeepSeek 官方定价 / OpenAI 官方定价
# 维护: 随第三方调价更新
EXTERNAL_PRICING_USD: dict[str, dict[str, float]] = {
    # DeepSeek 系列（USD/1K tokens）
    "deepseek-chat": {
        "input": 0.00027,
        "output": 0.00110,
    },
    "deepseek-reasoner": {
        "input": 0.00055,
        "output": 0.00219,
    },
    "deepseek-coder": {
        "input": 0.00014,
        "output": 0.00028,
    },
    "deepseek-vision": {
        "input": 0.00027,
        "output": 0.00110,
    },
    # Embedding 模型
    "text-embedding-3-small": {
        "input": 0.00002,
        "output": 0.0,
    },
    "text-embedding-3-large": {
        "input": 0.00013,
        "output": 0.0,
    },
    "deepseek-embedding": {
        "input": 0.00007,
        "output": 0.0,
    },
}

# ==================================================================
# 加价率配置
# ==================================================================
# external 默认加价率: 第三方成本 × (1 + markup_rate) = 用户售价
DEFAULT_EXTERNAL_MARKUP_RATE: float = 0.50  # 50%
# internal 默认加价率: 0（直接用平台定价）
DEFAULT_INTERNAL_MARKUP_RATE: float = 0.0

# 模型映射别名 → 标准名
MODEL_ALIASES: dict[str, str] = {
    "deepseek-chat": "deepseek-chat",
    "deepseek-reasoner": "deepseek-reasoner",
    "deepseek-coder": "deepseek-coder",
    "deepseek": "deepseek-chat",
    "gpt-4": "deepseek-chat",            # fallback 到 DeepSeek 成本
    "gpt-4o": "deepseek-chat",
    "claude-3-opus": "deepseek-reasoner",
    "claude-3-sonnet": "deepseek-chat",
    "text-embedding-3-small": "text-embedding-3-small",
    "text-embedding-3-large": "text-embedding-3-large",
    "text-embedding-ada-002": "text-embedding-3-small",
    "text-embedding-v2": "deepseek-embedding",
    "m3e": "m3e",
    "moka-ai/m3e-base": "m3e",
    "numpy": "numpy",
    "mlx": "mlx",
}


# ==================================================================
# 公共 API
# ==================================================================


def resolve_model_name(model_name: str) -> str:
    """解析模型别名到标准化名。"""
    return MODEL_ALIASES.get(model_name.strip().lower(), model_name)


def is_external_model(model_name: str) -> bool:
    """判断模型是否为外部（第三方 API）模型。"""
    key = resolve_model_name(model_name)
    return key in EXTERNAL_PRICING_USD


def get_internal_price(model_name: str, token_type: str = "embedding") -> float:
    """获取内部模型单价（¥/1K tokens）。

    如果未找到精确匹配，返回最低默认价。
    """
    key = resolve_model_name(model_name)
    pricing = INTERNAL_PRICING.get(key, {})
    return pricing.get(token_type, 0.001)  # default: ¥0.001/1K


def get_external_cost(
    model_name: str,
    token_type: Literal["input", "output"] = "input",
) -> float:
    """获取外部模型成本（¥/1K tokens）。

    自动将 USD 成本转换为 ¥。
    """
    key = resolve_model_name(model_name)
    pricing = EXTERNAL_PRICING_USD.get(key, {"input": 0.0, "output": 0.0})
    return pricing.get(token_type, 0.0) * USD_TO_CNY


def get_markup_rate(model_type: str) -> float:
    """获取加价率。"""
    if model_type == "external":
        return DEFAULT_EXTERNAL_MARKUP_RATE
    return DEFAULT_INTERNAL_MARKUP_RATE


def calculate_cost(
    model_type: str,
    model_name: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int | None = None,
) -> dict[str, float]:
    """计算 token 调用费用。

    Args:
        model_type: "internal" 或 "external"
        model_name: 模型名称（支持别名）
        prompt_tokens: 输入 token 数
        completion_tokens: 输出 token 数
        total_tokens: 总 token 数（如果提供，用于 internal 模型计算）

    Returns:
        {
            "token_cost": ¥,          # 用户售价
            "external_cost": ¥,       # 外部成本（仅 external 有效，internal=0）
            "markup_rate": float,     # 加价率
        }
    """
    markup_rate = get_markup_rate(model_type)
    token_count = total_tokens or (prompt_tokens + completion_tokens)

    if model_type == "internal":
        # 内部模型：固定平台定价
        unit_price = get_internal_price(model_name)
        token_cost = round(token_count / 1000.0 * unit_price, 6)
        return {
            "token_cost": token_cost,
            "external_cost": 0.0,
            "markup_rate": 0.0,
        }

    # 外部模型：成本 × (1 + 加价率)
    input_cost = get_external_cost(model_name, "input") * (prompt_tokens / 1000.0)
    output_cost = get_external_cost(model_name, "output") * (completion_tokens / 1000.0)
    external_cost = round(input_cost + output_cost, 6)

    # 售价 = 成本 × (1 + markup_rate)
    token_cost = round(external_cost * (1 + markup_rate), 6)

    return {
        "token_cost": token_cost,
        "external_cost": external_cost,
        "markup_rate": markup_rate,
    }


def classify_model(model_name: str) -> str:
    """判断模型为 internal 还是 external。

    Returns:
        "internal" | "external"
    """
    key = resolve_model_name(model_name)
    if key in EXTERNAL_PRICING_USD or key in (
        "deepseek-chat", "deepseek-reasoner", "deepseek-coder",
        "deepseek-vision", "text-embedding-3-small", "text-embedding-3-large",
        "deepseek-embedding",
    ):
        return "external"
    return "internal"

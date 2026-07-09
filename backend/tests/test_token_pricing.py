"""
测试：Token双重计费定价模型
=========================
覆盖 token_pricing.py 的核心逻辑：
- 内部模型固定价计算
- 外部模型成本×加价率计算
- 模型类型自动分类
- 别名解析
"""

from __future__ import annotations

import pytest

from app.ai.token_pricing import (
    INTERNAL_PRICING,
    EXTERNAL_PRICING_USD,
    calculate_cost,
    classify_model,
    resolve_model_name,
    is_external_model,
    get_internal_price,
    get_external_cost,
    get_markup_rate,
)


class TestResolveModelName:
    """模型别名解析"""

    def test_exact_match(self):
        assert resolve_model_name("deepseek-chat") == "deepseek-chat"

    def test_alias_match(self):
        assert resolve_model_name("gpt-4") == "deepseek-chat"
        assert resolve_model_name("deepseek") == "deepseek-chat"

    def test_case_insensitive(self):
        assert resolve_model_name("DeepSeek-Chat") == "deepseek-chat"

    def test_unknown(self):
        """未知模型保持原样返回"""
        assert resolve_model_name("unknown-model") == "unknown-model"


class TestIsExternalModel:
    """外部/内部模型分类"""

    def test_external_deepseek(self):
        assert is_external_model("deepseek-chat") is True

    def test_internal_local(self):
        assert is_external_model("m3e") is False
        assert is_external_model("mlx") is False
        assert is_external_model("knowledge_graph") is False

    def test_alias_resolution(self):
        """gpt-4 别名映射到 deepseek-chat → 判定为外部"""
        assert is_external_model("gpt-4") is True


class TestClassifyModel:
    """模型类型自动分类"""

    def test_external_models(self):
        assert classify_model("deepseek-chat") == "external"
        assert classify_model("deepseek-reasoner") == "external"
        assert classify_model("deepseek-coder") == "external"

    def test_internal_models(self):
        assert classify_model("m3e") == "internal"
        assert classify_model("mlx") == "internal"
        assert classify_model("knowledge_graph") == "internal"
        assert classify_model("rule_engine") == "internal"
        assert classify_model("vector_search") == "internal"

    def test_unknown_model_defaults_internal(self):
        assert classify_model("some-new-local-model") == "internal"


class TestGetInternalPrice:
    """内部模型单价"""

    def test_m3e_embedding(self):
        assert get_internal_price("m3e", "embedding") == 0.001

    def test_mlx_generation(self):
        assert get_internal_price("mlx", "generation") == 0.005

    def test_knowledge_graph(self):
        assert get_internal_price("knowledge_graph", "query") == 0.002

    def test_unknown_model_default(self):
        """未知内部模型返回默认最低价 ¥0.001"""
        assert get_internal_price("unknown", "embedding") == 0.001


class TestGetExternalCost:
    """外部模型成本价（自动 USD → CNY 转换）"""

    def test_deepseek_chat_input(self):
        cost = get_external_cost("deepseek-chat", "input")
        # 0.00027 USD × 7.25 = ¥0.0019575
        assert round(cost, 6) == round(0.00027 * 7.25, 6)

    def test_deepseek_chat_output(self):
        cost = get_external_cost("deepseek-chat", "output")
        # 0.00110 USD × 7.25 = ¥0.007975
        assert round(cost, 6) == round(0.00110 * 7.25, 6)

    def test_deepseek_reasoner(self):
        cost_input = get_external_cost("deepseek-reasoner", "input")
        cost_output = get_external_cost("deepseek-reasoner", "output")
        assert cost_input > 0
        assert cost_output > cost_input  # output 通常比 input 贵

    def test_unknown_model_zero(self):
        assert get_external_cost("unknown", "input") == 0.0


class TestGetMarkupRate:
    """加价率"""

    def test_external_default(self):
        assert get_markup_rate("external") == 0.50

    def test_internal_default(self):
        assert get_markup_rate("internal") == 0.0


class TestCalculateCost:
    """核心：费用计算"""

    def test_internal_m3e(self):
        """内部模型：固定平台价，external_cost=0"""
        result = calculate_cost(
            model_type="internal",
            model_name="m3e",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=1000,
        )
        # 1000 tokens × ¥0.001/1K = ¥0.001
        assert result["token_cost"] == 0.001
        assert result["external_cost"] == 0.0
        assert result["markup_rate"] == 0.0

    def test_internal_mlx(self):
        """内部 mlx 模型：按 embedding 定价（默认 token_type）"""
        result = calculate_cost(
            model_type="internal",
            model_name="mlx",
            total_tokens=500,
        )
        # 500 tokens × ¥0.003/1K = ¥0.0015
        assert result["token_cost"] == 0.0015

    def test_external_deepseek_chat(self):
        """外部 deepseek-chat：成本×加价率"""
        result = calculate_cost(
            model_type="external",
            model_name="deepseek-chat",
            prompt_tokens=800,
            completion_tokens=200,
        )
        # input cost: 0.00027 × 7.25 × (800/1000) = ¥0.001566
        # output cost: 0.00110 × 7.25 × (200/1000) = ¥0.001595
        # external_cost = 0.001566 + 0.001595 = ¥0.003161
        # token_cost = 0.003161 × 1.5 = ¥0.0047415
        assert result["external_cost"] > 0
        assert result["token_cost"] > result["external_cost"]
        assert result["markup_rate"] == 0.50

    def test_external_reasoner(self):
        """外部 deepseek-reasoner：更贵的推理模型"""
        result = calculate_cost(
            model_type="external",
            model_name="deepseek-reasoner",
            prompt_tokens=500,
            completion_tokens=100,
        )
        assert result["external_cost"] > 0
        assert result["token_cost"] > result["external_cost"]

    def test_external_embedding_small(self):
        """外部 embedding 模型：只有 input"""
        result = calculate_cost(
            model_type="external",
            model_name="text-embedding-3-small",
            prompt_tokens=1000,
            completion_tokens=0,
        )
        assert result["external_cost"] > 0

    def test_large_call(self):
        """大量 token 调用验证"""
        result = calculate_cost(
            model_type="external",
            model_name="deepseek-chat",
            prompt_tokens=10000,
            completion_tokens=3000,
        )
        # 预估: (10K×0.00027 + 3K×0.00110) × 7.25 × 1.5
        assert result["token_cost"] > 0.01  # 至少 > 1 分钱
        assert result["external_cost"] > 0

    def test_zero_tokens(self):
        """0 token 调用 → 费用为 0"""
        result = calculate_cost(
            model_type="internal",
            model_name="m3e",
            total_tokens=0,
        )
        assert result["token_cost"] == 0.0

    def test_alias_auto_resolution(self):
        """别名 gpt-4 → deepseek-chat，自动解析"""
        result = calculate_cost(
            model_type="external",
            model_name="gpt-4",
            prompt_tokens=800,
            completion_tokens=200,
        )
        assert result["external_cost"] > 0

    def test_unknown_external_model(self):
        """未知外部模型 → cost=0（无法计价）"""
        result = calculate_cost(
            model_type="external",
            model_name="some-future-model",
            prompt_tokens=100,
            completion_tokens=50,
        )
        assert result["external_cost"] == 0.0
        assert result["token_cost"] == 0.0


class TestPricingInternalStructure:
    """内部定价表完整性"""

    def test_all_internal_have_prices(self):
        """每个内部模型至少有一个定价类型"""
        for model, pricing in INTERNAL_PRICING.items():
            assert len(pricing) >= 1, f"{model} 缺少定价"

    def test_prices_positive(self):
        """所有价格 > 0"""
        for model, pricing in INTERNAL_PRICING.items():
            for token_type, price in pricing.items():
                assert price > 0, f"{model}/{token_type} 价格应 > 0"


class TestPricingExternalStructure:
    """外部定价表完整性"""

    def test_all_external_have_prices(self):
        """每个外部模型至少有一个定价类型"""
        for model, pricing in EXTERNAL_PRICING_USD.items():
            assert len(pricing) >= 1, f"{model} 缺少定价"

"""Token定价API路由 — 查询定价表和费用计算"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from app.ai.token_pricing import (
    INTERNAL_PRICING, EXTERNAL_PRICING_USD,
    calculate_cost as token_calculate_cost,
    get_internal_price, get_external_cost, get_markup_rate,
)

router = APIRouter(prefix="/api/v1/token", tags=["Token定价"])


class PricingResponse(BaseModel):
    model_type: str
    model_name: str
    price_per_1k: float
    unit: str
    category: str
    description: str


class CostCalculateRequest(BaseModel):
    model_type: str
    model_name: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    token_type: str = "text"


class CostResponse(BaseModel):
    model_type: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    total_cost: float
    external_cost: float
    currency: str = "CNY"
    breakdown: str


@router.get("/pricing", response_model=list[PricingResponse])
async def get_pricing():
    """获取全部模型定价表"""
    result = []

    # Internal models
    for model_name, prices in INTERNAL_PRICING.items():
        for token_type, price in prices.items():
            result.append(PricingResponse(
                model_type="internal",
                model_name=model_name,
                price_per_1k=price,
                unit="¥/1K tokens",
                category=token_type,
                description=f"自有模型 {model_name} - {token_type} ¥{price}/1K"
            ))

    # External models (USD prices)
    for model_name, prices in EXTERNAL_PRICING_USD.items():
        input_price = prices.get("input", 0)
        output_price = prices.get("output", 0)
        result.append(PricingResponse(
            model_type="external",
            model_name=model_name,
            price_per_1k=input_price,
            unit="$ USD/1M tokens",
            category="input",
            description=f"外部模型 {model_name} - input ${input_price}/1M, output ${output_price}/1M (USD)"
        ))

    return result


@router.post("/calculate", response_model=CostResponse)
async def calculate_cost_endpoint(req: CostCalculateRequest):
    """计算指定调用费用"""
    cost_result = token_calculate_cost(
        model_type=req.model_type,
        model_name=req.model_name,
        prompt_tokens=req.prompt_tokens,
        completion_tokens=req.completion_tokens,
    )

    total_tokens = req.prompt_tokens + req.completion_tokens
    total_cost = cost_result["token_cost"]
    external_cost = cost_result["external_cost"]

    if req.model_type == "internal":
        base_price = get_internal_price(req.model_name)
        breakdown = f"¥{base_price}/1K × {total_tokens}tokens = ¥{total_cost:.6f} (自有模型，平台定价)"
    else:
        input_cost = get_external_cost(req.model_name, "input") * (req.prompt_tokens / 1000.0)
        output_cost = get_external_cost(req.model_name, "output") * (req.completion_tokens / 1000.0)
        base_cost = round(input_cost + output_cost, 6)
        markup = round(total_cost - base_cost, 6)
        markup_rate = get_markup_rate("external")
        breakdown = (
            f"成本: ¥{base_cost:.6f}(input {req.prompt_tokens}tokens + output {req.completion_tokens}tokens)"
            f" + 加价{markup_rate*100:.0f}%: ¥{markup:.6f}"
            f" = 售价: ¥{total_cost:.6f}"
        )

    return CostResponse(
        model_type=req.model_type,
        model_name=req.model_name,
        prompt_tokens=req.prompt_tokens,
        completion_tokens=req.completion_tokens,
        total_tokens=total_tokens,
        total_cost=round(total_cost, 6),
        external_cost=round(external_cost, 6),
        breakdown=breakdown,
    )

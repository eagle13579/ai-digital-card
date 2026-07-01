"""AI 微服务 — 将 backend/app/ai/ 模块暴露为统一 REST API (端口 8202)"""

import os
import sys
from typing import Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# ── sys.path: 确保可导入 backend/app 下的模块 ──────────────────────────
_backend_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# ── 导入现有 AI 模块 ────────────────────────────────────────────────
from app.ai.ocr import OCRScanner
from app.ai.extractor import AIExtractor
from app.ai.writing_assistant import WritingAssistant
from app.ai.ab_testing import get_ab_testing_engine
from app.ai.rag_pipeline import RAGPipeline
from app.ai.recommendation import RecommendEngine
from app.ai.vector_search import VectorSearchEngine

# ── FastAPI 应用 ──────────────────────────────────────────────────
app = FastAPI(title="AI 微服务", version="0.1.0")


# ══════════════════════════════════════════════════════════════════
# 请求 / 响应 模型
# ══════════════════════════════════════════════════════════════════

class VectorSearchRequest(BaseModel):
    query: str
    top_k: int = 10
    min_score: float = 0.0
    exclude_user_id: Optional[int] = None


class RAGRequest(BaseModel):
    user_id: int
    query_text: str
    top_k: int = 10
    temperature: float = 0.7
    max_tokens: int = 2048
    include_sources: bool = True
    conversation_history: Optional[list[dict]] = None


class RecommendRequest(BaseModel):
    user_id: int
    top_k: int = 20
    exclude_ids: Optional[list[int]] = None
    strategy: str = "hybrid"


class OCRRequest(BaseModel):
    image_path: str
    use_external_ocr: bool = False
    extract_contacts: bool = True
    extract_business: bool = False


class WritingRequest(BaseModel):
    purpose: str  # bio | company | recommendation | slogan
    api_key: Optional[str] = None
    kwargs: dict[str, Any] = {}


class ABTestAnalyzeRequest(BaseModel):
    experiment_id: int
    events: list[dict[str, Any]]
    method: str = "chi_square"


class ExtractRequest(BaseModel):
    text: Optional[str] = None
    pdf_path: Optional[str] = None
    generate_summary: bool = False
    api_key: Optional[str] = None


# ══════════════════════════════════════════════════════════════════
# API 端点
# ══════════════════════════════════════════════════════════════════

@app.post("/ai/vector-search")
async def vector_search(req: VectorSearchRequest):
    """向量语义搜索 — 委托 VectorSearchEngine.search()"""
    try:
        # VectorSearchEngine 需要 db session，此处传入 None
        # 调用方需确保索引已构建，或自行注入 session
        engine = VectorSearchEngine(db=None)  # type: ignore[arg-type]
        results = engine.search(
            query=req.query,
            top_k=req.top_k,
            min_score=req.min_score,
            exclude_user_id=req.exclude_user_id,
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/rag")
async def rag_query(req: RAGRequest):
    """检索增强生成 — 委托 RAGPipeline.query()"""
    try:
        pipeline = RAGPipeline(db=None)  # type: ignore[arg-type]
        response = await pipeline.query(
            user_id=req.user_id,
            query_text=req.query_text,
            top_k=req.top_k,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            include_sources=req.include_sources,
            conversation_history=req.conversation_history,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/recommend")
async def recommend(req: RecommendRequest):
    """个性化推荐 — 委托 RecommendEngine.personalize_recommend()"""
    try:
        engine = RecommendEngine(db=None)  # type: ignore[arg-type]
        result = await engine.personalize_recommend(
            user_id=req.user_id,
            top_k=req.top_k,
            exclude_ids=req.exclude_ids,
            strategy=req.strategy,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/ocr")
async def ocr_scan(req: OCRRequest):
    """OCR 名片扫描 — 委托 OCRScanner.scan_card() + extract_contact_info()"""
    try:
        text = OCRScanner.scan_card(req.image_path, use_external_ocr=req.use_external_ocr)
        result = {"text": text}
        if req.extract_contacts:
            result["contacts"] = OCRScanner.extract_contact_info(text)
        if req.extract_business:
            result["business"] = OCRScanner.extract_business_info(text)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/writing")
async def writing_generate(req: WritingRequest):
    """文案生成 — 委托 WritingAssistant.generate()"""
    try:
        content = await WritingAssistant.generate(
            purpose=req.purpose,
            api_key=req.api_key,
            **req.kwargs,
        )
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/ab-test/analyze")
async def ab_test_analyze(req: ABTestAnalyzeRequest):
    """A/B 测试分析 — 委托 ABTestingEngine.compute_results()"""
    try:
        engine = get_ab_testing_engine()
        results = engine.compute_results(
            experiment_id=req.experiment_id,
            events=req.events,
            method=req.method,
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/extract")
async def extract(req: ExtractRequest):
    """信息提取 — 委托 AIExtractor 方法"""
    try:
        if req.pdf_path:
            raw_text = AIExtractor.extract_text_from_pdf(req.pdf_path)
        elif req.text:
            raw_text = req.text
        else:
            raise HTTPException(status_code=400, detail="需要提供 text 或 pdf_path")

        fields = AIExtractor.extract_fields_from_text(raw_text)
        result = {"fields": fields}

        if req.generate_summary:
            summary = await AIExtractor.generate_summary(
                text=raw_text,
                api_key=req.api_key,
            )
            result["summary"] = summary

        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "service": "ai-service"}


# ══════════════════════════════════════════════════════════════════
# 启动入口
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8202,
        reload=False,
        log_level="info",
    )

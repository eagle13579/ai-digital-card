
"""
统一推理网关 — 所有产品通过同一组API消费训练模型
==============================================
GET  /api/v1/models              - 列出所有已训练模型+版本
GET  /api/v1/models/{name}       - 单个模型详情+元数据
POST /api/v1/predict/matching    - 名片匹配推理
POST /api/v1/predict/recommend   - 内容推荐推理
POST /api/v1/predict/sales       - 销售预测推理
POST /api/v1/predict/embedding   - 向量嵌入推理

所有产品（go-aiport/GaiaCity/赛博参谋/链客宝）统一调这组API
"""
import os
import json
import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

router = APIRouter(prefix="/api/v1", tags=["推理网关"])

# ── 路径 ──
BACKEND_DIR = Path(os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..")))
DATA_DIR = BACKEND_DIR / "data"
MODELS_DIR = BACKEND_DIR / "models"


def _load_json(path: Path) -> dict:
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _file_size_mb(path: Path) -> float:
    if path.exists():
        return round(path.stat().st_size / (1024 * 1024), 2)
    return 0


# ── 模型注册表 ──

_MODEL_REGISTRY = {
    "matching_model_v2": {
        "name": "名片匹配模型v2",
        "type": "matching",
        "file": MODELS_DIR / "matching_model_v2.pt",
        "version": "2.0",
        "description": "基于标签+向量的名片匹配模型",
        "input_schema": {"user_tags": "list[dict]", "target_tags": "list[dict]"},
    },
    "matching_model_v2_mac": {
        "name": "名片匹配模型v2 (Mac MPS)",
        "type": "matching",
        "file": MODELS_DIR / "matching_model_v2_mac.pt",
        "version": "2.0",
        "description": "Mac MPS训练的匹配模型",
        "input_schema": {"user_tags": "list[dict]", "target_tags": "list[dict]"},
    },
    "online_weights": {
        "name": "在线学习权重",
        "type": "recommendation",
        "file": DATA_DIR / "online_weights.json",
        "version": "live",
        "description": "用户反馈驱动的在线推荐权重",
        "input_schema": {"user_id": "str", "context": "dict"},
    },
    "sales_prediction": {
        "name": "销售预测模型",
        "type": "prediction",
        "file": DATA_DIR / "sales_prediction_model.json",
        "version": "1.0",
        "description": "基于CRM交易数据的销售机会评分",
        "input_schema": {"deal_features": "list[float]"},
    },
    "user_tower": {
        "name": "用户塔预训练",
        "type": "embedding",
        "file": DATA_DIR / "models" / "user_tower_pretrained.pt",
        "version": "1.0",
        "description": "用户画像向量嵌入模型",
        "input_schema": {"user_id": "str"},
    },
    "knowledge_models": {
        "name": "心智模型知识库",
        "type": "knowledge",
        "file": None,
        "version": "live",
        "description": "知识库中的心智模型，通过API查询",
        "input_schema": {"query": "str"},
    },
    "gaia_evolution": {
        "name": "Gaia进化引擎",
        "type": "evolution",
        "file": None,
        "version": "live",
        "description": "模型权重的自动进化引擎",
        "input_schema": {"module": "str"},
    },
}


# ── 请求/响应模型 ──

class PredictRequest(BaseModel):
    model_name: str
    input_data: Dict[str, Any]


class ModelInfo(BaseModel):
    model_id: str
    name: str
    type: str
    version: str
    description: str
    file_size_mb: float
    trained_at: Optional[str] = None
    input_schema: Dict[str, Any]


class ModelListResponse(BaseModel):
    code: int = 200
    message: str = "ok"
    data: List[ModelInfo]


class PredictResponse(BaseModel):
    code: int = 200
    message: str = "ok"
    data: Dict[str, Any]


# ── API端点 ──

@router.get("/models", response_model=ModelListResponse)
async def list_models():
    """列出所有已训练模型+版本"""
    models = []
    for mid, cfg in _MODEL_REGISTRY.items():
        fpath = cfg.get("file")
        size = _file_size_mb(fpath) if fpath else 0
        trained_at = None
        if fpath and fpath.exists():
            mtime = datetime.datetime.fromtimestamp(fpath.stat().st_mtime)
            trained_at = mtime.isoformat()

        models.append(ModelInfo(
            model_id=mid,
            name=cfg["name"],
            type=cfg["type"],
            version=cfg["version"],
            description=cfg["description"],
            file_size_mb=size,
            trained_at=trained_at,
            input_schema=cfg["input_schema"],
        ))

    return ModelListResponse(data=models)


@router.get("/models/{model_id}", response_model=ModelInfo)
async def get_model(model_id: str):
    """单个模型详情"""
    cfg = _MODEL_REGISTRY.get(model_id)
    if not cfg:
        raise HTTPException(status_code=404, detail=f"模型 {model_id} 不存在")

    fpath = cfg.get("file")
    size = _file_size_mb(fpath) if fpath else 0
    trained_at = None
    if fpath and fpath.exists():
        mtime = datetime.datetime.fromtimestamp(fpath.stat().st_mtime)
        trained_at = mtime.isoformat()

    return ModelInfo(
        model_id=model_id,
        name=cfg["name"],
        type=cfg["type"],
        version=cfg["version"],
        description=cfg["description"],
        file_size_mb=size,
        trained_at=trained_at,
        input_schema=cfg["input_schema"],
    )


@router.post("/predict/matching", response_model=PredictResponse)
async def predict_matching(request: PredictRequest):
    """名片匹配推理 — 读取online_weights计算匹配分"""
    weights = _load_json(DATA_DIR / "online_weights.json")
    result = {
        "model": "matching_model_v2",
        "score": _calculate_matching_score(request.input_data, weights),
        "weights_used": weights,
    }
    return PredictResponse(data=result)


@router.post("/predict/recommend", response_model=PredictResponse)
async def predict_recommend(request: PredictRequest):
    """推荐推理 — 权重+反馈数据"""
    weights = _load_json(DATA_DIR / "online_weights.json")
    learning_log = DATA_DIR / "learning_log.jsonl"
    recent_feedback = []
    if learning_log.exists():
        with open(learning_log, "r", encoding="utf-8") as f:
            for line in f.readlines()[-10:]:
                try:
                    recent_feedback.append(json.loads(line))
                except Exception:
                    pass

    result = {
        "weights": weights,
        "recent_feedback_count": len(recent_feedback),
        "boost_factor": weights.get("global_adjustment", 1.0),
    }
    return PredictResponse(data=result)


@router.post("/predict/sales", response_model=PredictResponse)
async def predict_sales(request: PredictRequest):
    """销售预测推理"""
    model_data = _load_json(DATA_DIR / "sales_prediction_model.json")
    result = {
        "model_trained": model_data.get("trained", False),
        "samples": model_data.get("train_samples", 0),
        "prediction": _dummy_predict(request.input_data, model_data),
    }
    return PredictResponse(data=result)


@router.post("/predict/embedding", response_model=PredictResponse)
async def predict_embedding(request: PredictRequest):
    """向量嵌入推理 — bge-m3 嵌入服务代理"""
    # 实际调 embedding_service 或 Mac Mini :9091
    result = {
        "service": "embedding_service",
        "dimension": 768,
        "note": "当前返回占位向量，真实推理需连接embedding服务",
        "vector_preview": [0.0] * 4,
    }
    return PredictResponse(data=result)


@router.get("/predict/health")
async def predict_health():
    """推理网关健康状态"""
    model_count = len(_MODEL_REGISTRY)
    available = sum(1 for m in _MODEL_REGISTRY.values()
                    if m.get("file") is None or m["file"].exists())
    return {
        "code": 200,
        "message": "ok",
        "data": {
            "models_registered": model_count,
            "models_available": available,
            "data_dir_size_mb": _dir_size_mb(DATA_DIR),
        }
    }


def _dir_size_mb(path: Path) -> float:
    total = 0
    if path.exists():
        for f in path.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
    return round(total / (1024 * 1024), 1)


def _calculate_matching_score(input_data: dict, weights: dict) -> float:
    """简化的匹配分计算（占位逻辑，真实推理调 matching_engine）"""
    tag_match_w = weights.get("tag_match", 0.4)
    semantic_w = weights.get("semantic", 0.4)
    graph_w = weights.get("graph", 0.2)
    base = tag_match_w * 0.7 + semantic_w * 0.6 + graph_w * 0.5
    adj = weights.get("global_adjustment", 1.0)
    return round(base * adj, 4)


def _dummy_predict(input_data: dict, model: dict) -> dict:
    """简化的预测（占位逻辑，真实推理调 sales_prediction）"""
    features = input_data.get("deal_features", [])
    if model.get("trained") and len(features) == model.get("train_samples", 0):
        return {"score": 0.72, "confidence": "medium", "label": "qualified"}
    return {"score": 0.5, "confidence": "low", "label": "unscored"}

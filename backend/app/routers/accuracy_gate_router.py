"""
accuracy_gate_router.py — F20 名片Agent准确率门禁 API

API:
  POST   /api/accuracy-gate/check       — 执行门禁检查（支持CI/CD上下文）
  GET    /api/accuracy-gate/baseline     — 获取当前活跃基线
  GET    /api/accuracy-gate/history      — 门禁检查历史记录
  GET    /api/accuracy-gate/status       — 门禁系统状态概览
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Any, Optional

from app.services.accuracy_gate import (
    accuracy_gate,
    AccuracyGate,
    AccuracyGateError,
    BaselineNotFoundError,
    GateConfigNotFoundError,
    InsufficientSamplesError,
    CalibrationError,
)

router = APIRouter(prefix="/api/accuracy-gate", tags=["F20 名片Agent准确率门禁"])


# ──────────────────────────────────────────────
# 请求/响应模型
# ──────────────────────────────────────────────

class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Any = None


class CiContext(BaseModel):
    """CI/CD流水线上下文"""
    pipeline_id: Optional[str] = Field(None, description="CI/CD流水线ID")
    build_number: Optional[str] = Field(None, description="CI/CD构建编号")
    commit_sha: Optional[str] = Field(None, description="CI/CD提交SHA")
    branch: Optional[str] = Field(None, description="CI/CD分支名")


class GateCheckRequest(BaseModel):
    """门禁检查请求"""
    source: str = Field(default="api", description="检查来源 (api/ci_cd/scheduled/calibration)")
    accuracy_override: Optional[float] = Field(
        None, ge=0, le=100, description="直接传入准确率（不自动计算）"
    )
    sample_count_override: Optional[int] = Field(
        None, ge=0, description="样本数覆盖"
    )
    ci_context: Optional[CiContext] = Field(None, description="CI/CD上下文")


class CalibrateRequest(BaseModel):
    """基线校准请求"""
    calibration_type: str = Field(
        default="manual", description="校准类型 (monthly/quarterly/manual/ci_triggered)"
    )


# ──────────────────────────────────────────────
# POST /api/accuracy-gate/check — 执行门禁检查
# ──────────────────────────────────────────────

@router.post("/check", response_model=ApiResponse)
async def gate_check(req: GateCheckRequest):
    """执行准确率门禁检查

    检查逻辑:
      1. 获取当前活跃基线
      2. 计算当前准确率（或使用传入值）
      3. 对比基线阈值
      4. 输出门禁决策 (pass/block/warn/error)

    CI/CD阻断:
      - 准确率低于告警阈值 → 直接阻断 (block)
      - 准确率低于基线但高于告警阈值 → 告警 (warn) 或阻断 (block)
      - 样本数不足 → 告警 (warn)

    Returns:
        code=0: 检查成功
        code=4001: 基线不存在
        code=4002: 门禁检查异常
    """
    try:
        ci_dict = req.ci_context.model_dump() if req.ci_context else None
        result = await accuracy_gate.run_gate_check(
            source=req.source,
            accuracy_override=req.accuracy_override,
            sample_count_override=req.sample_count_override,
            ci_context=ci_dict,
        )
        return ApiResponse(
            code=0,
            message="门禁检查完成",
            data=result.to_dict(),
        )
    except BaselineNotFoundError as e:
        return ApiResponse(
            code=4001,
            message=str(e),
            data=None,
        )
    except AccuracyGateError as e:
        return ApiResponse(
            code=4002,
            message=str(e),
            data=None,
        )
    except Exception as e:
        return ApiResponse(
            code=5000,
            message=f"门禁检查异常: {str(e)}",
            data=None,
        )


# ──────────────────────────────────────────────
# GET /api/accuracy-gate/baseline — 获取基线
# ──────────────────────────────────────────────

@router.get("/baseline", response_model=ApiResponse)
async def get_baseline(
    baseline_id: Optional[str] = Query(None, description="指定基线ID（不传则返回当前活跃基线）"),
):
    """获取准确率基线

    - 不传 baseline_id: 返回当前活跃基线
    - 传 baseline_id: 返回指定基线的详情
    """
    try:
        if baseline_id:
            baseline = await accuracy_gate.get_baseline_by_id(baseline_id)
            if not baseline:
                return ApiResponse(
                    code=4001,
                    message=f"基线不存在: {baseline_id}",
                    data=None,
                )
            return ApiResponse(code=0, message="success", data=baseline.to_dict())
        else:
            baseline = await accuracy_gate.get_active_baseline()
            if not baseline:
                return ApiResponse(
                    code=4001,
                    message="没有活跃基线，请先初始化基线",
                    data=None,
                )
            return ApiResponse(code=0, message="success", data=baseline.to_dict())
    except Exception as e:
        return ApiResponse(
            code=5000,
            message=f"获取基线异常: {str(e)}",
            data=None,
        )


# ──────────────────────────────────────────────
# GET /api/accuracy-gate/history — 门禁检查历史
# ──────────────────────────────────────────────

@router.get("/history", response_model=ApiResponse)
async def get_history(
    limit: int = Query(default=50, ge=1, le=200, description="返回条数"),
    offset: int = Query(default=0, ge=0, description="偏移量"),
    source: Optional[str] = Query(None, description="按来源过滤 (api/ci_cd/scheduled/calibration)"),
    decision: Optional[str] = Query(None, description="按决策过滤 (pass/block/warn/error)"),
):
    """获取门禁检查历史记录"""
    try:
        records, total = await accuracy_gate.get_check_history(
            limit=limit,
            offset=offset,
            source=source,
            decision=decision,
        )
        return ApiResponse(
            code=0,
            message="success",
            data={
                "total": total,
                "offset": offset,
                "limit": limit,
                "records": [r.to_dict() for r in records],
            },
        )
    except Exception as e:
        return ApiResponse(
            code=5000,
            message=f"获取历史记录异常: {str(e)}",
            data=None,
        )


# ──────────────────────────────────────────────
# GET /api/accuracy-gate/status — 门禁系统状态
# ──────────────────────────────────────────────

@router.get("/status", response_model=ApiResponse)
async def get_status():
    """获取门禁系统状态概览

    包含:
      - 门禁开关状态
      - 当前活跃基线信息
      - 最近24小时检查统计
      - 系统健康状态
    """
    try:
        status = await accuracy_gate.get_gate_status()
        return ApiResponse(code=0, message="success", data=status)
    except Exception as e:
        return ApiResponse(
            code=5000,
            message=f"获取门禁状态异常: {str(e)}",
            data=None,
        )


# ──────────────────────────────────────────────
# POST /api/accuracy-gate/calibrate — 基线校准
# ──────────────────────────────────────────────

@router.post("/calibrate", response_model=ApiResponse)
async def calibrate_baseline(req: CalibrateRequest):
    """执行基线校准

    校准类型:
      - monthly: 月度校准（新阈值=当前×0.6 + 旧×0.4）
      - quarterly: 季度校准（新阈值=当前×0.5 + 旧×0.5）
      - manual: 手动校准（新阈值=当前×0.95）
      - ci_triggered: CI触发校准（新阈值=max(当前-1%, 旧)）

    校准流程:
      1. 读取当前活跃基线和F18质量基线
      2. 计算当前准确率统计
      3. 按策略生成新基线阈值
      4. 归档旧基线，激活新基线
      5. 发送校准通知
    """
    try:
        result = await accuracy_gate.calibrate_baseline(
            calibration_type=req.calibration_type,
        )
        return ApiResponse(
            code=0,
            message="基线校准完成",
            data=result.to_dict(),
        )
    except BaselineNotFoundError as e:
        return ApiResponse(
            code=4001,
            message=str(e),
            data=None,
        )
    except CalibrationError as e:
        return ApiResponse(
            code=4003,
            message=str(e),
            data=None,
        )
    except Exception as e:
        return ApiResponse(
            code=5000,
            message=f"基线校准异常: {str(e)}",
            data=None,
        )


# ──────────────────────────────────────────────
# GET /api/accuracy-gate/calibrations — 校准历史
# ──────────────────────────────────────────────

@router.get("/calibrations", response_model=ApiResponse)
async def get_calibrations(
    limit: int = Query(default=20, ge=1, le=100, description="返回条数"),
    offset: int = Query(default=0, ge=0, description="偏移量"),
    calibration_type: Optional[str] = Query(
        None, description="按类型过滤 (monthly/quarterly/manual/ci_triggered)"
    ),
):
    """获取基线校准历史"""
    try:
        records, total = await accuracy_gate.list_calibrations(
            limit=limit,
            offset=offset,
            calibration_type=calibration_type,
        )
        return ApiResponse(
            code=0,
            message="success",
            data={
                "total": total,
                "offset": offset,
                "limit": limit,
                "records": [r.to_dict() for r in records],
            },
        )
    except Exception as e:
        return ApiResponse(
            code=5000,
            message=f"获取校准历史异常: {str(e)}",
            data=None,
        )

#!/usr/bin/env python
"""
convert_matching_model_onnx.py — AI数智名片 匹配模型 ONNX + INT8 量化转换
==============================================================
背景: 硬件叙事崩塌 → 端侧轻量化。PyTorch .pt 依赖 GPU/大内存，
转换为 ONNX INT8 后: 推理快 3-5x, 内存降 4x, 可部署到端侧。

用法:
    python convert_matching_model_onnx.py            # 默认转换+量化
    python convert_matching_model_onnx.py --no-quant # 仅转换不量化

依赖 (go-aiport venv):
    torch 2.12.1+cpu, onnx 1.22.0, onnxruntime 1.20.1
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

# ── 路径 ────────────────────────────────────────────────────────────
BACKEND_DIR = Path(r"D:\AI数智名片\backend")
MODEL_DIR = BACKEND_DIR / "models"
PT_MODEL = MODEL_DIR / "matching_model_v2.pt"
ONNX_MODEL = MODEL_DIR / "matching_model_v2.onnx"
ONNX_QUANT = MODEL_DIR / "matching_model_v2_int8.onnx"
SCALERS = MODEL_DIR / "matching_scalers_v2.npy"

# ── 模型定义 (与 train_matching_model_v2.py 保持一致) ────────────────
OVERLAP_FEATURES_V2 = ["tag_overlap_score", "common_tag_count",
                       "overlap_provide_to_need", "overlap_need_to_provide",
                       "provide_need_balance"]
SEMANTIC_FEATURES_V2 = ["vector_semantic", "intro_semantic"]
WEIGHT_FEATURES_V2 = ["tag_count_a", "tag_count_b", "avg_weight_a",
                      "avg_weight_b", "tag_weight_score", "tag_category_overlap"]
ALL_FEATURES = OVERLAP_FEATURES_V2 + SEMANTIC_FEATURES_V2 + WEIGHT_FEATURES_V2
N_FEATURES = len(ALL_FEATURES)  # 13


def build_model():
    """从训练脚本动态加载模型结构。"""
    sys.path.insert(0, str(BACKEND_DIR / "scripts"))
    try:
        import train_matching_model_v2 as tm
        model = tm.ThreeTowerModelV2(dropout=0.0)  # 推理时关闭dropout
        model.eval()
        return model, tm
    except ImportError as e:
        print(f"[fallback] 直接import失败 ({e})，使用内联模型定义")
        return _inline_model(), None


def _inline_model():
    """内联三塔模型定义 (与训练脚本一致)。"""
    import torch
    import torch.nn as nn

    class ThreeTowerModelV2(nn.Module):
        def __init__(self, dropout=0.0):
            super().__init__()
            self.tower_overlap = nn.Sequential(
                nn.Linear(len(OVERLAP_FEATURES_V2), 10), nn.BatchNorm1d(10), nn.ReLU(),
                nn.Linear(10, 6), nn.BatchNorm1d(6), nn.ReLU(),
                nn.Linear(6, 4), nn.ReLU(),
            )
            self.tower_semantic = nn.Sequential(
                nn.Linear(len(SEMANTIC_FEATURES_V2), 6), nn.BatchNorm1d(6), nn.ReLU(),
                nn.Linear(6, 3), nn.ReLU(),
            )
            self.tower_weight = nn.Sequential(
                nn.Linear(len(WEIGHT_FEATURES_V2), 10), nn.BatchNorm1d(10), nn.ReLU(),
                nn.Linear(10, 6), nn.BatchNorm1d(6), nn.ReLU(),
                nn.Linear(6, 4), nn.ReLU(),
            )
            self.combined = nn.Sequential(
                nn.Linear(11, 8), nn.ReLU(),
                nn.Linear(8, 1),
            )

        def forward(self, x):
            x_o = self.tower_overlap(x[:, :len(OVERLAP_FEATURES_V2)])
            x_s = self.tower_semantic(x[:, len(OVERLAP_FEATURES_V2):len(OVERLAP_FEATURES_V2)+len(SEMANTIC_FEATURES_V2)])
            x_w = self.tower_weight(x[:, len(OVERLAP_FEATURES_V2)+len(SEMANTIC_FEATURES_V2):])
            h = torch.cat([x_o, x_s, x_w], dim=1)
            return self.combined(h)

    return ThreeTowerModelV2(dropout=0.0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-quant", action="store_true", help="跳过INT8量化")
    args = parser.parse_args()

    import torch

    print("=" * 60)
    print("matching_model_v2.pt → ONNX 转换")
    print("=" * 60)

    if not PT_MODEL.exists():
        print(f"❌ 模型不存在: {PT_MODEL}")
        sys.exit(1)

    # 1. 加载模型
    print(f"\n[1/4] 加载模型: {PT_MODEL.name}")
    model, tm = build_model()
    state = torch.load(PT_MODEL, map_location="cpu", weights_only=True)
    # 兼容三种state_dict格式: 直接权重 / model_state_dict键 / state_dict键
    if isinstance(state, dict):
        if "model_state_dict" in state:
            state = state["model_state_dict"]
        elif "state_dict" in state:
            state = state["state_dict"]
    model.load_state_dict(state)
    model.eval()
    print(f"  ✅ 加载成功 ({sum(p.numel() for p in model.parameters())} 参数)")

    # 2. 导出ONNX
    print(f"\n[2/4] 导出ONNX (batch=1, features={N_FEATURES})")
    dummy = torch.randn(1, N_FEATURES)
    with torch.no_grad():
        torch.onnx.export(
            model, dummy, str(ONNX_MODEL),
            input_names=["features"],
            output_names=["match_score"],
            dynamic_axes={"features": {0: "batch"}},
            opset_version=17,
        )
    print(f"  ✅ {ONNX_MODEL.name} ({ONNX_MODEL.stat().st_size/1024:.1f} KB)")

    # 3. INT8量化
    if not args.no_quant:
        print(f"\n[3/4] INT8量化 (动态)")
        try:
            from onnxruntime.quantization import quantize_dynamic, QuantType
            quantize_dynamic(
                str(ONNX_MODEL), str(ONNX_QUANT),
                weight_type=QuantType.QInt8,
            )
            print(f"  ✅ {ONNX_QUANT.name} ({ONNX_QUANT.stat().st_size/1024:.1f} KB)")
        except Exception as e:
            print(f"  ⚠️ 量化失败: {e} (保留FP32 ONNX)")
    else:
        print("\n[3/4] 跳过量化")

    # 4. 验证推理一致性
    print(f"\n[4/4] 验证: PyTorch vs ONNX 输出一致性")
    import onnxruntime as ort
    rng = np.random.default_rng(42)
    test_x = rng.standard_normal((5, N_FEATURES)).astype(np.float32)

    with torch.no_grad():
        pt_out = model(torch.from_numpy(test_x)).numpy().flatten()

    def run_ort(path):
        sess = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
        return sess.run(None, {"features": test_x})[0].flatten()

    onnx_out = run_ort(ONNX_MODEL)
    diff = np.abs(pt_out - onnx_out).max()
    print(f"  FP32 ONNX vs PyTorch: max_diff={diff:.6f} {'✅' if diff < 1e-3 else '⚠️'}")

    if ONNX_QUANT.exists():
        quant_out = run_ort(ONNX_QUANT)
        diff_q = np.abs(pt_out - quant_out).max()
        print(f"  INT8 ONNX vs PyTorch: max_diff={diff_q:.6f} {'✅' if diff_q < 0.1 else '⚠️'}")

    # 5. 基准 (可选快速)
    print(f"\n  📊 产出:")
    print(f"    {ONNX_MODEL.name} — FP32")
    if ONNX_QUANT.exists():
        print(f"    {ONNX_QUANT.name} — INT8 (推荐端侧)")
    print(f"\n  ✅ 转换完成! 推理代码示例:")
    print(f"    import onnxruntime as ort, numpy as np")
    print(f"    sess = ort.InferenceSession(r'{ONNX_QUANT if ONNX_QUANT.exists() else ONNX_MODEL}')")
    print(f"    score = sess.run(None, {{'features': features_np}})[0]")


if __name__ == "__main__":
    main()

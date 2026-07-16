#!/usr/bin/env python3
"""
sandwich_train.py — 三明治模型训练全流程

用744B生成高质量训练数据 → 微调专用匹配模型

三步走:
  1. 744B生成深度标注（慢但高质）
  2. 用标注数据训练/微调匹配模型
  3. 部署到在线层

用法:
  python sandwich_train.py --status          # 查看所有可训练的数据和模型
  python sandwich_train.py --generate-data   # 用744B生成训练数据（慢）
  python sandwich_train.py --train           # 训练匹配模型
  python sandwich_train.py --pipeline        # 全流程
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# ── 配置 ──
COLIBRI_API = "http://192.168.1.233:5060/v1/chat/completions"
PROJECT_ROOT = Path(__file__).parent.parent  # D:/AI数智名片
DATA_DIR = PROJECT_ROOT / "backend" / "data"
MODELS_DIR = PROJECT_ROOT / "backend" / "models"
TRAINING_DIR = PROJECT_ROOT / "training_data"
AUGMENTED_DIR = TRAINING_DIR / "augmented"
STATE_FILE = TRAINING_DIR / "sandwich_train_state.json"


def call_744b(prompt: str, max_tokens: int = 512, temperature: float = 0.1) -> str:
    """调用744B大模型"""
    import urllib.request
    data = json.dumps({
        "model": "glm-5.2-colibri",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode()
    req = urllib.request.Request(
        COLIBRI_API, data=data,
        headers={"Content-Type": "application/json"}, method="POST")
    resp = urllib.request.urlopen(req, timeout=600)
    return json.loads(resp.read())["choices"][0]["message"]["content"]


def cmd_status(args):
    """查看所有可训练的数据和模型资源"""
    print(f"\n{'='*55}")
    print("  🏗️ 三明治训练 — 资源全景")
    print(f"{'='*55}")

    # 1. 已有训练数据
    print(f"\n📊 已有训练数据:")
    data_files = [
        ("training_data.json", "匹配样本(10维特征)"),
        ("training_data_sample.json", "匹配样本示例"),
        ("v2_training_data.json", "V2增强数据"),
        ("user_embeddings.json", "用户Embedding"),
    ]
    for name, desc in data_files:
        path = DATA_DIR / name
        if path.exists():
            size = path.stat().st_size
            print(f"  ✅ {name:35s} {size//1024:>5d}KB — {desc}")

    # 2. 已有模型
    print(f"\n🧠 已有模型:")
    print(f"  ✅ GLM-5.2 744B         Mac Mini :5060  (358GB, 慢但高质)")
    print(f"  ✅ bge-small-zh-v1.5     本地 512维      (60ms, 在线层)")

    # 查看已训练模型
    model_files = list(MODELS_DIR.glob("*.pkl")) + list(MODELS_DIR.glob("*.joblib"))
    if model_files:
        for mf in model_files:
            print(f"  ✅ 已训练模型: {mf.name} ({mf.stat().st_size//1024}KB)")

    # 3. 可训练的方向
    print(f"\n🎯 可训练的3个方向 (按优先级):")
    print(f"  🔴 方向1: 匹配模型")
    print(f"     数据: 104条标注 + 126K条V2数据")
    print(f"     方法: 744B增强标注 → 训练XGBoost/MLP分类器")
    print(f"     效果: 从标签匹配升级为语义匹配")
    print(f"  🟡 方向2: Embedding增强")
    print(f"     数据: 所有客户/供应商/经销商资料")
    print(f"     方法: 744B分析 → 生成深度embedding → 替换bge-small")
    print(f"     效果: 向量搜索质量大幅提升")
    print(f"  🟢 方向3: 数字员工灵魂注入")
    print(f"     数据: 222个数字员工")
    print(f"     方法: 744B个性化生成soul-injection.yaml")
    print(f"     效果: 每个员工有更深度的灵魂和个性")

    # 4. 744B当前状态
    try:
        import urllib.request
        req = urllib.request.Request("http://192.168.1.233:5060/health", method="GET")
        resp = urllib.request.urlopen(req, timeout=5)
        h = json.loads(resp.read())
        print(f"\n🔌 744B服务: ✅ 在线 (已处理{h['scheduler']['admitted']}次请求)")
    except:
        print(f"\n🔌 744B服务: ❌ 离线")

    print(f"\n{'='*55}")


def cmd_generate_data(args):
    """用744B生成高质量训练数据"""
    print(f"\n{'='*55}")
    print("  🥪 Step 1: 744B生成训练数据")
    print(f"{'='*55}")

    # 加载现有匹配数据
    data_path = DATA_DIR / "training_data.json"
    if not data_path.exists():
        print("  ❌ training_data.json 不存在")
        return

    with open(data_path) as f:
        data = json.load(f)

    samples = data.get("samples", [])
    print(f"  原始数据: {len(samples)}条 ({data['meta']['positive_count']}正/{data['meta']['negative_count']}负)")

    # 只处理不确定的样本（分数在0.3-0.7之间）— 744B最能发挥作用的地方
    uncertain = [s for s in samples if 0.3 <= s.get("score", 0) <= 0.7]
    print(f"  需744B增强: {len(uncertain)}条（分数模糊的样本）")

    if args.dry_run:
        print("  试运行模式 — 不实际调用744B")
        return

    # 确保目录存在
    os.makedirs(AUGMENTED_DIR, exist_ok=True)

    # 逐个调用744B增强（慢！）
    augmented = []
    start = time.time()
    for i, sample in enumerate(uncertain[:args.limit]):
        user_id = sample["user_id"]
        candidate_id = sample["candidate_id"]
        score = sample["score"]
        features = sample.get("features", {})

        print(f"\n  [{i+1}/{min(len(uncertain), args.limit)}] user#{user_id} × candidate#{candidate_id} (score:{score:.2f})...", end=" ")

        prompt = f"""你是一个商业匹配专家。分析以下两个人/企业是否适合匹配合作。

用户特征: {json.dumps(features, ensure_ascii=False)}
当前匹配分: {score:.2f}（0-1之间，越高越匹配）

请判断：
1. 这个匹配是否合理？（是/否）
2. 详细理由（20字内）
3. 建议的匹配分（0-1之间，可调整当前分）

格式: JSON {{"reasonable": true/false, "reason": "...", "suggested_score": 0.0}}"""

        try:
            result = call_744b(prompt, max_tokens=128, temperature=0.1)
            # 尝试解析JSON
            result_clean = result.strip().strip("```json").strip("```").strip()
            parsed = json.loads(result_clean)
            sample["_744b_analysis"] = parsed
            sample["_744b_reasonable"] = parsed.get("reasonable", False)
            sample["_744b_suggested_score"] = parsed.get("suggested_score", score)
            print(f"✅ 合理:{parsed.get('reasonable')} 建议分:{parsed.get('suggested_score')}")
        except Exception as e:
            print(f"744B失败: {e}")
            sample["_744b_analysis"] = {"error": str(e), "raw": result[:200]}

        augmented.append(sample)

        # 每5条保存一次
        if (i + 1) % 5 == 0:
            with open(AUGMENTED_DIR / "augmented_data.json", "w") as f:
                json.dump({"meta": data["meta"], "samples": augmented,
                          "_744b_enhanced": len(augmented), "_generated_at": datetime.now().isoformat()},
                          f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start
    print(f"\n\n  完成: {len(augmented)}条 | 耗时: {elapsed:.0f}s | 平均: {elapsed/max(len(augmented),1):.1f}s/条")

    # 保存最终结果
    with open(AUGMENTED_DIR / "augmented_data.json", "w") as f:
        json.dump({"meta": data["meta"], "samples": augmented,
                  "_744b_enhanced": len(augmented), "_generated_at": datetime.now().isoformat()},
                  f, ensure_ascii=False, indent=2)
    print(f"  已保存到: {AUGMENTED_DIR / 'augmented_data.json'}")


def cmd_pipeline(args):
    """全流程: 生成数据 + 训练模型"""
    print(f"\n{'='*55}")
    print("  🥪 三明治训练全流程")
    print(f"{'='*55}")

    # Step 1: 查看状态
    cmd_status(args)

    # Step 2: 生成数据
    print(f"\n{'─'*55}")
    print("  Step 2/3: 744B生成增强数据")
    print(f"{'─'*55}")
    cmd_generate_data(args)

    # Step 3: 训练建议
    print(f"\n{'─'*55}")
    print("  Step 3/3: 下一步训练建议")
    print(f"{'─'*55}")
    print("""
  训练命令（增强数据生成后执行）:

  1. 训练XGBoost匹配模型:
     python -c "
     import json, pandas as pd
     from xgboost import XGBClassifier
     data = json.load(open('training_data/augmented/augmented_data.json'))
     samples = data['samples']
     X = [[s['features'][f] for f in data['meta']['feature_names']] for s in samples]
     y = [1 if s.get('_744b_reasonable', s['label']) else 0 for s in samples]
     model = XGBClassifier(n_estimators=100, max_depth=4)
     model.fit(X, y)
     import joblib; joblib.dump(model, 'backend/models/matching_model.pkl')
     print('模型已保存')
     "

  2. 测试新模型:
     python -c "
     import joblib
     model = joblib.load('backend/models/matching_model.pkl')
     print(f'模型准确率: {model.score(X, y):.2f}')
     "
    """)


def main():
    parser = argparse.ArgumentParser(description="三明治模型训练全流程")
    parser.add_argument("--dry-run", action="store_true", help="试运行")
    parser.add_argument("--limit", type=int, default=20, help="744B处理样本上限")

    sub = parser.add_subparsers(dest="command")
    sub.add_parser("status", help="查看所有可训练的资源")
    sub.add_parser("generate-data", help="用744B生成训练数据")
    sub.add_parser("pipeline", help="全流程")

    args = parser.parse_args()
    if args.command == "status":
        cmd_status(args)
    elif args.command == "generate-data":
        cmd_generate_data(args)
    elif args.command == "pipeline":
        cmd_pipeline(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

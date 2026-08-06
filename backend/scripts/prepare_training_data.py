#!/usr/bin/env python3
"""准备LoRA微调训练数据：将现有JSONL数据集统一转换为ChatML格式，合并去重后输出。

输入源 (自动发现):
  - training_data/auto_extracted/*.jsonl       — (instruction/input/output 格式)
  - training_data/ant_design/*.jsonl           — (instruction/input/output 格式)
  - training_data/code_assets_v1.jsonl         — (已为 ChatML 格式)
  - training_data/code_assets_v2.jsonl(可选)   — (已为 ChatML 格式)

输出:
  - training_data/train_data_chatml.jsonl      — 统一 ChatML 格式
  - training_data/train_data_stats.json        — 数据集统计
"""

import argparse
import glob
import hashlib
import json
import logging
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("prepare_training_data")

# ── ChatML 模板 ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "你是一个 AI 数字名片助手，"
    "基于企业内部代码资产库、设计系统和文档回答问题。"
)

CHATML_SYSTEM = f"<|im_start|>system\n{SYSTEM_PROMPT}\n<|im_end|>"
CHATML_USER = "<|im_start|>user\n{question}\n<|im_end|>"
CHATML_ASSISTANT = "<|im_start|>assistant\n{answer}\n<|im_end|>"

# ── 训练数据根目录 ─────────────────────────────────────────────────────────

TRAINING_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "training_data"


def sha256_digest(obj: dict) -> str:
    """计算 JSON 对象的 SHA256 指纹（用于去重）。"""
    raw = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


# ── 解析器：instruction/input/output → ChatML ──────────────────────────────


def parse_instruction_jsonl(file_path: Path) -> List[Dict]:
    """解析 instruction/input/output 格式的 JSONL，返回 ChatML message 列表。

    输入格式示例:
        {"instruction": "你是一个...", "input": "设计 Hero 组件", "output": "组件类型: Hero..."}

    输出:
        [{"messages": [...], "text": "...", "source": "<filename>"}, ...]
    """
    records = []
    seen: Set[str] = set()
    line_count = 0
    skip_count = 0

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                line_count += 1
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    skip_count += 1
                    continue

                instruction = data.get("instruction", "").strip()
                input_text = data.get("input", "").strip()
                output_text = data.get("output", "").strip()

                # 构建 question: instruction + input
                if instruction and input_text:
                    question = f"{instruction}\n\n{input_text}"
                elif instruction:
                    question = instruction
                elif input_text:
                    question = input_text
                else:
                    skip_count += 1
                    continue

                if not output_text:
                    skip_count += 1
                    continue

                # 构建 ChatML
                user_content = question
                assistant_content = output_text

                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                    {"role": "assistant", "content": assistant_content},
                ]

                text = "\n".join([
                    CHATML_SYSTEM,
                    CHATML_USER.format(question=user_content),
                    CHATML_ASSISTANT.format(answer=assistant_content),
                    "<|im_start|>assistant",  # MLX prompt 结束标记
                ])

                record = {
                    "messages": messages,
                    "text": text,
                    "source": file_path.name,
                }

                # 去重
                digest = sha256_digest(messages)
                if digest not in seen:
                    seen.add(digest)
                    records.append(record)
                else:
                    skip_count += 1

    except Exception as e:
        logger.error("读取 %s 失败: %s", file_path, e)

    logger.info(
        "  %s: 读取 %d 行, 有效 %d 条 (去重后), 跳过 %d 条",
        file_path.name, line_count, len(records), skip_count,
    )
    return records


def parse_chatml_jsonl(file_path: Path) -> List[Dict]:
    """解析已为 ChatML 格式的 JSONL（含 messages + text 字段）。

    直接读取并通过 messages 的 SHA256 去重，打上 source 标记。
    """
    records = []
    seen: Set[str] = set()
    line_count = 0
    skip_count = 0

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                line_count += 1
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    skip_count += 1
                    continue

                messages = data.get("messages")
                if not messages or not isinstance(messages, list):
                    skip_count += 1
                    continue

                # 确保有 text 字段
                text = data.get("text", "")
                if not text:
                    # 尝试重建 text
                    text_parts = []
                    for msg in messages:
                        role = msg.get("role", "")
                        content = msg.get("content", "")
                        text_parts.append(f"<|im_start|>{role}\n{content}\n<|im_end|>")
                    text_parts.append("<|im_start|>assistant")
                    text = "\n".join(text_parts)

                record = {
                    "messages": messages,
                    "text": text,
                    "source": file_path.name,
                }

                digest = sha256_digest(messages)
                if digest not in seen:
                    seen.add(digest)
                    records.append(record)
                else:
                    skip_count += 1

    except Exception as e:
        logger.error("读取 %s 失败: %s", file_path, e)

    logger.info(
        "  %s: 读取 %d 行, 有效 %d 条 (去重后), 跳过 %d 条",
        file_path.name, line_count, len(records), skip_count,
    )
    return records


# ── 发现所有数据源 ──────────────────────────────────────────────────────────


def discover_sources(data_dir: Path) -> Dict[str, List[Path]]:
    """发现所有 JSONL 数据源，按类型分组。

    Returns:
        {
            "instruction": [Path, ...],   # instruction/input/output 格式
            "chatml": [Path, ...],        # 已为 ChatML 格式
        }
    """
    sources: Dict[str, List[Path]] = {"instruction": [], "chatml": []}

    # auto_extracted/*.jsonl
    auto_dir = data_dir / "auto_extracted"
    if auto_dir.is_dir():
        for f in sorted(auto_dir.glob("*.jsonl")):
            sources["instruction"].append(f)

    # ant_design/*.jsonl
    ant_dir = data_dir / "ant_design"
    if ant_dir.is_dir():
        for f in sorted(ant_dir.glob("*.jsonl")):
            sources["instruction"].append(f)

    # code_assets_v1.jsonl, code_assets_v2.jsonl (ChatML 格式)
    for pattern in ("code_assets_v*.jsonl",):
        for f in sorted(data_dir.glob(pattern)):
            sources["chatml"].append(f)

    # 其他根目录下可能为 ChatML 格式的文件（排除已归类的）
    for f in sorted(data_dir.glob("*.jsonl")):
        if f.name.startswith("code_assets_v"):
            continue  # 已包含
        if f.name in ("train_data_chatml.jsonl", "train_data_stats.json"):
            continue
        # 默认按 ChatML 格式尝试
        sources["chatml"].append(f)

    return sources


# ── 主流程 ─────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="准备 LoRA 微调训练数据：合并/去重 JSONL → ChatML 格式",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=str(TRAINING_DATA_DIR),
        help=f"训练数据目录 (默认: {TRAINING_DATA_DIR})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="train_data_chatml.jsonl",
        help="输出文件名 (相对于 data-dir, 默认: train_data_chatml.jsonl)",
    )
    parser.add_argument(
        "--stats",
        type=str,
        default="train_data_stats.json",
        help="统计输出文件名 (相对于 data-dir, 默认: train_data_stats.json)",
    )
    parser.add_argument(
        "--dedup",
        action="store_true",
        default=True,
        help="启用去重 (默认: True)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅统计，不写文件",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.is_dir():
        logger.error("数据目录不存在: %s", data_dir)
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("训练数据准备开始")
    logger.info("数据目录: %s", data_dir)
    logger.info("=" * 60)

    # ── 发现数据源 ────────────────────────────────────────────────────
    sources = discover_sources(data_dir)

    total_instruction = len(sources["instruction"])
    total_chatml = len(sources["chatml"])
    logger.info(
        "发现 %d 个 instruction 格式文件, %d 个 ChatML 格式文件",
        total_instruction, total_chatml,
    )

    if total_instruction == 0 and total_chatml == 0:
        logger.warning("未找到任何 JSONL 数据源！")
        sys.exit(0)

    # ── 解析所有数据 ──────────────────────────────────────────────────
    all_records: List[Dict] = []
    source_stats: Dict[str, Dict] = {}

    # 处理 instruction 格式
    for file_path in sources["instruction"]:
        records = parse_instruction_jsonl(file_path)
        all_records.extend(records)
        source_stats[file_path.name] = {
            "type": "instruction",
            "count": len(records),
            "path": str(file_path),
        }

    # 处理 ChatML 格式
    for file_path in sources["chatml"]:
        records = parse_chatml_jsonl(file_path)
        all_records.extend(records)
        source_stats[file_path.name] = {
            "type": "chatml",
            "count": len(records),
            "path": str(file_path),
        }

    # ── 全局去重 ──────────────────────────────────────────────────────
    if args.dedup and all_records:
        seen: Set[str] = set()
        deduped: List[Dict] = []
        for r in all_records:
            digest = sha256_digest(r["messages"])
            if digest not in seen:
                seen.add(digest)
                deduped.append(r)
        duplicates = len(all_records) - len(deduped)
        all_records = deduped
        logger.info("全局去重: 移除 %d 条重复数据, 剩余 %d 条", duplicates, len(all_records))
    else:
        duplicates = 0

    # ── 统计信息 ──────────────────────────────────────────────────────
    role_counter: Counter = Counter()
    source_counter: Counter = Counter()
    total_tokens_est = 0
    for r in all_records:
        source_counter[r.get("source", "unknown")] += 1
        for msg in r.get("messages", []):
            role_counter[msg.get("role", "")] += 1
        total_tokens_est += len(r.get("text", "")) // 2  # 粗略估计: ~2 char/token

    stats = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_records": len(all_records),
        "duplicates_removed": duplicates,
        "source_files": source_stats,
        "records_per_source": dict(source_counter),
        "role_counts": dict(role_counter),
        "estimated_tokens": total_tokens_est,
        "data_dir": str(data_dir),
    }

    logger.info("-" * 60)
    logger.info("数据集统计:")
    logger.info("  总样本数: %d", stats["total_records"])
    logger.info("  去重移除: %d", stats["duplicates_removed"])
    logger.info("  估计 token 数: %d", stats["estimated_tokens"])
    logger.info("  各来源分布:")
    for src, cnt in sorted(source_counter.items()):
        logger.info("    %-40s %d 条", src, cnt)
    logger.info("-" * 60)

    if args.dry_run:
        logger.info("【Dry-Run】未写入任何文件。")
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return

    # ── 写入输出文件 ─────────────────────────────────────────────────
    output_path = data_dir / args.output
    with open(output_path, "w", encoding="utf-8") as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    logger.info("训练数据已写入: %s (%d 条)", output_path, len(all_records))

    stats_path = data_dir / args.stats
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    logger.info("统计数据已写入: %s", stats_path)

    # ── 打印最终摘要 ─────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("  训练数据准备完成！")
    print(f"  输出文件: {output_path}")
    print(f"  样本数量: {len(all_records)}")
    print(f"  估计token: {total_tokens_est}")
    print("=" * 60)


if __name__ == "__main__":
    main()

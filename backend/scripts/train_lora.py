#!/usr/bin/env python3
"""在 Mac Mini (192.168.1.233) 上启动 LoRA 微调训练。

架构:
  本脚本运行在 Windows 开发机上，通过 SSH 远程在 Mac Mini 上执行 MLX LoRA 训练。
  Mac Mini 上运行 MLX (Apple Silicon 优化框架) 进行高效 LoRA 微调。

用法:
  python train_lora.py --data 训练数据路径  --model 基础模型  --epochs 3 --lr 1e-4

参数:
  --data       训练数据 JSONL 路径 (ChatML 格式)
  --model      基础模型路径/名称 (如 Qwen2.5-0.5B-Instruct)
  --epochs     训练轮数 (默认: 5)
  --lr         学习率 (默认: 2e-4)
  --lora-r     LoRA rank (默认: 8)
  --lora-alpha LoRA alpha (默认: 16)
  --lora-drop  LoRA dropout (默认: 0.1)
  --batch-size  每设备批大小 (默认: 4)
  --grad-accum 梯度累积步数 (默认: 2)
  --max-seq    最大序列长度 (默认: 2048)
  --warmup     预热步数 (默认: 10)
  --output     输出目录 (默认: ./lora_output)
  --remote-dir Mac Mini 上工作目录 (默认: ~/lora_training)
  --host       Mac Mini SSH 地址 (默认: 192.168.1.233)
  --port       SSH 端口 (默认: 22)
  --user       SSH 用户名 (默认: 当前系统用户)
  --dry-run    仅打印命令，不执行
"""

import argparse
import json
import logging
import os
import shlex
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("train_lora")

# -- 默认配置 -----------------------------------------------------------------

DEFAULT_HOST = "192.168.1.233"
DEFAULT_PORT = 22
DEFAULT_REMOTE_DIR = "~/lora_training"
DEFAULT_BASE_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"

# MLX LoRA 训练脚本模板 (将在 Mac Mini 上生成并执行)
MLX_TRAIN_SCRIPT = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MLX LoRA 微调脚本 - 在 Mac Mini (Apple Silicon) 上运行。"""

import json
import logging
import os
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("mlx_lora_train")

# -- 超参数 ------------------------------------------------------------------
MODEL_PATH = "{model_path}"
TRAIN_DATA = "{train_data}"
OUTPUT_DIR = "{output_dir}"
NUM_EPOCHS = {epochs}
LEARNING_RATE = {lr}
LORA_R = {lora_r}
LORA_ALPHA = {lora_alpha}
LORA_DROPOUT = {lora_dropout}
BATCH_SIZE = {batch_size}
GRAD_ACCUM_STEPS = {grad_accum}
MAX_SEQ_LEN = {max_seq}
WARMUP_STEPS = {warmup}
SAVE_STEPS = {save_steps}
LOG_STEPS = {log_steps}

os.makedirs(OUTPUT_DIR, exist_ok=True)

# -- 检查依赖 -----------------------------------------------------------------
try:
    import mlx.core as mx
    import mlx.nn as nn
    import mlx.optimizers as optim
    from mlx.utils import tree_flatten, tree_unflatten
except ImportError:
    logger.error("需要安装 MLX: pip install mlx mlx-lm")
    sys.exit(1)

try:
    from mlx_lm import load, generate
    from mlx_lm.utils import load_config
    from mlx_lm.tuner import train, TrainingArgs
except ImportError:
    logger.error("需要安装 mlx-lm: pip install mlx-lm")
    sys.exit(1)


def main():
    logger.info("=" * 60)
    logger.info("MLX LoRA 微调启动")
    logger.info(f"  基础模型: {MODEL_PATH}")
    logger.info(f"  训练数据: {TRAIN_DATA}")
    logger.info(f"  输出目录: {OUTPUT_DIR}")
    logger.info(f"  Epochs: {NUM_EPOCHS}, LR: {LEARNING_RATE}")
    logger.info(f"  LoRA: r={LORA_R}, alpha={LORA_ALPHA}, dropout={LORA_DROPOUT}")
    logger.info(f"  Batch: {BATCH_SIZE}, Grad Accum: {GRAD_ACCUM_STEPS}")
    logger.info(f"  Max Seq: {MAX_SEQ_LEN}")
    logger.info("=" * 60)

    # -- 检查训练数据 ---------------------------------------------------------
    if not os.path.exists(TRAIN_DATA):
        logger.error(f"训练数据不存在: {TRAIN_DATA}")
        sys.exit(1)

    with open(TRAIN_DATA, "r") as f:
        num_lines = sum(1 for _ in f)
    logger.info(f"训练数据行数: {num_lines}")

    # -- 加载基础模型 ---------------------------------------------------------
    logger.info("加载基础模型中...")
    t0 = time.time()
    model, tokenizer = load(MODEL_PATH)
    logger.info(f"模型加载完成 (耗时 {time.time() - t0:.1f}s)")

    # -- 配置训练参数 ---------------------------------------------------------
    training_args = TrainingArgs(
        batch_size=BATCH_SIZE,
        iters=num_lines * NUM_EPOCHS,  # total training steps
        val_batches=0,                  # no validation during training
        steps_per_report=LOG_STEPS,
        steps_per_eval=0,
        steps_per_save=SAVE_STEPS,
        max_seq_length=MAX_SEQ_LEN,
        grad_checkpoint=False,
    )

    # -- LoRA 配置 ------------------------------------------------------------
    lora_config = {
        "num_layers": -1,          # all layers
        "lora_rank": LORA_R,
        "lora_alpha": LORA_ALPHA,
        "lora_dropout": LORA_DROPOUT,
        "lora_keys": "all",        # all linear layers
        "lora_on_modules": ["q_proj", "k_proj", "v_proj", "o_proj",
                            "gate_proj", "up_proj", "down_proj"],
    }

    # -- 优化器 --------------------------------------------------------------
    optimizer = optim.AdamW(learning_rate=LEARNING_RATE)

    # -- 准备训练数据 (JSONL -> 文本列表) ------------------------------------
    logger.info("加载训练数据...")
    texts = []
    with open(TRAIN_DATA, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                text = record.get("text", record.get("text", ""))
                if text:
                    texts.append(text)
            except json.JSONDecodeError:
                continue

    logger.info(f"加载 {len(texts)} 条训练样本")

    # -- 训练 -----------------------------------------------------------------
    logger.info("开始训练...")
    t0 = time.time()

    model, train_metrics = train(
        model=model,
        tokenizer=tokenizer,
        train_set=texts,
        args=training_args,
        optimizer=optimizer,
        lora_config=lora_config,
        adapter_path=OUTPUT_DIR,
    )

    elapsed = time.time() - t0
    logger.info(f"训练完成! 耗时 {elapsed:.1f}s ({elapsed/60:.1f} min)")

    logger.info(f"LoRA 适配器已保存到: {OUTPUT_DIR}")

    # -- 保存训练报告 ---------------------------------------------------------
    report = {
        "model": MODEL_PATH,
        "train_data": TRAIN_DATA,
        "num_samples": len(texts),
        "num_epochs": NUM_EPOCHS,
        "learning_rate": LEARNING_RATE,
        "lora_r": LORA_R,
        "lora_alpha": LORA_ALPHA,
        "lora_dropout": LORA_DROPOUT,
        "batch_size": BATCH_SIZE,
        "grad_accum_steps": GRAD_ACCUM_STEPS,
        "max_seq_len": MAX_SEQ_LEN,
        "training_time_seconds": round(elapsed, 2),
        "training_time_minutes": round(elapsed / 60, 2),
        "output_dir": OUTPUT_DIR,
        "timestamp": "{timestamp}",
        "loss_history": train_metrics if isinstance(train_metrics, list) else [],
    }

    report_path = os.path.join(OUTPUT_DIR, "training_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logger.info(f"训练报告已保存: {report_path}")

    # -- 推理测试 -------------------------------------------------------------
    logger.info("运行推理测试...")
    test_prompts = [
        "请解释 Ant Design Button 组件的用法。",
        "请分析设计系统 primary color 色板的规范。",
        "请解释前端组件 Hero 区域的设计模式。",
    ]

    test_results = []
    for prompt in test_prompts:
        formatted = (
            "<|im_start|>system\\n你是一个 AI 数字名片助手，"
            "基于企业内部代码资产库和文档回答问题。\\n<|im_end|>\\n"
            f"<|im_start|>user\\n{prompt}\\n<|im_end|>\\n"
            "<|im_start|>assistant\\n"
        )
        try:
            response = generate(
                model=model,
                tokenizer=tokenizer,
                prompt=formatted,
                max_tokens=256,
                temperature=0.7,
            )
            test_results.append({
                "prompt": prompt,
                "response": response,
            })
            logger.info(f"  OK Prompt: {prompt[:40]}...")
        except Exception as e:
            logger.warning(f"  FAIL 推理失败: {e}")
            test_results.append({
                "prompt": prompt,
                "error": str(e),
            })

    inference_path = os.path.join(OUTPUT_DIR, "test_inference.json")
    with open(inference_path, "w", encoding="utf-8") as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    logger.info(f"推理测试结果已保存: {inference_path}")

    logger.info("=" * 60)
    logger.info("MLX LoRA 微调全部完成！")
    logger.info(f"  适配器路径: {OUTPUT_DIR}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
'''


def build_train_script(args: argparse.Namespace) -> str:
    """根据参数生成 MLX 训练脚本内容。"""
    try:
        with open(args.data, "r") as f:
            num_lines = sum(1 for _ in f)
    except Exception:
        num_lines = 100  # 默认

    save_steps = max(1, (num_lines * args.epochs) // 10)
    log_steps = max(1, save_steps // 4)
    timestamp = datetime.utcnow().isoformat()

    # 使用简单替换避免 .format() 与 Python f-string 的大括号冲突
    replacements = {
        "{model_path}": shlex.quote(args.model),
        "{train_data}": shlex.quote(args.data),
        "{output_dir}": shlex.quote(args.output),
        "{epochs}": str(args.epochs),
        "{lr}": str(args.lr),
        "{lora_r}": str(args.lora_r),
        "{lora_alpha}": str(args.lora_alpha),
        "{lora_dropout}": str(args.lora_dropout),
        "{batch_size}": str(args.batch_size),
        "{grad_accum}": str(args.grad_accum),
        "{max_seq}": str(args.max_seq),
        "{warmup}": str(args.warmup),
        "{save_steps}": str(save_steps),
        "{log_steps}": str(log_steps),
        "{timestamp}": timestamp,
    }

    script = MLX_TRAIN_SCRIPT
    for placeholder, value in replacements.items():
        script = script.replace(placeholder, value)
    return script


def build_ssh_command(args: argparse.Namespace, remote_script_path: str) -> str:
    """构建 SSH 命令。"""
    ssh_opts = "-o StrictHostKeyChecking=no -o ConnectTimeout=10"
    if args.port != 22:
        ssh_opts += f" -p {args.port}"

    user_host = f"{args.user}@{args.host}" if args.user else args.host
    cmd = (
        f"ssh {ssh_opts} {user_host} "
        f'"cd {args.remote_dir} && '
        f'python3 {shlex.quote(remote_script_path)} '
        f'2>&1 | tee {shlex.quote(remote_script_path)}.log"'
    )
    return cmd


def main():
    parser = argparse.ArgumentParser(
        description="在 Mac Mini 上通过 SSH 启动 MLX LoRA 微调",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            示例:
              # 基本用法
              python train_lora.py --data ../../training_data/train_data_chatml.jsonl

              # 指定模型和超参数
              python train_lora.py \\
                --data ../../training_data/train_data_chatml.jsonl \\
                --model Qwen/Qwen2.5-0.5B-Instruct \\
                --epochs 10 --lr 1e-4 --lora-r 16

              # Dry-run 查看命令
              python train_lora.py --dry-run
        """),
    )

    # -- 训练数据参数 ---------------------------------------------------------
    parser.add_argument(
        "--data", type=str,
        default=str(
            Path(__file__).resolve().parent.parent.parent
            / "training_data" / "train_data_chatml.jsonl"
        ),
        help="训练数据 JSONL 路径 (ChatML 格式)",
    )
    parser.add_argument(
        "--model", type=str, default=DEFAULT_BASE_MODEL,
        help=f"基础模型路径/名称 (默认: {DEFAULT_BASE_MODEL})",
    )

    # -- 训练超参数 -----------------------------------------------------------
    parser.add_argument("--epochs", type=int, default=5, help="训练轮数 (默认: 5)")
    parser.add_argument("--lr", type=float, default=2e-4, help="学习率 (默认: 2e-4)")
    parser.add_argument("--lora-r", type=int, default=8, help="LoRA rank (默认: 8)")
    parser.add_argument("--lora-alpha", type=int, default=16, help="LoRA alpha (默认: 16)")
    parser.add_argument("--lora-dropout", type=float, default=0.1, help="LoRA dropout (默认: 0.1)")
    parser.add_argument("--batch-size", type=int, default=4, help="每设备批大小 (默认: 4)")
    parser.add_argument("--grad-accum", type=int, default=2, help="梯度累积步数 (默认: 2)")
    parser.add_argument("--max-seq", type=int, default=2048, help="最大序列长度 (默认: 2048)")
    parser.add_argument("--warmup", type=int, default=10, help="预热步数 (默认: 10)")

    # -- 路径参数 -------------------------------------------------------------
    parser.add_argument(
        "--output", type=str, default="./lora_output",
        help="输出目录 (相对于 remote-dir, 默认: ./lora_output)",
    )

    # -- SSH 参数 --------------------------------------------------------------
    parser.add_argument(
        "--remote-dir", type=str, default=DEFAULT_REMOTE_DIR,
        help=f"Mac Mini 上工作目录 (默认: {DEFAULT_REMOTE_DIR})",
    )
    parser.add_argument(
        "--host", type=str, default=DEFAULT_HOST,
        help=f"Mac Mini SSH 地址 (默认: {DEFAULT_HOST})",
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="SSH 端口 (默认: 22)")
    parser.add_argument(
        "--user", type=str, default=os.environ.get("USER", ""),
        help="SSH 用户名 (默认: 当前系统用户)",
    )
    parser.add_argument(
        "--identity", type=str, default="",
        help="SSH 私钥路径 (可选)",
    )

    # -- 其他 ------------------------------------------------------------------
    parser.add_argument(
        "--dry-run", action="store_true",
        help="仅打印命令和脚本，不实际执行。同时生成训练脚本到本地供审查。",
    )
    parser.add_argument(
        "--local", action="store_true",
        help="本地模式: 不在远程执行，仅在本地生成训练脚本。",
    )

    args = parser.parse_args()

    # -- 打印配置 -------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("LoRA 微调启动器")
    logger.info(f"  数据: {args.data}")
    logger.info(f"  模型: {args.model}")
    logger.info(f"  Epochs: {args.epochs}, LR: {args.lr}")
    logger.info(f"  LoRA: r={args.lora_r}, alpha={args.lora_alpha}")
    logger.info(f"  远程主机: {args.user}@{args.host}:{args.port}")
    logger.info(f"  远程目录: {args.remote_dir}")
    logger.info("=" * 60)

    # -- 验证数据文件 ---------------------------------------------------------
    data_path = Path(args.data)
    if not data_path.exists():
        logger.warning(f"训练数据文件不存在: {data_path}")
        logger.warning("请先运行 prepare_training_data.py 生成数据")
        if not args.dry_run:
            logger.warning("可运行: python prepare_training_data.py")
            sys.exit(1)

    # -- 生成训练脚本 ---------------------------------------------------------
    script_content = build_train_script(args)
    script_filename = f"mlx_lora_train_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.py"

    if args.dry_run or args.local:
        local_script_path = Path.cwd() / script_filename
        local_script_path.write_text(script_content, encoding="utf-8")
        logger.info(f"训练脚本已保存到: {local_script_path}")

        if args.dry_run:
            print()
            print("=" * 60)
            print("Dry-Run 模式 - 构建的 SSH 命令:")
            print("=" * 60)
            ssh_cmd = build_ssh_command(args, f"~/{Path(args.remote_dir).name}/{script_filename}")
            print(ssh_cmd)
            print()
            return
        elif args.local:
            logger.info("本地模式完成。可手动将脚本复制到 Mac Mini 运行。")
            return

    # -- 上传并执行 -----------------------------------------------------------
    ssh_base = "ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10"
    if args.port != 22:
        ssh_base += f" -p {args.port}"
    if args.identity:
        ssh_base += f" -i {shlex.quote(args.identity)}"
    user_host = f"{args.user}@{args.host}" if args.user else args.host

    # 1) 确保远程目录存在
    mkdir_cmd = f"{ssh_base} {user_host} 'mkdir -p {args.remote_dir}'"
    logger.info(f"创建远程目录: {mkdir_cmd}")

    try:
        subprocess.run(mkdir_cmd, shell=True, check=True, timeout=15)
        logger.info("远程目录创建成功")
    except subprocess.CalledProcessError as e:
        logger.error(f"创建远程目录失败: {e}")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        logger.error("SSH 连接超时")
        sys.exit(1)

    # 2) 将训练脚本通过 SSH 管道写入远程文件
    write_cmd = (
        f"{ssh_base} {user_host} "
        f"'cat > {args.remote_dir}/{script_filename}'"
    )
    logger.info("上传训练脚本到远程...")

    try:
        proc = subprocess.Popen(
            write_cmd, shell=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate(
            input=script_content.encode("utf-8"), timeout=30
        )
        if proc.returncode != 0:
            logger.error(f"上传脚本失败: {stderr.decode()}")
            sys.exit(1)
        logger.info("训练脚本上传成功")
    except Exception as e:
        logger.error(f"上传脚本异常: {e}")
        sys.exit(1)

    # 3) 同步训练数据到远程
    logger.info("同步训练数据到远程...")
    data_remote_path = f"{args.remote_dir}/train_data.jsonl"
    scp_cmd = "scp -o StrictHostKeyChecking=no -o ConnectTimeout=10"
    if args.port != 22:
        scp_cmd += f" -P {args.port}"
    if args.identity:
        scp_cmd += f" -i {shlex.quote(args.identity)}"
    scp_cmd += (
        f" {shlex.quote(str(data_path))}"
        f" {user_host}:{shlex.quote(data_remote_path)}"
    )

    try:
        subprocess.run(scp_cmd, shell=True, check=True, timeout=120)
        logger.info("训练数据同步成功")
    except subprocess.CalledProcessError as e:
        logger.error(f"训练数据同步失败: {e}")
        logger.warning("请手动将数据复制到 Mac Mini")
        sys.exit(1)

    # 4) 在远程执行训练脚本
    logger.info("=" * 60)
    logger.info("在 Mac Mini 上启动训练...")
    logger.info("=" * 60)

    remote_script = f"{args.remote_dir}/{script_filename}"
    run_cmd = (
        f"{ssh_base} -t {user_host} "
        f"'cd {args.remote_dir} && "
        f"python3 {remote_script} "
        f"2>&1 | tee {remote_script}.log'"
    )
    logger.info(f"执行命令: {run_cmd}")

    try:
        subprocess.run(run_cmd, shell=True, check=True, timeout=86400)
        logger.info("训练完成！")
    except subprocess.TimeoutExpired:
        logger.warning("训练超时(24h)，请检查远程状态")
    except subprocess.CalledProcessError as e:
        logger.error(f"训练执行失败 (返回码 {e.returncode})")
        logger.info(f"可 SSH 登录检查日志: {ssh_base} {user_host} "
                    f"'cat {remote_script}.log'")
        sys.exit(1)

    # -- 最终指引 -------------------------------------------------------------
    print()
    print("=" * 60)
    print("  LoRA 微调流程完成！")
    print()
    print("  后续步骤:")
    print(f"    1. SSH 到 Mac Mini 检查输出:")
    print(f"       ssh {user_host} 'ls -la {args.remote_dir}/{args.output}/'")
    print(f"    2. 运行推理测试:")
    print(f"       ssh {user_host} 'cat {args.remote_dir}/"
          f"{args.output}/test_inference.json'")
    print(f"    3. 部署模型:")
    print(f"       python deploy_model.py "
          f"--adapter-path {args.remote_dir}/{args.output}")
    print("=" * 60)


if __name__ == "__main__":
    main()

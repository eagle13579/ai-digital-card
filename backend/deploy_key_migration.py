#!/usr/bin/env python3
"""
AI数智名片 — 安全密钥部署脚本
===============================
通过 SSH 将加密密钥文件部署到生产服务器，并配置 SECRET_MASTER_KEY。

用法:
    python deploy_key_migration.py [--server 47.116.116.87] [--user root]

前提:
    1. 已安装 sshpass (或已配置 SSH 密钥认证)
    2. backend/.env.encrypted 已存在 (通过 key_manager.py encrypt 生成)
    3. 已将 SECRET_MASTER_KEY 分享给部署者 (通过安全渠道)
"""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.resolve()
ENCRYPTED_ENV = BACKEND_DIR / ".env.encrypted"
DEPLOY_SYSTEMD_SERVICE = "aibizcard-backend"  # 生产 systemd 服务名


def run_ssh(host: str, user: str, cmd: str, password: str = "") -> str:
    """通过 SSH 执行远程命令并返回输出。"""
    ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10"]
    if password:
        ssh_cmd = ["sshpass", "-p", password] + ssh_cmd
    ssh_cmd += [f"{user}@{host}", cmd]
    try:
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"⚠️  SSH 命令警告 (rc={result.returncode}): {result.stderr[:200]}")
        return result.stdout
    except FileNotFoundError:
        print("❌ sshpass 未安装。安装: apt install sshpass 或使用 SSH 密钥认证。")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"❌ SSH 连接超时: {user}@{host}")
        sys.exit(1)


def run_scp(host: str, user: str, local_path: str, remote_path: str, password: str = "") -> None:
    """通过 SCP 上传文件到服务器。"""
    scp_cmd = ["scp", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10"]
    if password:
        scp_cmd = ["sshpass", "-p", password] + scp_cmd
    scp_cmd += [local_path, f"{user}@{host}:{remote_path}"]
    try:
        result = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"⚠️  SCP 警告: {result.stderr[:200]}")
    except Exception as exc:
        print(f"❌ SCP 失败: {exc}")
        sys.exit(1)


def check_prerequisites() -> bool:
    """检查前提条件。"""
    if not ENCRYPTED_ENV.exists():
        print(f"❌ 加密文件不存在: {ENCRYPTED_ENV}")
        print("   请先运行: python key_manager.py encrypt")
        return False

    master_key = os.environ.get("SECRET_MASTER_KEY")
    if not master_key:
        print("⚠️  未设置 SECRET_MASTER_KEY 环境变量。")
        print("   部署时将提示您手动输入。")
        return True

    print(f"✅  SECRET_MASTER_KEY 已设置 (前8位: {master_key[:8]}...)")
    print(f"✅  {ENCRYPTED_ENV.name} 已存在 ({ENCRYPTED_ENV.stat().st_size / 1024:.1f} KB)")
    return True


def deploy_to_server(host: str, user: str, password: str, master_key: str) -> None:
    """将加密文件和配置部署到生产服务器。"""
    print(f"\n{'='*60}")
    print(f"🚀 部署到 {user}@{host}")
    print(f"{'='*60}\n")

    # ── 步骤 1: 上传 .env.encrypted ──
    print("📤 [1/4] 上传 .env.encrypted...")
    remote_base = "/opt/aibizcard/backend"
    run_ssh(host, user, f"mkdir -p {remote_base}", password)
    run_scp(host, user, str(ENCRYPTED_ENV), f"{remote_base}/.env.encrypted", password)
    run_ssh(host, user, f"chmod 600 {remote_base}/.env.encrypted", password)
    print("   ✅ 上传完成")

    # ── 步骤 2: 设置 SECRET_MASTER_KEY 到 .profile ──
    print("🔑 [2/4] 设置 SECRET_MASTER_KEY 到 ~/.profile...")
    profile_line = f'export SECRET_MASTER_KEY="{master_key}"'
    # 检查是否已存在
    existing = run_ssh(host, user, f'grep "SECRET_MASTER_KEY" ~/.profile || true', password)
    if "SECRET_MASTER_KEY" in existing:
        # 更新现有条目
        run_ssh(host, user, f'sed -i "s|^export SECRET_MASTER_KEY=.*|{profile_line}|" ~/.profile', password)
        print("   ✅ ~/.profile 已更新")
    else:
        run_ssh(host, user, f'echo "{profile_line}" >> ~/.profile', password)
        print("   ✅ ~/.profile 已追加")

    # ── 步骤 3: 添加到 systemd 服务环境变量 ──
    print("🛠️  [3/4] 设置 SECRET_MASTER_KEY 到 systemd 服务...")
    service_file = f"/etc/systemd/system/{DEPLOY_SYSTEMD_SERVICE}.service"
    # 检查服务是否存在
    svc_check = run_ssh(host, user, f"test -f {service_file} && echo 'exists' || echo 'missing'", password)
    if "exists" in svc_check:
        # 检查是否有 EnvironmentFile 或 Environment 行
        env_check = run_ssh(
            host, user,
            f"grep -E '(EnvironmentFile=|Environment=.*SECRET_MASTER_KEY)' {service_file} || true",
            password,
        )
        if "EnvironmentFile" in env_check:
            # 如果已有 EnvironmentFile, 追加到该文件
            env_file_path = run_ssh(
                host, user,
                f"grep 'EnvironmentFile=' {service_file} | head -1 | sed 's/.*EnvironmentFile=//'",
                password,
            ).strip()
            if env_file_path:
                run_ssh(host, user, f'mkdir -p $(dirname {env_file_path})', password)
                # 检查环境文件是否已包含
                env_file_content = run_ssh(host, user, f"test -f {env_file_path} && cat {env_file_path} || true", password)
                if "SECRET_MASTER_KEY" in env_file_content:
                    # 更新
                    run_ssh(
                        host, user,
                        f'sed -i "s|^SECRET_MASTER_KEY=.*|SECRET_MASTER_KEY={master_key}|" {env_file_path}',
                        password,
                    )
                else:
                    run_ssh(host, user, f'echo "SECRET_MASTER_KEY={master_key}" >> {env_file_path}', password)
                run_ssh(host, user, f"chmod 600 {env_file_path}", password)
                print(f"   ✅ 已追加到 EnvironmentFile: {env_file_path}")
        else:
            # 在 [Service] 段添加 Environment
            run_ssh(
                host, user,
                f"sed -i '/^\\[Service\\]/a Environment=SECRET_MASTER_KEY={master_key}' {service_file}",
                password,
            )
            print(f"   ✅ 已添加 Environment= 到 {service_file}")

        # 重新加载 systemd
        run_ssh(host, user, "systemctl daemon-reload", password)
        print("   ✅ systemd reloaded")
    else:
        print(f"   ⚠️  systemd 服务 {DEPLOY_SYSTEMD_SERVICE} 不存在, 跳过。")
        print(f"      SECRET_MASTER_KEY 已设置在 ~/.profile 中。")

    # ── 步骤 4: 重启服务 ──
    print("🔄 [4/4] 重启后端服务...")
    if "exists" in svc_check:
        run_ssh(host, user, f"systemctl restart {DEPLOY_SYSTEMD_SERVICE}", password)
        # 检查状态
        status = run_ssh(host, user, f"systemctl is-active {DEPLOY_SYSTEMD_SERVICE}", password).strip()
        if status == "active":
            print(f"   ✅ {DEPLOY_SYSTEMD_SERVICE} 已重启并正常运行")
        else:
            print(f"   ⚠️  服务状态: {status}")
            logs = run_ssh(host, user, f"journalctl -u {DEPLOY_SYSTEMD_SERVICE} -n 20 --no-pager", password)
            print(f"      最近日志:\n{logs}")
    else:
        print("   ⚠️  服务不存在, 跳过重启。")
        print("   请手动重启后端进程以加载新环境变量。")

    print(f"\n{'='*60}")
    print("✅ 部署完成!")
    print(f"{'='*60}")
    print(f"\n📋 验证:")
    print(f"   1. SSH 登录服务器: ssh {user}@{host}")
    print(f"   2. 检查密钥: echo $SECRET_MASTER_KEY | head -c 16")
    print(f"   3. 检查加密文件: ls -la {remote_base}/.env.encrypted")
    print(f"   4. 查看服务状态: systemctl status {DEPLOY_SYSTEMD_SERVICE}")


def main():
    parser = argparse.ArgumentParser(description="部署加密密钥到生产服务器")
    parser.add_argument("--server", default="47.116.116.87", help="生产服务器 IP/域名")
    parser.add_argument("--user", default="root", help="SSH 用户名")
    parser.add_argument("--password", default="", help="SSH 密码 (留空则使用密钥认证)")
    parser.add_argument("--master-key", default="",
                        help="SECRET_MASTER_KEY (留空则从环境变量读取或交互式输入)")
    args = parser.parse_args()

    # 检查前提条件
    if not check_prerequisites():
        sys.exit(1)

    # 获取主密钥
    master_key = args.master_key or os.environ.get("SECRET_MASTER_KEY", "")
    if not master_key:
        print("\n🔑 SECRET_MASTER_KEY 未设置。")
        master_key = input("   请输入主密钥 (输入内容不会显示): ").strip()
        if not master_key:
            print("❌ 主密钥不能为空")
            sys.exit(1)

    print(f"\n⚠️  即将部署到 {args.user}@{args.server}")
    confirm = input("   确认继续? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("❌ 已取消")
        sys.exit(0)

    deploy_to_server(
        host=args.server,
        user=args.user,
        password=args.password,
        master_key=master_key,
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康雷达 v1.0 — AI数智军团综合可观测性扫描
量化 9 大维度健康指标，支持基线对比与变更检测。

用法:
  python3 health_radar.py --baseline   # 首次扫描并保存基线（全量报告）
  python3 health_radar.py --check      # 对比基线，只输出变化（供 cron 静默巡检）
  python3 health_radar.py --report     # 全量报告（不存基线）
  python3 health_radar.py --json       # 输出 JSON 机器可读

指标维度:
  SVC  服务健康 (端口+HTTP)      CODE 代码同步 (分支+未推送)
  TEST 测试门禁 (契约+graphql)   KB   知识库健康 (盖娅量+同步区)
  RES  资源水位 (磁盘+内存)      PROC 常驻进程
  CRON 定时任务状态              GIT  仓库完整性
  DB   数据库连通
"""
import json
import os
import re
import socket
import subprocess
import sys
import time
from datetime import datetime

STATE_DIR = "/opt/hermes-remote/home/state"
BASELINE_FILE = os.path.join(STATE_DIR, "health_radar_baseline.json")
REPO = "/var/www/ai-digital-card"
BACKEND = os.path.join(REPO, "backend")

# ---------------- 工具函数 ----------------

def run(cmd, timeout=15, cwd=None):
    """执行命令返回 (rc, stdout)"""
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, errors='replace',
                           timeout=timeout, cwd=cwd or REPO)
        return p.returncode, p.stdout.strip()
    except subprocess.TimeoutExpired:
        return 124, ""
    except Exception as e:
        return -1, str(e)

def check_port(port, host="127.0.0.1"):
    """TCP 端口探测"""
    try:
        s = socket.create_connection((host, port), timeout=2)
        s.close()
        return True
    except OSError:
        return False

def check_http(port, path="/api/health", host="127.0.0.1", timeout=4):
    """HTTP 健康检查"""
    try:
        import urllib.request
        req = urllib.request.Request(f"http://{host}:{port}{path}", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except Exception:
        return 0

def get_size_mb(path):
    """目录大小 MB（浅层 du）"""
    rc, out = run(f"du -sm {path} 2>/dev/null | cut -f1", timeout=20)
    try:
        return int(out)
    except (ValueError, TypeError):
        return -1

# ---------------- 指标采集 ----------------

def scan_services():
    """SVC: 服务健康"""
    services = [
        ("ai-digital-card", 8201, "/api/health"),
        ("gaia-commercial(灵枢)", 8555, "/"),
        ("ai-shuzhi(军团总览)", 5070, "/"),
    ]
    out = {}
    for name, port, path in services:
        port_ok = check_port(port)
        http = check_http(port, path) if port_ok else 0
        out[name] = {"port": port, "listen": port_ok, "http": http,
                     "ok": port_ok and http in (200, 302, 308)}
    # 链客宝（区分「未启动」与「异常」）
    port_ok = check_port(8001)
    # 链客宝真实健康端点是 /health（/api/health 已废弃返回404，2026-08-08 实测）
    http = check_http(8001, "/health") if port_ok else 0
    out["chainke(链客宝)"] = {"port": 8001, "listen": port_ok, "http": http,
                              "ok": port_ok and http in (200, 302, 308),
                              "note": "" if port_ok else "未启动(服务inactive)"}
    return out

def scan_code():
    """CODE: 分支同步 + 未推送"""
    out = {"master_ahead": -1, "master_behind": -1, "dirty": False, "current": ""}
    rc, cur = run("git branch --show-current", cwd=REPO)
    out["current"] = cur
    rc, dirty = run("git status --porcelain | wc -l", cwd=REPO)
    out["dirty_files"] = int(dirty or 0)
    # 对比 origin/master
    rc, ahead = run("git rev-list --count origin/master..master", cwd=REPO)
    rc2, behind = run("git rev-list --count master..origin/master", cwd=REPO)
    out["master_ahead"] = int(ahead or 0)
    out["master_behind"] = int(behind or 0)
    # 未推送分支数（本地领先的本地分支）
    rc, brs = run("git for-each-ref --format='%(refname:short) %(upstream:short)' refs/heads/", cwd=REPO)
    out["local_branches"] = len([l for l in brs.splitlines() if l.strip()]) if brs else 0
    return out

def scan_tests():
    """TEST: 测试门禁（快速子集）"""
    out = {"api_standards": None, "graphql": None}
    env = f"cd {BACKEND} && PYTHONPATH=/var/www venv/bin/pytest"
    rc, res = run(f"{env} tests/test_api_standards.py -q --no-header -p no:warnings --timeout=60 2>&1 | tail -1", timeout=90)
    m = re.search(r"(\d+) passed", res or "")
    out["api_standards"] = int(m.group(1)) if m else (0 if rc != 0 else None)
    rc, res = run(f"{env} tests/test_graphql.py -q --no-header -p no:warnings --timeout=60 2>&1 | tail -1", timeout=90)
    m = re.search(r"(\d+) passed", res or "")
    out["graphql"] = int(m.group(1)) if m else (0 if rc != 0 else None)
    return out

def scan_kb():
    """KB: 知识库健康"""
    out = {}
    # 盖娅知识量
    rc, res = run("psql --version", timeout=5)
    rc, cnt = run(
        "DB_URL=$(grep '^DATABASE_URL' backend/.env | cut -d= -f2-); "
        "PGURL=$(echo \"$DB_URL\" | sed 's/+asyncpg//'); "
        f"psql \"$PGURL\" -t -c 'SELECT count(*) FROM gaia_knowledge;' 2>/dev/null | tr -d ' '",
        timeout=15, cwd=REPO)
    out["gaia_knowledge"] = int(cnt) if (cnt and cnt.isdigit()) else -1
    # 同步区文件数（递归）
    rc, n = run("find knowledge-sync/local -type f 2>/dev/null | wc -l", cwd=REPO)
    out["sync_local_files"] = int(n or 0)
    return out

def scan_resources():
    """RES: 资源水位"""
    out = {}
    rc, df = run("df -h / | tail -1 | awk '{print $5}' | tr -d '%'")
    out["disk_used_pct"] = int(df) if (df and df.isdigit()) else -1
    rc, mem = run("free -m | awk 'NR==2{printf \"%d %d\", $3, $2}'")
    parts = mem.split()
    out["mem_used_mb"] = int(parts[0]) if parts else -1
    out["mem_total_mb"] = int(parts[1]) if len(parts) > 1 else -1
    return out

def scan_procs():
    """PROC: 常驻进程（稳定计数：只看主进程，避免 worker 波动噪音）"""
    wanted = ["hermes gateway run", "start_agents.py", "legion_wake_scheduler.py",
              "uvicorn main:app", "gunicorn -w"]
    out = {}
    for w in wanted:
        rc, n = run(f"ps aux | grep -E '{w}' | grep -v grep | wc -l")
        out[w] = int(n or 0)
    return out

def scan_cron():
    """CRON: Hermes 任务健康（从 gateway 侧看最近运行）"""
    out = {}
    rc, n = run("systemctl is-active hermes-remote-gateway 2>/dev/null | tr -d ' '")
    out["gateway"] = n if n else "unknown"
    rc, n = run("ls /opt/hermes-remote/home/logs/ 2>/dev/null | wc -l")
    out["log_files"] = int(n or 0)
    return out

def scan_git_repo():
    """GIT: 仓库完整性"""
    out = {}
    # %h+%s 由 git 自己截断（不会切断 UTF-8 多字节），比 cut -c1-40 安全（2026-08-08 修复中文切断）
    rc, head = run("git log --pretty='%h %s' master -1", cwd=REPO)
    out["master_head"] = head if head else "?"
    rc, tag = run("git describe --tags --abbrev=0 2>/dev/null", cwd=REPO)
    out["latest_tag"] = tag if tag else "none"
    return out

def scan_db():
    """DB: 数据库连通"""
    rc, res = run(
        "DB_URL=$(grep '^DATABASE_URL' backend/.env | cut -d= -f2-); "
        "PGURL=$(echo \"$DB_URL\" | sed 's/+asyncpg//'); "
        f"psql \"$PGURL\" -t -c 'SELECT 1;' 2>/dev/null | tr -d ' '",
        timeout=15, cwd=REPO)
    out = {"ok": res == "1", "probe": res if res else "FAIL"}
    return out

# ---------------- 汇总 ----------------

def compute_score(data):
    """综合健康评分 0-100"""
    score = 0
    max_score = 0
    # 服务 25 分
    for name, svc in data["services"].items():
        max_score += 25 / max(len(data["services"]), 1)
        if svc["ok"]:
            score += 25 / max(len(data["services"]), 1)
    # 代码 15 分
    max_score += 15
    code = data["code"]
    if code["master_ahead"] == 0 and code["master_behind"] == 0:
        score += 15
    elif code["master_ahead"] <= 5 and code["master_behind"] <= 5:
        score += 8
    elif code["master_ahead"] <= 20:
        score += 4
    # 测试 20 分
    max_score += 20
    t = data["tests"]
    if t["api_standards"] is not None:
        score += 10 if t["api_standards"] >= 15 else (5 if t["api_standards"] > 0 else 0)
    if t["graphql"] is not None:
        score += 10 if t["graphql"] >= 10 else (5 if t["graphql"] > 0 else 0)
    # 知识库 10 分
    max_score += 10
    kb = data["kb"]
    if kb["gaia_knowledge"] > 0:
        score += 5
    if kb["sync_local_files"] > 100:
        score += 5
    # 资源 15 分
    max_score += 15
    res = data["resources"]
    if res["disk_used_pct"] >= 0:
        if res["disk_used_pct"] < 75:
            score += 10
        elif res["disk_used_pct"] < 90:
            score += 5
    if res["mem_total_mb"] > 0:
        ratio = res["mem_used_mb"] / res["mem_total_mb"]
        if ratio < 0.8:
            score += 5
    # 进程 10 分
    max_score += 10
    procs = data["procs"]
    if procs.get("uvicorn main:app", 0) >= 1 and procs.get("gunicorn -w", 0) >= 1:
        score += 5
    if procs.get("start_agents.py", 0) >= 1:
        score += 5
    # DB 5 分
    max_score += 5
    if data["db"]["ok"]:
        score += 5
    pct = round(score / max_score * 100) if max_score else 0
    return pct

def grade(pct):
    if pct >= 90:
        return "🟢 优秀"
    if pct >= 75:
        return "🟡 良好"
    if pct >= 60:
        return "🟠 警告"
    return "🔴 危险"

def human_report(data, score):
    lines = []
    lines.append(f"# 健康雷达 {grade(score)} 综合评分: {score}/100")
    lines.append(f"> 扫描时间: {data['meta']['time']} | 标签: {data['meta']['tag']}")
    lines.append("")
    # 服务
    lines.append("## 🖥 服务健康")
    for name, svc in data["services"].items():
        mark = "✅" if svc["ok"] else "❌"
        note = f" {svc['note']}" if svc.get("note") else ""
        lines.append(f"- {mark} {name} (:{svc['port']}) listen={svc['listen']} http={svc['http']}{note}")
    # 代码
    c = data["code"]
    lines.append("")
    lines.append("## 🌿 代码同步")
    lines.append(f"- 分支: {c['current']} | master ahead={c['master_ahead']} behind={c['master_behind']} | 脏文件={c['dirty_files']} | 本地分支={c['local_branches']}")
    lines.append(f"- HEAD: {data['git']['master_head']} | tag: {data['git']['latest_tag']}")
    # 测试
    t = data["tests"]
    lines.append("")
    lines.append("## 🧪 测试门禁")
    lines.append(f"- API 契约: {t['api_standards']}/15 | graphql: {t['graphql']}/10")
    # 知识库
    kb = data["kb"]
    lines.append("")
    lines.append("## 📚 知识库")
    lines.append(f"- 盖娅知识量: {kb['gaia_knowledge']} | 本地同步区: {kb['sync_local_files']} 文件")
    # 资源
    r = data["resources"]
    lines.append("")
    lines.append("## 💾 资源")
    lines.append(f"- 磁盘: {r['disk_used_pct']}% | 内存: {r['mem_used_mb']}/{r['mem_total_mb']} MB")
    # 进程
    p = data["procs"]
    cr = data["cron"]
    lines.append("")
    lines.append("## ⚙️ 进程")
    lines.append(f"- gateway={cr.get('gateway','?')} | start_agents={p.get('start_agents.py',0)} | scheduler={p.get('legion_wake_scheduler.py',0)} | uvicorn={p.get('uvicorn main:app',0)} | gunicorn={p.get('gunicorn -w',0)}")
    # DB
    lines.append("")
    lines.append(f"## 🗄 数据库: {'✅ 连通' if data['db']['ok'] else '❌ 异常 (' + str(data['db']['probe']) + ')'}")
    return "\n".join(lines)

def diff_report(baseline, current):
    """对比基线，返回变化描述列表"""
    changes = []
    b, c = baseline, current
    # 服务
    for name in set(list(b.get("services", {}).keys()) + list(c.get("services", {}).keys())):
        bs = b.get("services", {}).get(name, {})
        cs = c.get("services", {}).get(name, {})
        if bs.get("ok") != cs.get("ok"):
            changes.append(f"SVC {name}: {'✅恢复' if cs.get('ok') else '❌异常'} (http {bs.get('http')}→{cs.get('http')})")
    # 代码
    for k in ["master_ahead", "master_behind", "dirty_files"]:
        if b.get("code", {}).get(k) != c.get("code", {}).get(k):
            changes.append(f"CODE {k}: {b.get('code', {}).get(k)} → {c.get('code', {}).get(k)}")
    # 测试
    for k in ["api_standards", "graphql"]:
        if b.get("tests", {}).get(k) != c.get("tests", {}).get(k):
            changes.append(f"TEST {k}: {b.get('tests', {}).get(k)} → {c.get('tests', {}).get(k)}")
    # 知识库
    for k in ["gaia_knowledge", "sync_local_files"]:
        if b.get("kb", {}).get(k) != c.get("kb", {}).get(k):
            changes.append(f"KB {k}: {b.get('kb', {}).get(k)} → {c.get('kb', {}).get(k)}")
    # 资源
    for k in ["disk_used_pct"]:
        if b.get("resources", {}).get(k) != c.get("resources", {}).get(k):
            changes.append(f"RES {k}: {b.get('resources', {}).get(k)}% → {c.get('resources', {}).get(k)}%")
    # 进程
    for k in ["gateway", "uvicorn main:app", "gunicorn -w", "start_agents.py"]:
        if b.get("procs", {}).get(k) != c.get("procs", {}).get(k):
            changes.append(f"PROC {k}: {b.get('procs', {}).get(k)} → {c.get('procs', {}).get(k)}")
    # DB
    if b.get("db", {}).get("ok") != c.get("db", {}).get("ok"):
        changes.append(f"DB: {'✅恢复' if c.get('db', {}).get('ok') else '❌异常'}")
    # HEAD
    if b.get("git", {}).get("master_head") != c.get("git", {}).get("master_head"):
        changes.append(f"GIT HEAD: {b.get('git', {}).get('master_head','?')[:10]} → {c.get('git', {}).get('master_head','?')[:10]}")
    # 评分
    bs = b.get("score", 0)
    cs = c.get("score", 0)
    if bs != cs:
        changes.append(f"SCORE: {bs} → {cs}")
    return changes

# ---------------- 主流程 ----------------

def main():
    mode = "--check"
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    tag = os.environ.get("RADAR_TAG", "")

    data = {
        "meta": {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "tag": tag},
        "services": scan_services(),
        "code": scan_code(),
        "tests": scan_tests(),
        "kb": scan_kb(),
        "resources": scan_resources(),
        "procs": scan_procs(),
        "cron": scan_cron(),
        "git": scan_git_repo(),
        "db": scan_db(),
    }
    data["score"] = compute_score(data)

    os.makedirs(STATE_DIR, exist_ok=True)

    if mode == "--baseline":
        with open(BASELINE_FILE, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(human_report(data, data["score"]))
        print("\n✅ 基线已保存 →", BASELINE_FILE)

    elif mode == "--json":
        print(json.dumps(data, ensure_ascii=False, indent=2))

    elif mode == "--check":
        if not os.path.exists(BASELINE_FILE):
            print(human_report(data, data["score"]))
            print("\n⚠️ 无基线，已用本次扫描作为基线")
            with open(BASELINE_FILE, "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return
        with open(BASELINE_FILE) as f:
            baseline = json.load(f)
        changes = diff_report(baseline, data)
        if changes:
            lines = [f"📡 健康雷达变更 (评分 {baseline.get('score','?')} → {data['score']})"]
            lines.append(f"> 时间: {data['meta']['time']}")
            lines.extend(["- " + ch for ch in changes])
            lines.append("")
            lines.append(human_report(data, data["score"]))
            print("\n".join(lines))
        # 评分大幅下降也提示
        elif baseline.get("score", 0) - data["score"] >= 15:
            print(f"📉 健康评分下降: {baseline.get('score')} → {data['score']}")
            print(human_report(data, data["score"]))
        # 静默（无变化）

    else:  # --report
        print(human_report(data, data["score"]))

if __name__ == "__main__":
    main()

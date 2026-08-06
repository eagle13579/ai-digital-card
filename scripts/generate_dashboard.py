#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI数智军团 运行看板生成器
产出: D:\AI数智名片\dashboard\index.html + 盖娅之城 static/
"""
import json, os, socket, subprocess
from datetime import datetime

HERMES = r"D:\向海容的知识库\wiki\wiki\记忆宫殿"
OUT_DIRS = [
    r"D:\AI数智名片\dashboard",
    r"D:\向海容的知识库\wiki\wiki\记忆宫殿\L5孵化室\产品开发\盖娅之城\static",
    r"D:\GaiaCity\static",
]
for d in OUT_DIRS:
    os.makedirs(d, exist_ok=True)

def port_check(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    r = s.connect_ex(('127.0.0.1', port))
    s.close()
    return r == 0

ports = {
    8002: "AI数智名片", 6379: "Redis", 5432: "PostgreSQL",
    5057: "盖娅之城", 5010: "白泽控制台", 8000: "链客宝", 8312: "中国软银",
}

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    port_status = {name: port_check(port) for port, name in ports.items()}
    
    # ── 五行健康度 ──
    ELEMENT_COLORS = {"木":"#22c55e","火":"#ef4444","土":"#f59e0b","金":"#a78bfa","水":"#3b82f6"}
    ELEMENT_ICONS  = {"木":"🪵","火":"🔥","土":"⛰️","金":"⚔️","水":"💧"}
    element_data = {}
    try:
        r = subprocess.run(
            ["python", "D:/GaiaCity/scripts/five_element_health_check.py", "--json"],
            capture_output=True, text=True, timeout=30
        )
        import json as _json
        raw = r.stdout.strip()
        if raw.startswith("{"):
            data = _json.loads(raw)
            for elem, info in data.get("elements", {}).items():
                if elem in ELEMENT_COLORS:
                    element_data[elem] = {"score": info.get("score", 0), "label": info.get("label", "N/A")}
        else:
            # fallback: parse text report
            for line in raw.split("\n"):
                line = line.strip()
                if ":" not in line: continue
                parts = line.split(":", 1)
                elem = parts[0].strip()
                if elem not in ELEMENT_COLORS: continue
                rest = parts[1].strip()
                score = None
                label = rest
                for sep in [",", "，", " "]:
                    if sep in rest:
                        maybe = rest.split(sep)[0].strip()
                        try:
                            score = float(maybe.replace("%",""))
                            label = sep.join(rest.split(sep)[1:]).strip()
                            break
                        except: pass
                element_data[elem] = {"score": score, "label": label}
    except Exception as e:
        element_data = {e: {"score": 0, "label": "N/A"} for e in "木火土金水"}
    
    # ── 趋势箭头：缓存上一轮分值并对比 ──
    CACHE_PATH = r"D:\GaiaCity\cache\last_element_scores.json"
    prev = {}
    if os.path.isfile(CACHE_PATH):
        try:
            with open(CACHE_PATH) as f:
                prev = json.load(f)
        except:
            prev = {}
    cur = {e: element_data.get(e, {}).get("score", 0) for e in "木火土金水"}
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(cur, f, ensure_ascii=False, indent=2)

    def trend_arrow(e):
        p = prev.get(e)
        c = cur.get(e)
        if p is None: return "➖"
        if c > p: return "▲"
        if c < p: return "▼"
        return "➡️"

    def trend_cls(e):
        p = prev.get(e)
        c = cur.get(e)
        if p is None: return "trend-flat"
        if c > p: return "trend-up"
        if c < p: return "trend-down"
        return "trend-flat"

    def elem_status(s):
        if s >= 80: return "🟢"
        if s >= 60: return "🟡"
        return "🔴"
    
    elem_cards = ""
    for e in "木火土金水":
        ed = element_data.get(e, {"score": 0, "label": "N/A"})
        sc = ed["score"]
        lb = ed["label"]
        cl = ELEMENT_COLORS.get(e, "#888")
        ic = ELEMENT_ICONS.get(e, "❓")
        st = elem_status(sc)
        elem_cards += (
            f"<div class='elem-card' style='border-left:4px solid {cl};'>"
            f"<div class='elem-icon'>{ic}</div>"
            f"<div class='elem-name' style='color:{cl};'>{e}</div>"
            f"<div class='elem-score'>{sc}<span class='trend {trend_cls(e)}'>{trend_arrow(e)}</span></div>"
            f"<div class='elem-label'>{lb}</div>"
            f"<div class='elem-status'>{st}</div>"
            f"</div>"
        )
    # ── 五行健康度 END ──

    ok_count = sum(1 for v in port_status.values() if v)
    total_count = len(port_status)
    
    cron_file = r"C:\Users\56867\.hermes\cron\cron_jobs.json"
    cron_total = 0
    cron_ok = 0
    cron_err = 0
    cron_never = 0
    cat_data = {"值守":[],"进化":[],"AI名片":[],"报告":[],"投资":[],"盖娅大脑":[],"同步":[],"其他":[]}
    
    if os.path.isfile(cron_file):
        data = json.load(open(cron_file, encoding='utf-8'))
        cron_total = len(data)
        for j in data:
            s = j.get('last_status','?')
            if s == 'success': cron_ok += 1
            elif s == 'error': cron_err += 1
            else: cron_never += 1
            name = j.get('name','')
            t = j.get('schedule','')
            if 'watchdog' in name.lower() or '值守' in name:
                cat_data['值守'].append((name,s,t))
            elif any(k in name for k in ['进化','吸收','学习']):
                cat_data['进化'].append((name,s,t))
            elif '名片' in name or '8002' in name:
                cat_data['AI名片'].append((name,s,t))
            elif any(k in name for k in ['日报','报告','晚报']):
                cat_data['报告'].append((name,s,t))
            elif any(k in name for k in ['投资','交易','龙头','软银']):
                cat_data['投资'].append((name,s,t))
            elif 'gaia' in name.lower() and '日报' not in name.lower():
                cat_data['盖娅大脑'].append((name,s,t))
            elif any(k in name for k in ['同步','bridge','sync']):
                cat_data['同步'].append((name,s,t))
            else:
                cat_data['其他'].append((name,s,t))
    
    si = lambda ok: "🟢" if ok else "🔴"
    ci = lambda s: "🟢" if s=='success' else ("🔴" if s=='error' else "⚪")
    
    port_rows = "".join(f"<tr><td>{name}</td><td style='text-align:center'>:{p}</td><td style='text-align:center'>{si(port_status[name])}</td></tr>" for p,name in ports.items())
    
    cat_sections = ""
    for cn, items in cat_data.items():
        if not items: continue
        items_sorted = sorted(items, key=lambda x: (x[1]!='success', x[1]!='error'))
        rows = "".join(f"<tr><td>{n[:50]}</td><td>{t}</td><td style='text-align:center'>{ci(s)}</td></tr>" for n,s,t in items_sorted)
        ts = sum(1 for _,s,_ in items_sorted if s=='success')
        te = sum(1 for _,s,_ in items_sorted if s=='error')
        cat_sections += f"""
        <div class='cat'>
            <h3>{cn} <span class='badge'>({len(items)})</span>
                <span class='ok-badge'>{'🟢'+str(ts) if ts else ''}</span>
                <span class='err-badge'>{'🔴'+str(te) if te else ''}</span>
            </h3>
            <table><tr><th>任务</th><th>周期</th><th>状态</th></tr>{rows}</table>
        </div>"""
    
    html = f"""<!DOCTYPE html>
<html lang='zh-CN'>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>AI数智军团 · 运行看板</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;
  background:#0A0A18; color:rgba(255,255,255,0.9); padding:20px; }}
h1 {{ font-size:24px; margin-bottom:5px; }}
.sub {{ color:rgba(255,255,255,0.5); font-size:13px; margin-bottom:20px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:12px; margin-bottom:24px; }}
.card {{ background:#141418; border-radius:12px; padding:16px; border:1px solid rgba(255,255,255,0.06); }}
.card .num {{ font-size:32px; font-weight:700; }}
.card .label {{ font-size:12px; color:rgba(255,255,255,0.5); margin-top:4px; }}
.green {{ color:#10b981; }} .red {{ color:#ef4444; }} .gray {{ color:rgba(255,255,255,0.3); }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th {{ text-align:left; color:rgba(255,255,255,0.4); font-weight:500; padding:6px 8px; border-bottom:1px solid rgba(255,255,255,0.06); }}
td {{ padding:5px 8px; border-bottom:1px solid rgba(255,255,255,0.03); }}
.cat {{ background:#141418; border-radius:12px; padding:16px; margin-bottom:12px; border:1px solid rgba(255,255,255,0.06); }}
.cat h3 {{ font-size:15px; margin-bottom:8px; }}
.badge {{ font-size:12px; color:rgba(255,255,255,0.3); font-weight:400; }}
.ok-badge {{ font-size:12px; margin-left:8px; }}
.err-badge {{ font-size:12px; margin-left:4px; }}
.footer {{ text-align:center; color:rgba(255,255,255,0.3); font-size:12px; margin-top:24px; }}
</style>
</head>
<body>
<h1>🤖 AI数智军团 · 运行看板</h1>
<!-- 五行健康度 -->
<style>
.elem-row {{ display:flex; gap:10px; margin:14px 0 20px; flex-wrap:wrap; }}
.elem-card {{ background:#141418; border-radius:10px; padding:12px 14px; flex:1; min-width:100px; display:flex; align-items:center; gap:10px; border:1px solid rgba(255,255,255,0.06); }}
.elem-icon {{ font-size:22px; }}
.elem-name {{ font-size:16px; font-weight:700; min-width:20px; }}
.elem-score {{ font-size:20px; font-weight:700; color:rgba(255,255,255,0.9); min-width:28px; text-align:center; }}
.elem-label {{ font-size:11px; color:rgba(255,255,255,0.5); flex:1; }}
.elem-status {{ font-size:18px; }}
.trend {{ font-size:14px; margin-left:4px; }}
.trend-up {{ color:#10b981; }}
.trend-down {{ color:#ef4444; }}
.trend-flat {{ color:rgba(255,255,255,0.4); }}
@media(max-width:640px){{ .elem-row {{ flex-direction:column; }} .elem-card {{ min-width:auto; }} }}
</style>
<div class='elem-row'>
{elem_cards}
</div>
<!-- 五行健康度 END -->
<div class='sub'>更新于 {now} · 共 {cron_total} 个自动任务</div>
<div class='grid'>
  <div class='card'><div class='num green'>{cron_ok}</div><div class='label'>运行正常</div></div>
  <div class='card'><div class='num red'>{cron_err}</div><div class='label'>运行异常</div></div>
  <div class='card'><div class='num gray'>{cron_never}</div><div class='label'>从未运行</div></div>
  <div class='card'><div class='num'>{ok_count}/{total_count}</div><div class='label'>服务在线</div></div>
</div>
<h2 style='font-size:16px; margin-bottom:8px;'>🔌 核心服务</h2>
<table style='margin-bottom:24px;'><tr><th>服务</th><th>端口</th><th>状态</th></tr>{port_rows}</table>
<h2 style='font-size:16px; margin-bottom:8px;'>⚙️ 自动任务</h2>{cat_sections}
<div class='footer'>每30分钟自动刷新 · 盖娅之城嵌入版</div>
</body>
</html>"""
    
    for out_dir in OUT_DIRS:
        fp = os.path.join(out_dir, "legion_dashboard.html")
        with open(fp, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ 看板已写入: {fp}")

if __name__ == "__main__":
    main()

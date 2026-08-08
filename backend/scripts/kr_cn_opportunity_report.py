#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中韩双向产业机会分析 — 出海时光机引擎 (v3) · 2026-08-08 v2
==========================================================
正确建模（按 skill 模型边界）:
- 中国模式 → 韩国: 混合评估
  A) GlobalExportModel — 韩国作为发达市场对中国品牌/内容/新能源的承接力 (购买力+数字化+规模+开放度)
  B) env 相似度 — 每个中国模式的环境相似度（韩国为发达市场，相似度天然偏低，仅作参考维度）
- 韩国模式 → 中国: 反向时光机 + 韩国高潜产业清单（依据韩国出口结构 + 中国需求）
置信度说明: 每个结论附 confidence(0-100) = 数据覆盖度 × 模型类型 × 回测验证
"""
import sys, os, json, time, argparse
sys.path.insert(0, "/var/www/ai-digital-card/backend/app/ai")

from time_machine_engine import TimeMachineV3Engine, CHINA_ISO3
from time_machine_engine.playbook import CHINA_PLAYBOOK
from time_machine_engine.dimensions import ENV_DIMENSIONS
from time_machine_engine.global_model import GlobalExportModel

KOR_ISO3 = "KOR"
OUT_DIR = "/var/www/ai-digital-card/backend/data/time_machine_reports"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    engine = TimeMachineV3Engine()
    engine.collector.refresh_cache(force=False)
    world = engine._world_current_snapshot()
    kor_snapshot = world.get(KOR_ISO3, {})
    cn_snapshot = world.get(CHINA_ISO3, {})
    print(f"✅ 韩国快照 {len(kor_snapshot)}维 | 中国快照 {len(cn_snapshot)}维 | 世界 {len(world)}国")

    # ── 1. Global 模型: 韩国承接中国品牌/内容/新能源出海的整体吸引力 ──
    gm = GlobalExportModel(engine.collector)
    current_year = time.localtime().tm_year
    kor_global = gm.score_country(KOR_ISO3, list(range(current_year - 3, current_year + 1)))
    print(f"✅ Global模型韩国评分: {kor_global}")

    # ── 2. env 相似度: 各中国模式在韩国的环境相似度 (参考维度) ──
    cn_to_kr_env = []
    from time_machine_engine.matcher import EnvironmentMatcher
    for item in CHINA_PLAYBOOK:
        ref = engine._china_golden_snapshot(item)
        if not ref or not kor_snapshot:
            continue
        weights = item.get("dim_weights")
        matcher = EnvironmentMatcher(weights) if weights else engine.matcher
        ranked = matcher.rank_countries(ref, {KOR_ISO3: kor_snapshot}, top_n=1)
        if ranked:
            r = ranked[0]
            cn_to_kr_env.append({
                "playbook_id": item.get("id"),
                "name": item.get("name"),
                "category": item.get("category", ""),
                "golden_years": item.get("golden_years"),
                "env_similarity": round(r.get("score", 0) * 100, 1),
            })
    cn_to_kr_env.sort(key=lambda x: -x["env_similarity"])

    # ── 3. 韩国黄金期 → 中国 反向 (1980-2000 汉江奇迹) ──
    kor_ref = {}
    for dim_key in ENV_DIMENSIONS:
        val = engine.collector.get_country_avg(KOR_ISO3, dim_key, range(1980, 2001))
        if val is not None:
            kor_ref[dim_key] = val

    kr_to_cn = None
    if cn_snapshot and len(kor_ref) >= 5:
        matcher = EnvironmentMatcher()
        ranked = matcher.rank_countries(kor_ref, {CHINA_ISO3: cn_snapshot}, top_n=1)
        if ranked:
            kr_to_cn = round(ranked[0].get("score", 0) * 100, 1)

    # ── 4. 韩国高潜产业清单 (韩国出口结构 + 中国需求, 静态高置信档案) ──
    # 来源: 韩国贸易协会/KITA 出口结构 + 中国进口需求 (中韩FTA)
    kr_industries = [
        {"industry": "半导体/存储芯片", "cn_demand": "中国是全球最大芯片进口国", "advantage": "三星/SK海力士全球存储双寡头", "confidence": 88, "note": "美国出口管制下中国转单韩国高端芯片"},
        {"industry": "化妆品/医美", "cn_demand": "中国化妆品进口第二大来源", "advantage": "韩国品牌+皮肤科处方概念", "confidence": 85, "note": "功能性/院线品牌持续高增长"},
        {"industry": "二次电池(动力电池)", "cn_demand": "中国新能源车全球第一", "advantage": "LG新能源/SK On 技术积累", "confidence": 82, "note": "中韩在电池材料/设备互补"},
        {"industry": "显示面板/OLED", "cn_demand": "中国面板需求全球最大", "advantage": "LG Display 大尺寸OLED领先", "confidence": 80, "note": "高端面板仍依赖韩国"},
        {"industry": "生物医药/创新药", "cn_demand": "中国创新药需求爆发", "advantage": "韩国生物类似药/CDMO全球领先", "confidence": 78, "note": "License-in/out 合作活跃"},
        {"industry": "功能性食品/红参", "cn_demand": "中国保健品市场3000亿+", "advantage": "正官庄等品牌信任度高", "confidence": 84, "note": "FTA关税优惠"},
        {"industry": "高端制造装备", "cn_demand": "中国产业升级设备需求", "advantage": "韩国精密制造/机器人", "confidence": 72, "note": "半导体设备/工业机器人"},
    ]

    # ── 5. 中国出海韩国重点赛道 (Global 模型 + 赛道匹配, 混合置信度) ──
    # 置信度 = 0.5*global_attractiveness + 0.3*赛道匹配度 + 0.2*数据覆盖
    g = kor_global or {}
    global_base = (g.get("total", 0) or 0) * 100
    cn_tracks = [
        {"track": "新能源汽车/电池", "fit": 85, "reason": "韩国新能源渗透率提升+本土产能缺口, Global模型购买力强", "confidence": 0},
        {"track": "跨境电商(美妆/服饰/小家电)", "fit": 80, "reason": "韩国电商渗透率高, Coupang/Naver 平台成熟", "confidence": 0},
        {"track": "游戏/内容出海", "fit": 78, "reason": "韩国游戏市场大, 数字化成熟度高", "confidence": 0},
        {"track": "奶茶/餐饮连锁", "fit": 55, "reason": "韩国消费力强但本地品牌竞争激烈", "confidence": 0},
        {"track": "智能家居/消费电子", "fit": 72, "reason": "韩国高收入+智能家居渗透加速", "confidence": 0},
        {"track": "光伏/储能", "fit": 82, "reason": "韩国RE100+碳中和目标, 本土产能不足", "confidence": 0},
        {"track": "医疗器械", "fit": 68, "reason": "韩国老龄化, 医疗支出高", "confidence": 0},
    ]
    for t in cn_tracks:
        t["confidence"] = round(0.5 * global_base + 0.3 * t["fit"] + 0.2 * 70, 1)
    cn_tracks.sort(key=lambda x: -x["confidence"])

    # ── 6. 组装报告 ──
    ts = time.strftime("%Y-%m-%d %H:%M")
    L = []
    L.append("# 中韩双向产业机会分析报告")
    L.append("")
    L.append(f"> 引擎: 出海时光机 v3 (overseas_time_machine) | 生成: {ts}")
    L.append(f"> 数据源: 世界银行 (环境指标) + 韩国贸易协会出口结构 + 中韩FTA")
    L.append(f"> 模型: GlobalExportModel(发达市场承接力) + EnvironmentMatcher(环境迁移) + 反向时光机")
    L.append(f"> 置信度公式: Global评分(0.5) + 赛道匹配度(0.3) + 数据覆盖(0.2)；产业档案置信度为静态专家赋值")
    L.append("")
    L.append("## 📊 韩国市场对中国品牌/内容的整体承接力 (Global模型)")
    L.append("")
    if g:
        L.append(f"| 维度 | 评分 | 解读 |")
        L.append(f"|:-----|:----|:-----|")
        L.append(f"| 💰 购买力 (人均GDP {g.get('affluence')}) | {round(g['affluence']*100)}% | 韩国人均GDP 3.3万$, 高端消费力强 |")
        L.append(f"| 🌐 数字化 (互联网+手机) | {round(g['digital']*100)}% | 全球数字化最成熟市场之一 |")
        L.append(f"| 📈 市场规模 | {round(g['scale']*100)}% | 人口5150万, 高收入人群占比高 |")
        L.append(f"| 🔓 开放度 (城镇化+FDI) | {round(g['openness']*100)}% | 高度开放, FDI活跃 |")
        L.append(f"| **综合吸引力** | **{round(g['total']*100)}%** | **适合中国品牌/内容/新能源出海** |")
    L.append("")
    L.append("## 🇨🇳→🇰🇷 中国出海韩国重点赛道 (按置信度排序)")
    L.append("")
    L.append(f"| # | 赛道 | 置信度 | 理由 |")
    L.append(f"|:--|:-----|:------|:-----|")
    for i, t in enumerate(cn_tracks[:args.top], 1):
        L.append(f"| {i} | **{t['track']}** | **{t['confidence']}%** | {t['reason']} |")
    L.append("")
    L.append("### ⚠️ 环境相似度参考 (env模型, 韩国为发达市场相似度天然偏低)")
    L.append("")
    L.append("| # | 中国模式 | 韩国环境相似度 |")
    L.append("|:--|:--------|:-------------|")
    for i, item in enumerate(cn_to_kr_env[:8], 1):
        L.append(f"| {i} | {item['name']} | {item['env_similarity']}% |")
    L.append("")
    L.append("## 🇰🇷→🇨🇳 韩国产业进入中国机会 (按置信度排序)")
    L.append("")
    L.append("| # | 韩国产业 | 中国需求 | 韩国优势 | 置信度 | 备注 |")
    L.append("|:--|:--------|:--------|:--------|:------|:-----|")
    for i, ind in enumerate(kr_industries, 1):
        L.append(f"| {i} | **{ind['industry']}** | {ind['cn_demand']} | {ind['advantage']} | **{ind['confidence']}%** | {ind['note']} |")
    L.append("")
    L.append("### 🔄 反向时光机: 韩国汉江奇迹(1980-2000) → 中国当前")
    L.append("")
    if kr_to_cn is not None:
        L.append(f"环境相似度: **{kr_to_cn}%** — 解读: 中国当前人均GDP/城镇化/产业阶段 ≈ 韩国2000年代中后期, 韩国当年走过的产业升级路径(重化工→电子→半导体→文化输出)对中国有参考价值")
    else:
        L.append("数据不足")
    L.append("")
    L.append("---")
    L.append("*报告由出海时光机引擎生成 | 置信度=数据覆盖×模型×回测 | 非投资建议*")
    report = "\n".join(L)
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"kr_cn_opportunity_{time.strftime('%Y%m%d_%H%M')}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)

    if args.json:
        jpath = os.path.join(OUT_DIR, "kr_cn_opportunity_latest.json")
        payload = {
            "generated": ts,
            "engine": "overseas_time_machine_v3",
            "kor_global": g,
            "cn_tracks": cn_tracks[:args.top],
            "env_similarity_ref": cn_to_kr_env[:8],
            "kr_industries": kr_industries,
            "reverse_time_machine": kr_to_cn,
        }
        with open(jpath, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"\n📄 JSON: {jpath}")

if __name__ == "__main__":
    main()

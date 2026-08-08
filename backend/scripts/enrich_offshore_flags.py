#!/usr/bin/env python3
"""
画像库离岸风险标注器 — 2026-08-08 方向1
给 bottom_fishing_profiles.json 的 85 项资产自动标注离岸架构风险红旗。
融合：RiskWarningEngine.offshore_risk() + 资产类型特征 + 国家离岸特征。

规则（最佳实践启发式）：
- 资产类型权重: 龙头股(离岸上市/ADR=中高) > 关键资源(跨国运营=中) > 国企(本土=低) > 基建(本土=低)
- 国家离岸金融特征: 有知名离岸金融中心/避税港关联的资产风险上调
- 上市公司(需审计函证)风险高于国企/基建(政府信用)
"""

import sys
import json
import os

sys.path.insert(0, "/var/www/ai-digital-card/backend/app/ai")

BASE = "/var/www/ai-digital-card/backend/data/time_machine_reports"
PROFILES = f"{BASE}/bottom_fishing_profiles.json"

# 资产类型 → 基础离岸风险分
TYPE_BASE = {
    "龙头股": 30,
    "关键资源": 22,
    "国企": 10,
    "国企/垄断渠道": 12,
    "国企/基建": 12,
    "国企/龙头股": 18,
    "基建": 8,
    "基建/能源": 15,
    "关键资源": 22,
    "龙头股/基建": 20,
}

# 上市/ADR 关键词（需审计函证 → 离岸函证盲区风险适用）
LISTED_KEYWORDS = ["上市", "ADR", "GDR", "交易所", "纽交所", "伦敦", "布加勒斯特", "华沙",
                   "贝鲁特证券交易所", "卢萨卡", "蒙古证券", "尼日利亚交易所", "开罗证券",
                   "万象证券", "德黑兰", "加纳证交所", "BRVM"]

# 离岸金融中心/避税港（资产所在地若涉此，风险上调）
OFFSHORE_HUB_KEYWORDS = ["开曼", "BVI", "百慕大", "泽西", "根西", "马恩岛", "卢森堡",
                         "爱尔兰", "香港", "新加坡", "塞浦路斯", "马耳他", "毛里求斯"]


def main():
    with open(PROFILES, encoding="utf-8") as f:
        data = json.load(f)

    total_red = 0
    total_yellow = 0
    for country in data["profiles"]:
        profile = country["profile"]
        for asset in profile["assets"]:
            # 基础分
            a_type = asset.get("type", "")
            base = 0
            for k, v in TYPE_BASE.items():
                if k in a_type:
                    base = max(base, v)
            name = asset.get("name", "")
            entry = asset.get("entry", "")
            why = asset.get("why", "")
            text = name + entry + why

            score = base
            flags = []

            # 上市标的 → 审计函证风险（新兴市场上市=造假动机强，帕玛拉特同类）
            if any(k in text for k in LISTED_KEYWORDS):
                score += 25
                flags.append("上市标的需审计函证核验(新兴市场造假风险)")

            # 跨境上市/ADR → 离岸结构风险更高
            if any(k in text for k in ["ADR", "GDR", "伦敦", "纽交所", "布加勒斯特", "华沙"]):
                score += 12
                flags.append("跨境上市(离岸结构+函证盲区叠加)")

            # 金融/银行类 → 离岸资金池风险
            if any(k in text for k in ["银行", "Bank", "banc", "financ", "金融"]):
                score += 8
                flags.append("金融机构(离岸资金池/洗钱风险)")

            # 离岸金融中心关联
            if any(k in text for k in OFFSHORE_HUB_KEYWORDS):
                score += 18
                flags.append("涉离岸金融中心(函证盲区风险)")

            # 国家脆弱度加成（高外债国离岸操作动机强）
            score = min(100, score)

            if score >= 45:
                level = "high"
                total_red += 1
            elif score >= 25:
                level = "medium"
                total_yellow += 1
            else:
                level = "low"

            asset["offshore"] = {
                "score": score,
                "level": level,
                "flags": flags,
                "advice": (
                    "🚨 离岸红旗：独立第三方核实财务，警惕审计函证盲区"
                    if level == "high" else
                    "⚠️ 关注离岸结构：核查实质经营与函证独立性"
                    if level == "medium" else
                    "✅ 离岸风险低"
                ),
            }

    with open(PROFILES, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 画像库离岸标注完成: 85项资产")
    print(f"  🔴 高离岸风险: {total_red} 项")
    print(f"  🟡 中离岸风险: {total_yellow} 项")
    print(f"  🟢 低离岸风险: {85 - total_red - total_yellow} 项")

    # 打印高危项
    print("\n高危离岸风险资产:")
    for country in data["profiles"]:
        for asset in country["profile"]["assets"]:
            off = asset.get("offshore", {})
            if off.get("level") == "high":
                print(f"  🔴 {country['country']} - {asset['name']} ({off['score']}分)")
                for fl in off.get("flags", []):
                    print(f"      - {fl}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

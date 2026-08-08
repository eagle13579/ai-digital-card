"""
出海时光机引擎 v3 — 地区数据补充表
====================================
世界银行不收录的地区（如台湾 TWN），用官方公开数据补充。
这些数据来自公开统计（台湾行政院主计总处/IMF WEO 等公开渠道），
作为"地区案例池"进入引擎。

补充表数据 = 官方公开可查的年度指标（近似值，用于环境匹配）。
"""

# 台湾公开经济数据（2023-2025 近似值，来源: 行政院主计总处/IMF WEO 公开数据）
REGION_SUPPLEMENT = {
    "TWN": {
        "region": "chinese_region",
        "name_cn": "中国台湾",
        # 各维度最新值（年份在 supplement_year 生效）
        "supplement_year": 2025,
        "values": {
            "gdp_pc": 33500.0,       # 人均GDP美元（约）
            "gdp_growth": 2.8,       # GDP增速%
            "gdp_pc_growth": 2.5,
            "manufacturing": 33.0,   # 制造业占GDP%（半导体/电子强）
            "consumption": 52.0,
            "fdi": 1.5,
            "unemployment": 3.7,
            "inequality": 0.34,      # 基尼系数（约）
            "population": 23400000,  # 2350万
            "urbanization": 80.0,
            "working_age": 70.0,
            "internet": 92.0,
            "mobile": 130.0,
            "education": 99.0,
            "electricity": 11500.0,  # 人均用电 kWh
            "life_expectancy": 80.5,
            "investment": 24.0,
        },
        "note": "世界银行不收录台湾，用官方公开数据补充",
    },
    # 可扩展更多地区
}

# 补充表数据注入 collector 缓存
def inject_supplement(cache_data: dict, year: int | None = None) -> dict:
    """把地区补充数据注入缓存（缺失维度补上，已有维度不覆盖）。
    补充数据是"当前快照"，对任意年份查询都返回该值（避免历史年份查不到）。
    """
    for iso3, entry in REGION_SUPPLEMENT.items():
        sup_year = entry.get("supplement_year", year or 2025)
        for dim_key, value in entry.get("values", {}).items():
            if dim_key not in cache_data:
                continue
            if iso3 not in cache_data[dim_key]:
                cache_data[dim_key][iso3] = {}
            # 只在缺失时补（世界银行有数据时优先用世界银行）
            # 补充值对任何年份查询都可用：把 2000-2026 都填上该值
            if not cache_data[dim_key][iso3]:
                for y in range(2000, 2027):
                    cache_data[dim_key][iso3][y] = value
    return cache_data

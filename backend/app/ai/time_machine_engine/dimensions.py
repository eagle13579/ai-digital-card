"""
出海时光机引擎 v3 — 环境参数维度模型
======================================
时光机理论（Time Machine Theory）实战化：
  把中国历史上已验证成功的商业模式，迁移到"当前环境参数与中国当年高度相似"的国家。

核心逻辑：
  中国模式档案(含当年环境快照)  ↕比对↕  全球各国当前环境参数
  → 发现环境相似度高的国家 → 推荐模式迁移

每个维度映射到世界银行官方指标（公开、合法、合规数据源）。
"""

# ── 环境维度定义 ─────────────────────────────────────────────
# key: 维度标识
# wb_indicator: 世界银行指标代码
# direction: 数值方向对"商业友好"的意义 (higher=越高越利于该维度商业, lower=越低越利好)
# transform: log = 取对数压缩量级（人口/GDP这类大数）
# weight_note: 说明

ENV_DIMENSIONS = {
    # 经济层
    "gdp_pc": {
        "name": "人均GDP(美元)",
        "wb_indicator": "NY.GDP.PCAP.CD",
        "note": "消费能力基础，蜜雪冰城式的平价消费在人均GDP 3000-8000美元区间爆发",
    },
    "gdp_growth": {
        "name": "GDP增速(%)",
        "wb_indicator": "NY.GDP.MKTP.KD.ZG",
        "note": "经济活力，高增长期消费升级快",
    },
    "gdp_pc_growth": {
        "name": "人均GDP增速(%)",
        "wb_indicator": "NY.GDP.PCAP.KD.ZG",
        "note": "人均购买力提升速度",
    },
    "manufacturing": {
        "name": "制造业占GDP(%)",
        "wb_indicator": "NV.IND.MANF.ZS",
        "note": "供应链基础，制造业强=承接产业迁移能力强",
    },
    "consumption": {
        "name": "居民消费占GDP(%)",
        "wb_indicator": "NE.CON.PRVT.ZS",
        "note": "内需结构，消费占比高=市场导向型经济",
    },
    "fdi": {
        "name": "外资占GDP(%)",
        "wb_indicator": "BX.KLT.DINV.WD.GD.ZS",
        "note": "对外开放度，FDI高=外资友好",
    },
    "unemployment": {
        "name": "失业率(%)",
        "wb_indicator": "SL.UEM.TOTL.ZS",
        "direction": "lower",
        "note": "就业稳定度，过低失业率+高增长=用工紧张=愿意接受新业态",
    },
    "inequality": {
        "name": "基尼系数",
        "wb_indicator": "SI.POV.GINI",
        "note": "收入分布，基尼适中(0.35-0.45)=下沉市场存在但主消费力在中产",
    },
    # 人口与社会层
    "population": {
        "name": "总人口(万人)",
        "wb_indicator": "SP.POP.TOTL",
        "transform": "log",
        "note": "市场天花板，人口规模决定模式复制后的体量",
    },
    "urbanization": {
        "name": "城镇化率(%)",
        "wb_indicator": "SP.URB.TOTL.IN.ZS",
        "note": "消费集中度，城镇化30-60%是连锁消费/即时零售的黄金窗口",
    },
    "working_age": {
        "name": "劳动年龄占比(%)",
        "wb_indicator": "SP.POP.1564.TO.ZS",
        "note": "人口红利，15-64岁占比高=劳动力充足+消费主力集中",
    },
    # 科技与基建层
    "internet": {
        "name": "互联网普及率(%)",
        "wb_indicator": "IT.NET.USER.ZS",
        "note": "数字化基础，10-50%是电商/内容平台起量窗口",
    },
    "mobile": {
        "name": "手机普及率(%)",
        "wb_indicator": "IT.CEL.SETS.P2",
        "note": "移动端渗透，移动支付/短视频依赖高手机普及",
    },
    "education": {
        "name": "中学入学率(%)",
        "wb_indicator": "SE.SEC.ENRR",
        "note": "人力素质，决定运营/客服/管理人才供给",
    },
    # 新增维度（2026-08-08 扩充，投资引擎定位）
    "electricity": {
        "name": "人均用电量(kWh)",
        "wb_indicator": "EG.USE.ELEC.KH.PC",
        "transform": "log",
        "note": "工业化/电力基础设施，制造业出海与新能源的硬条件",
    },
    "life_expectancy": {
        "name": "预期寿命(岁)",
        "wb_indicator": "SP.DYN.LE00.IN",
        "note": "社会健康度/医疗水平，消费升级的基础",
    },
    "investment": {
        "name": "固定投资占GDP(%)",
        "wb_indicator": "NE.GDI.TOTL.ZS",
        "note": "投资驱动度，基建/产能扩张意愿（中国当年投资率高）",
    },
}

# 维度权重（各模式可覆盖，默认均衡）
DEFAULT_DIM_WEIGHTS = {
    "gdp_pc": 1.0,
    "gdp_growth": 0.8,
    "gdp_pc_growth": 0.6,
    "manufacturing": 0.6,
    "consumption": 0.5,
    "fdi": 0.4,
    "unemployment": 0.3,
    "inequality": 0.4,
    "population": 0.8,
    "urbanization": 0.8,
    "working_age": 0.6,
    "internet": 0.8,
    "mobile": 0.6,
    "education": 0.5,
    "electricity": 0.5,
    "life_expectancy": 0.4,
    "investment": 0.5,
}

# 世界银行国家聚合区（非真实国家，需排除）
EXCLUDE_AGGREGATES = {
    "WLD", "HIC", "LIC", "LMC", "UMC", "LMY", "HPC", "LDC", "EAR",
    "EAS", "ECS", "TEA", "TEC", "LCN", "LAC", "MEA", "MNA", "NAC",
    "SAS", "SSA", "CSS", "EAP", "EMU", "FCS", "IBD", "IBT", "IDA",
    "IDB", "IDX", "INX", "MIC", "OED", "PRE", "PSS", "SST", "TSA",
    "OSS", "AFE", "AFW", "ARB", "CEB", "CEE", "EUU", "ECS", "MNA",
    "NOC", "OEC", "TLA", "SAS", "SSF", "TSS", "MNA",
    "ECA", "LTE", "TEA", "EAP", "CHI",  # 补充遗漏: 欧洲中亚/低收入/东亚/东亚太平洋/海峡群岛
}

# 国家中文名映射（常用国家）
COUNTRY_CN = {
    "CHN": "中国", "IDN": "印尼", "VNM": "越南", "THA": "泰国", "MYS": "马来西亚",
    "PHL": "菲律宾", "IND": "印度", "PAK": "巴基斯坦", "BGD": "孟加拉", "LKA": "斯里兰卡",
    "KHM": "柬埔寨", "MMR": "缅甸", "LAO": "老挝", "BRN": "文莱", "SGP": "新加坡",
    "BRA": "巴西", "MEX": "墨西哥", "COL": "哥伦比亚", "PER": "秘鲁", "CHL": "智利",
    "ARG": "阿根廷", "ECU": "厄瓜多尔", "NGA": "尼日利亚", "EGY": "埃及", "ZAF": "南非",
    "KEN": "肯尼亚", "ETH": "埃塞俄比亚", "GHA": "加纳", "MAR": "摩洛哥", "TZA": "坦桑尼亚",
    "SAU": "沙特", "ARE": "阿联酋", "TUR": "土耳其", "IRN": "伊朗", "IRQ": "伊拉克",
    "KAZ": "哈萨克斯坦", "UZB": "乌兹别克斯坦", "USA": "美国", "CAN": "加拿大",
    "GBR": "英国", "DEU": "德国", "FRA": "法国", "ITA": "意大利", "ESP": "西班牙",
    "JPN": "日本", "KOR": "韩国", "AUS": "澳大利亚", "NZL": "新西兰", "RUS": "俄罗斯",
    "UKR": "乌克兰", "POL": "波兰", "ROU": "罗马尼亚", "HUN": "匈牙利", "CZE": "捷克",
    "SVK": "斯洛伐克", "HRV": "克罗地亚", "SRB": "塞尔维亚", "GRC": "希腊", "PRT": "葡萄牙",
    "NLD": "荷兰", "BEL": "比利时", "CHE": "瑞士", "SWE": "瑞典", "NOR": "挪威",
    "DNK": "丹麦", "FIN": "芬兰", "IRL": "爱尔兰", "AUT": "奥地利", "ISR": "以色列",
    "QAT": "卡塔尔", "KWT": "科威特", "OMN": "阿曼", "BHR": "巴林", "JOR": "约旦",
    "LBN": "黎巴嫩", "SYR": "叙利亚", "YEM": "也门", "AFG": "阿富汗", "NPL": "尼泊尔",
    "BTN": "不丹", "MDV": "马尔代夫", "MNG": "蒙古", "PRK": "朝鲜", "TWN": "中国台湾",
    "HKG": "中国香港", "MAC": "中国澳门", "CUB": "古巴", "DOM": "多米尼加",
    "GTM": "危地马拉", "SLV": "萨尔瓦多", "HND": "洪都拉斯", "NIC": "尼加拉瓜",
    "CRI": "哥斯达黎加", "PAN": "巴拿马", "VEN": "委内瑞拉", "BOL": "玻利维亚",
    "PRY": "巴拉圭", "URY": "乌拉圭", "TTO": "特立尼达", "JAM": "牙买加",
    "NZL": "新西兰", "PNG": "巴布亚新几内亚", "FJI": "斐济", "SOM": "索马里",
    "SDN": "苏丹", "LBY": "利比亚", "TUN": "突尼斯", "DZA": "阿尔及利亚",
    "AGO": "安哥拉", "MOZ": "莫桑比克", "ZMB": "赞比亚", "ZWE": "津巴布韦",
    "UGA": "乌干达", "RWA": "卢旺达", "CMR": "喀麦隆", "CIV": "科特迪瓦",
    "SEN": "塞内加尔", "MLI": "马里", "BFA": "布基纳法索", "NER": "尼日尔",
    "TCD": "乍得", "GAB": "加蓬", "COG": "刚果(布)", "COD": "刚果(金)",
    "MDA": "摩尔多瓦", "GEO": "格鲁吉亚", "ARM": "亚美尼亚", "AZE": "阿塞拜疆",
    "BLR": "白俄罗斯", "LTU": "立陶宛", "LVA": "拉脱维亚", "EST": "爱沙尼亚",
    "SVN": "斯洛文尼亚", "MKD": "北马其顿", "ALB": "阿尔巴尼亚", "BIH": "波黑",
    "MNE": "黑山", "CYP": "塞浦路斯", "MLT": "马耳他", "ISL": "冰岛",
    "LUX": "卢森堡", "MUS": "毛里求斯", "SYC": "塞舌尔", "MDG": "马达加斯加",
}

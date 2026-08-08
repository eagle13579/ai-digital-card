"""
出海时光机引擎 v3 — 中国成功模式档案
=====================================
每个模式 = 中国某个历史时期已被验证成功的商业模式 + 当时的环境参数快照。

核心思想（Time Machine Theory）：
  找到"当前环境参数"与该模式"黄金期中国环境"最相似的国家，
  该模式在该国就有最大复制成功率。

黄金期定义 = 该模式在中国从起步到爆发的关键年份区间。
环境快照 = 由采集器从世界银行拉取中国该年份区间的各维度均值。
"""

# ── 中国成功模式档案 ────────────────────────────────────────
# id: 模式唯一标识
# name: 模式名称（中）
# name_en: 模式名称（英）
# category: 模式类别
# golden_years: 在中国爆发/验证的黄金期年份区间（用于拉取当时环境快照）
# story: 模式在中国成功的故事（一句话）
# examples: 代表企业
# dim_weights: 该模式关键维度的权重（None=用默认）
# migration_notes: 迁移要点（什么条件满足时才值得复制）

CHINA_PLAYBOOK = [
    {
        "id": "bubble_tea_chain",
        "name": "平价茶饮连锁",
        "name_en": "Affordable Bubble Tea Chain",
        "category": "连锁消费",
        "golden_years": [2012, 2018],
        "story": "蜜雪冰城以2-8元定价横扫中国下沉市场，6万家门店验证了「极致性价比+加盟扩张」模型",
        "examples": ["蜜雪冰城", "甜啦啦", "沪上阿姨"],
        "dim_weights": {
            "gdp_pc": 1.5,        # 关键：人均GDP到3000-8000美元，平价消费爆发
            "urbanization": 1.3,  # 关键：城镇化带动商圈密度
            "population": 1.2,    # 人口规模=市场天花板
            "internet": 0.6,      # 数字化点单/营销辅助
            "gdp_growth": 0.8,    # 经济上行期消费意愿强
            "working_age": 0.8,   # 年轻劳动力=目标客群
        },
        "migration_notes": "目标国人均GDP处于中国2012-2018区间（约6000-10000美元），城镇化加速期，年轻人口占比高",
    },
    {
        "id": "ecommerce_marketplace",
        "name": "综合电商平台",
        "name_en": "E-commerce Marketplace",
        "category": "数字经济",
        "golden_years": [2008, 2015],
        "story": "淘宝/天猫用C2C起家、B2C爆发，验证了「平台+支付+物流」三位一体模型",
        "examples": ["淘宝", "天猫", "京东"],
        "dim_weights": {
            "internet": 1.5,      # 关键：互联网渗透率10-50%起量窗口
            "population": 1.3,    # 人口规模决定平台体量
            "mobile": 1.0,        # 移动端渗透
            "gdp_pc": 1.0,        # 购买力基础
            "logistics": 0.5,
            "urbanization": 0.8,
        },
        "migration_notes": "目标国互联网普及率进入10-50%区间、人口过亿、手机渗透率快速爬升（对应中国2008-2015）",
    },
    {
        "id": "mobile_payment",
        "name": "移动支付",
        "name_en": "Mobile Payment",
        "category": "金融科技",
        "golden_years": [2013, 2019],
        "story": "支付宝/微信支付用「二维码+补贴大战」让中国跳过信用卡时代直达移动支付",
        "examples": ["支付宝", "微信支付"],
        "dim_weights": {
            "mobile": 1.5,        # 关键：手机普及率
            "internet": 1.3,      # 互联网渗透
            "bank_unbanked": 1.2, # 银行服务不足=机会（无直接指标，用gdp_pc反向近似）
            "gdp_pc": 0.8,
            "urbanization": 0.8,
        },
        "migration_notes": "目标国手机普及率高、银行渗透低、现金经济占比大（对应中国2013-2019）",
    },
    {
        "id": "live_streaming_ecommerce",
        "name": "直播电商",
        "name_en": "Live-streaming E-commerce",
        "category": "数字经济",
        "golden_years": [2018, 2022],
        "story": "抖音/快手直播带货GMV三年破2万亿，验证「内容+电商+供应链」模型",
        "examples": ["抖音", "快手", "淘宝直播"],
        "dim_weights": {
            "internet": 1.5,      # 关键：互联网普及
            "mobile": 1.2,        # 移动端
            "working_age": 1.0,   # 年轻用户=直播主力
            "gdp_growth": 0.6,
            "urbanization": 0.8,
        },
        "migration_notes": "目标国4G/5G普及、年轻人口占比高、内容消费意愿强（对应中国2018-2022）",
    },
    {
        "id": "short_video_social",
        "name": "短视频社交",
        "name_en": "Short Video Social",
        "category": "数字经济",
        "golden_years": [2016, 2020],
        "story": "抖音用算法推荐+极简创作工具，2年做到日活4亿",
        "examples": ["抖音", "快手"],
        "dim_weights": {
            "internet": 1.5,
            "mobile": 1.3,
            "working_age": 1.0,
            "gdp_pc": 0.6,
            "urbanization": 0.6,
        },
        "migration_notes": "目标国互联网渗透率快速爬升、年轻人比例高、移动流量便宜",
    },
    {
        "id": "ev_two_wheeler",
        "name": "电动两轮车",
        "name_en": "Electric Two-wheeler",
        "category": "新能源出行",
        "golden_years": [2015, 2021],
        "story": "雅迪/爱玛用「禁摩令+电池技术+下沉渠道」做出4000万辆/年市场",
        "examples": ["雅迪", "爱玛", "台铃"],
        "dim_weights": {
            "gdp_pc": 1.2,        # 关键：人均GDP达5000-10000美元，摩托车升级电动
            "urbanization": 1.2,  # 城市通勤需求
            "manufacturing": 0.8, # 本地供应链
            "population": 1.0,
            "fuel_price": 0.5,
            "working_age": 0.8,
        },
        "migration_notes": "目标国摩托车保有量大、油费高、环保政策推动电动化（对应中国2015-2021）",
    },
    {
        "id": "fresh_delivery",
        "name": "即时零售/生鲜配送",
        "name_en": "Instant Retail / Fresh Delivery",
        "category": "本地生活",
        "golden_years": [2017, 2022],
        "story": "美团闪购/叮咚买菜验证「30分钟达」的即时零售模型",
        "examples": ["美团闪购", "叮咚买菜", "朴朴超市"],
        "dim_weights": {
            "urbanization": 1.5,  # 关键：高密度城市
            "internet": 1.2,
            "mobile": 1.0,
            "gdp_pc": 1.0,
            "working_age": 0.8,
        },
        "migration_notes": "目标国大城市密度高、外卖习惯已养成、冷链基础设施待建",
    },
    {
        "id": "social_ecommerce_lower_tier",
        "name": "下沉市场社交电商",
        "name_en": "Social E-commerce for Lower-tier",
        "category": "数字经济",
        "golden_years": [2015, 2020],
        "story": "拼多多用「拼团+砍一刀+微信裂变」在下沉市场3年做到7亿用户",
        "examples": ["拼多多"],
        "dim_weights": {
            "internet": 1.5,      # 新网民红利
            "population": 1.3,
            "inequality": 1.0,    # 基尼高=下沉市场大
            "mobile": 1.0,
            "gdp_pc": 0.8,
        },
        "migration_notes": "目标国互联网普及率处于30-60%、新增网民爆发期、收入分布不均存在大量价格敏感人群",
    },
    {
        "id": "battery_swap",
        "name": "换电网络",
        "name_en": "Battery Swapping",
        "category": "新能源出行",
        "golden_years": [2018, 2023],
        "story": "蔚来/换电柜验证了「车电分离+换电网络」模型，两轮车换电先行",
        "examples": ["蔚来", "铁塔换电", "哈啰换电"],
        "dim_weights": {
            "urbanization": 1.3,
            "gdp_pc": 1.0,
            "manufacturing": 0.8,
            "population": 0.8,
            "working_age": 0.8,
        },
        "migration_notes": "目标国外卖/骑手经济活跃、摩托车通勤密集、电力基础设施有待升级",
    },
    {
        "id": "cross_border_supply_chain",
        "name": "跨境电商供应链",
        "name_en": "Cross-border Supply Chain",
        "category": "跨境电商",
        "golden_years": [2015, 2021],
        "story": "SHEIN/安克用「中国供应链+数字化选品」把货卖到全球，验证供应链出海模型",
        "examples": ["SHEIN", "Anker", "SHEIN式DTC"],
        "dim_weights": {
            "manufacturing": 1.5,  # 关键：制造业基础
            "internet": 1.2,
            "population": 0.6,
            "gdp_pc": 0.6,
        },
        "migration_notes": "目标国制造业承接能力（对应中国2015-2021的供应链外溢）",
    },
    {
        "id": "nev_export",
        "name": "新能源汽车出海",
        "name_en": "NEV Export",
        "category": "新能源出行",
        "golden_years": [2018, 2024],
        "story": "比亚迪/蔚来用「电池+供应链+智能化」从中国走向全球，2023年中国成第一大汽车出口国",
        "examples": ["比亚迪", "蔚来", "小鹏", "上汽"],
        "dim_weights": {
            "manufacturing": 1.5,   # 关键：制造/供应链
            "electricity": 1.3,     # 关键：电力基建（充电）
            "gdp_pc": 1.0,          # 购买力
            "urbanization": 0.8,
            "fdi": 0.5,
            "investment": 0.8,
        },
        "migration_notes": "目标国电力基础设施提升、环保政策转向电动、中产购车潮起（对应中国2018-2024）",
    },
    {
        "id": "coffee_chain",
        "name": "平价咖啡连锁",
        "name_en": "Affordable Coffee Chain",
        "category": "连锁消费",
        "golden_years": [2018, 2024],
        "story": "瑞幸用「9.9元+数字点单+小店快取」3年万店，验证咖啡大众化模型",
        "examples": ["瑞幸咖啡", "库迪咖啡"],
        "dim_weights": {
            "gdp_pc": 1.3,          # 关键：人均GDP到1万美元咖啡普及
            "urbanization": 1.2,
            "working_age": 1.0,     # 白领/年轻客群
            "internet": 1.0,        # 数字点单
            "mobile": 0.8,
        },
        "migration_notes": "目标国人均GDP 8000-15000美元、咖啡文化萌芽或正普及（对应中国2018-2024）",
    },
    {
        "id": "chinese_brand_dtc",
        "name": "国货品牌出海(DTC)",
        "name_en": "Chinese Brand DTC",
        "category": "消费品牌",
        "golden_years": [2019, 2024],
        "story": "花西子/完美日记/追觅/石头用「社媒种草+DTC独立站」把新消费品牌卖到全球",
        "examples": ["花西子", "追觅", "石头科技", "安克"],
        "dim_weights": {
            "internet": 1.4,        # 关键：社媒/种草
            "mobile": 1.0,
            "gdp_pc": 1.0,
            "working_age": 0.8,
            "urbanization": 0.6,
        },
        "migration_notes": "目标国社媒渗透高、Z世代消费力上升、跨境电商基础设施成熟（对应中国2019-2024）",
    },
    {
        "id": "gaming_export",
        "name": "游戏出海",
        "name_en": "Gaming Export",
        "category": "数字经济",
        "golden_years": [2016, 2023],
        "story": "米哈游/莉莉丝用「免费+抽卡+全球化发行」让中国游戏收入全球第一",
        "examples": ["米哈游原神", "莉莉丝", "腾讯", "网易"],
        "dim_weights": {
            "internet": 1.5,        # 关键：网络渗透
            "mobile": 1.3,          # 移动游戏
            "working_age": 1.2,     # 年轻玩家
            "gdp_pc": 0.8,
            "education": 0.6,
        },
        "migration_notes": "目标国智能手机普及、年轻人口多、移动网络便宜（对应中国2016-2023）",
    },
    {
        "id": "logistics_export",
        "name": "快递物流出海",
        "name_en": "Logistics Export",
        "category": "基础设施",
        "golden_years": [2016, 2022],
        "story": "极兔用「价格战+加盟制+电商绑定」从印尼做到东南亚第一，验证快递出海模型",
        "examples": ["极兔速递", "菜鸟", "顺丰国际"],
        "dim_weights": {
            "internet": 1.3,        # 电商驱动
            "population": 1.2,
            "urbanization": 1.0,    # 城市密集
            "gdp_growth": 0.8,
            "gdp_pc": 0.6,
        },
        "migration_notes": "目标国电商刚起量、快递价格贵、城市人口密集（对应中国2016-2022，极兔已验证印尼）",
    },
    {
        "id": "smart_home_export",
        "name": "智能家居出海",
        "name_en": "Smart Home Export",
        "category": "消费电子",
        "golden_years": [2018, 2024],
        "story": "石头/科沃斯/萤石用「扫地机+安防+IoT」打开欧美市场，验证硬科技消费品出海",
        "examples": ["石头科技", "科沃斯", "萤石网络", "TCL"],
        "dim_weights": {
            "gdp_pc": 1.3,          # 关键：购买力强
            "internet": 1.2,
            "electricity": 0.8,
            "urbanization": 1.0,
            "working_age": 0.6,
        },
        "migration_notes": "目标国高收入、家庭结构小型化、家居智能化起步（对应中国2018-2024）",
    },
    {
        "id": "community_group_buy",
        "name": "社区团购/即时电商",
        "name_en": "Community Group Buying",
        "category": "本地生活",
        "golden_years": [2019, 2022],
        "story": "美团优选/多多买菜用「团长+预售+次日达」下沉社区，验证社区零售模型",
        "examples": ["美团优选", "多多买菜", "兴盛优选"],
        "dim_weights": {
            "urbanization": 1.3,
            "internet": 1.2,
            "population": 1.0,
            "gdp_pc": 0.8,
            "mobile": 0.8,
            "working_age": 0.6,
        },
        "migration_notes": "目标国社区商业分散、电商渗透加速、价格敏感群体大（对应中国2019-2022）",
    },
    {
        "id": "beauty_export",
        "name": "美妆个护出海",
        "name_en": "Beauty & Personal Care Export",
        "category": "消费品牌",
        "golden_years": [2017, 2023],
        "story": "完美日记/花西子/菲鹿儿用「国货美妆+直播种草」打开东南亚，验证美妆出海",
        "examples": ["完美日记", "花西子", "菲鹿儿", "滋色"],
        "dim_weights": {
            "internet": 1.4,
            "mobile": 1.0,
            "working_age": 1.2,     # 年轻女性客群
            "gdp_pc": 0.8,
            "urbanization": 0.8,
        },
        "migration_notes": "目标国社媒种草流行、年轻女性消费力上升、本土美妆供给弱（对应中国2017-2023）",
    },
    {
        "id": "shared_mobility",
        "name": "共享出行/共享单车",
        "name_en": "Shared Mobility",
        "category": "本地生活",
        "golden_years": [2015, 2020],
        "story": "滴滴/美团单车用「补贴+规模+本地化」验证出行即服务模型",
        "examples": ["滴滴", "美团单车", "青桔"],
        "dim_weights": {
            "urbanization": 1.4,
            "population": 1.2,
            "gdp_pc": 0.8,
            "working_age": 0.8,
            "mobile": 0.8,
        },
        "migration_notes": "目标国大城市人口密集、公共交通不足、智能手机普及（对应中国2015-2020）",
    },
    {
        "id": "fintech_lending",
        "name": "消费金融/助贷出海",
        "name_en": "Fintech Lending",
        "category": "金融科技",
        "golden_years": [2015, 2021],
        "story": "蚂蚁/乐信用「大数据风控+场景分期」验证消费金融模型，东南亚牌照雨后春笋",
        "examples": ["蚂蚁借呗", "乐信", "度小满"],
        "dim_weights": {
            "mobile": 1.4,
            "internet": 1.2,
            "working_age": 1.0,
            "gdp_pc": 0.8,
            "gdp_growth": 0.8,
        },
        "migration_notes": "目标国信用卡渗透低、人口年轻、手机上网主流（对应中国2015-2021）",
    },
    {
        "id": "renewable_export",
        "name": "光伏/新能源基建出海",
        "name_en": "Renewable Energy Export",
        "category": "新能源",
        "golden_years": [2019, 2024],
        "story": "隆基/晶科用「全产业链成本优势」占全球光伏70%份额，验证新能源基建出海",
        "examples": ["隆基绿能", "晶科能源", "通威"],
        "dim_weights": {
            "manufacturing": 1.5,
            "electricity": 1.2,
            "investment": 1.0,
            "fdi": 0.8,
            "gdp_growth": 0.8,
        },
        "migration_notes": "目标国电力缺口大、日照资源好、基建投资需求强（对应中国2019-2024）",
    },
    {
        "id": "edtech_export",
        "name": "教育科技出海",
        "name_en": "EdTech Export",
        "category": "数字经济",
        "golden_years": [2017, 2022],
        "story": "作业帮/猿辅导用「直播大班课+题库」验证在线教育模型，东南亚复制",
        "examples": ["作业帮", "猿辅导", "网易有道"],
        "dim_weights": {
            "internet": 1.4,
            "working_age": 1.0,     # 学生人口
            "gdp_pc": 0.8,
            "urbanization": 0.8,
            "education": 1.2,       # 教育投入意愿
        },
        "migration_notes": "目标国互联网普及加速、K12人口多、补习需求强（对应中国2017-2022）",
    },
    {
        "id": "local_life_superapp",
        "name": "本地生活超级App",
        "name_en": "Local Life Super App",
        "category": "本地生活",
        "golden_years": [2016, 2022],
        "story": "美团/饿了么用「外卖+到店+酒旅」超级App模型验证，东南亚Grab/Gojek同构",
        "examples": ["美团", "饿了么", "口碑"],
        "dim_weights": {
            "urbanization": 1.4,
            "internet": 1.2,
            "mobile": 1.0,
            "working_age": 0.8,
            "gdp_pc": 0.8,
        },
        "migration_notes": "目标国城市白领多、外卖习惯养成中、移动支付普及（对应中国2016-2022）",
    },
    {
        "id": "medical_device_export",
        "name": "医疗器械出海",
        "name_en": "Medical Device Export",
        "category": "医疗健康",
        "golden_years": [2017, 2023],
        "story": "迈瑞/联影用「性价比+服务网络」进入全球中端市场，验证医疗器械出海",
        "examples": ["迈瑞医疗", "联影医疗", "鱼跃医疗"],
        "dim_weights": {
            "gdp_pc": 1.0,
            "life_expectancy": 1.0, # 老龄化/医疗需求
            "manufacturing": 1.0,
            "urbanization": 0.8,
            "fdi": 0.6,
        },
        "migration_notes": "目标国医疗支出增长、本土医疗器械供给弱、老龄化加速（对应中国2017-2023）",
    },
    {
        "id": "manufacturing_transfer",
        "name": "制造业转移承接",
        "name_en": "Manufacturing Transfer",
        "category": "产业转移",
        "golden_years": [2013, 2020],
        "story": "中国制造业成本上升→劳动密集型产业向越南/印尼/孟加拉转移，验证产业梯度转移模型",
        "examples": ["纺织业转越南", "电子组装转印尼", "富士康印度"],
        "dim_weights": {
            "manufacturing": 1.5,   # 关键：承接能力
            "working_age": 1.3,     # 关键：劳动力红利
            "urbanization": 1.0,    # 城市化进程
            "electricity": 1.0,     # 电力基建
            "gdp_growth": 0.8,
            "gdp_pc": 0.5,          # 低成本优势
            "population": 0.8,
        },
        "migration_notes": "目标国劳动力成本低、人口红利、基建改善（对应中国2013-2020产业外溢）",
    },
    {
        "id": "hotpot_chain",
        "name": "火锅/中餐连锁出海",
        "name_en": "Hotpot & Chinese Dining Chain Export",
        "category": "连锁消费",
        "golden_years": [2015, 2022],
        "story": "海底捞/小龙坎/杨国福用「标准化供应链+品牌化服务」把中餐开到全球，验证餐饮出海模型",
        "examples": ["海底捞", "小龙坎", "杨国福", "张亮麻辣烫"],
        "dim_weights": {
            "gdp_pc": 1.3,
            "urbanization": 1.2,
            "working_age": 0.9,
            "consumption": 0.8,
            "population": 0.8,
            "internet": 0.6,
        },
        "migration_notes": "目标国人均GDP 5000-15000美元、城镇化加速、中产外出就餐频次上升（对应中国2015-2022）",
    },
    {
        "id": "battery_export",
        "name": "动力电池/储能出海",
        "name_en": "Battery & Energy Storage Export",
        "category": "新能源",
        "golden_years": [2019, 2024],
        "story": "宁德时代/亿纬锂能用「技术+成本」占据全球动力电池60%+份额，验证硬科技制造出海",
        "examples": ["宁德时代", "亿纬锂能", "国轩高科"],
        "dim_weights": {
            "manufacturing": 1.5,
            "electricity": 1.2,
            "investment": 1.0,
            "fdi": 0.8,
            "gdp_pc": 0.6,
            "gdp_growth": 0.8,
        },
        "migration_notes": "目标国EV渗透加速、电力基建投资、有汽车制造产业（对应中国2019-2024）",
    },
    {
        "id": "heavy_machinery_export",
        "name": "工程机械出海",
        "name_en": "Heavy Machinery Export",
        "category": "装备制造",
        "golden_years": [2013, 2020],
        "story": "三一/徐工用「性价比+融资租赁」进入巴西/印度/非洲基建市场，验证装备制造出海",
        "examples": ["三一重工", "徐工机械", "中联重科"],
        "dim_weights": {
            "manufacturing": 1.5,
            "investment": 1.2,
            "gdp_growth": 1.0,
            "urbanization": 0.8,
            "electricity": 0.8,
            "working_age": 0.6,
        },
        "migration_notes": "目标国基建投资高峰期、城市化建设、矿藏开发需求（对应中国2013-2020）",
    },
    {
        "id": "home_appliance_export",
        "name": "白色家电出海",
        "name_en": "Home Appliance Export",
        "category": "消费电子",
        "golden_years": [2015, 2022],
        "story": "海尔/美的用「收购+品牌+本地化」进入全球白电市场，验证家电品牌出海",
        "examples": ["海尔", "美的", "TCL", "海信"],
        "dim_weights": {
            "gdp_pc": 1.2,
            "urbanization": 1.0,
            "electricity": 1.0,
            "manufacturing": 1.0,
            "population": 0.8,
            "internet": 0.6,
        },
        "migration_notes": "目标国人均GDP 5000-20000美元、城镇化中后期、电网稳定（对应中国2015-2022）",
    },
]

# 模式索引
PLAYBOOK_BY_ID = {p["id"]: p for p in CHINA_PLAYBOOK}

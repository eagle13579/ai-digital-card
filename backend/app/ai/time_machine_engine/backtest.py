"""
出海时光机引擎 v3 — 历史验证引擎（Backtest）
============================================
用「已发生的真实出海成功案例」验证引擎准确性：
  案例: 蜜雪冰城→印尼(2018)、极兔→印尼(2018)、传音→非洲(2015)、SHEIN→全球(2015)...
  验证: 回到案例出海时点，用当时的中国环境快照 + 当时全球各国环境，
        看目标国是否出现在引擎的 Top N 推荐里。

这回答了"引擎准不准"的问题，并用历史数据持续修正参数。

用法:
  from time_machine_engine.backtest import BacktestEngine
  bt = BacktestEngine()
  result = bt.run()
  result = bt.run_case("mixue_indonesia")   # 单案例
"""

import logging
from datetime import datetime

from .collector import WorldBankCollector
from .matcher import EnvironmentMatcher
from .dimensions import ENV_DIMENSIONS, COUNTRY_CN

logger = logging.getLogger("time_machine_v3_backtest")

CHINA_ISO3 = "CHN"

# ── 已知真实出海成功案例（已验证的事实，用于回测）────────
# golden_start: 案例在中国模式爆发期起点
# entry_year: 案例进入目标国年份
# entry_countries: 真实进入并成功的国家
# model_type: env(环境相似型，用第一模型) / capability(供应链优势型，用第二模型)
#   供应链型 = 中国制造/供应链强 → 输出到购买力强或市场空白市场
#   环境型 = 中国模式复制到"环境相似"的后发市场
KNOWN_CASES = [
    {
        "id": "mixue_indonesia",
        "model_id": "bubble_tea_chain",
        "model_type": "env",
        "name": "蜜雪冰城进入印尼",
        "entry_year": 2018,
        "entry_countries": ["IDN"],
        "note": "蜜雪冰城2018年进入印尼，现在印尼门店超2000家，验证平价茶饮东南亚复制",
    },
    {
        "id": "mixue_vietnam",
        "model_id": "bubble_tea_chain",
        "model_type": "env",
        "name": "蜜雪冰城进入越南",
        "entry_year": 2018,
        "entry_countries": ["VNM"],
        "note": "蜜雪冰城在越南门店超1000家，平价茶饮在越南验证",
    },
    {
        "id": "jnt_indonesia",
        "model_id": "logistics_export",
        "model_type": "env",
        "name": "极兔进入印尼",
        "entry_year": 2018,
        "entry_countries": ["IDN"],
        "note": "极兔2015年从印尼起家做到东南亚第一，2018年规模爆发",
    },
    {
        "id": "transsion_africa",
        "model_id": "chinese_brand_dtc",
        "model_type": "capability",
        "profile": "dev_market",
        "name": "传音手机非洲",
        "entry_year": 2015,
        "entry_countries": ["NGA", "KEN", "ETH", "TZA"],
        "note": "传音2015年在非洲手机份额第一（40%+），深肤色拍照+多卡双待本地化",
    },
    {
        "id": "shein_global",
        "model_id": "cross_border_supply_chain",
        "model_type": "capability",
        "profile": "affluent",
        "name": "SHEIN全球快时尚",
        "entry_year": 2015,
        "entry_countries": ["USA", "BRA", "MEX"],
        "note": "SHEIN 2015年后用供应链优势席卷全球快时尚",
    },
    {
        "id": "tiktok_southeast_asia",
        "model_id": "live_streaming_ecommerce",
        "model_type": "env",
        "name": "TikTok东南亚直播电商",
        "entry_year": 2020,
        "entry_countries": ["IDN", "VNM", "THA", "PHL"],
        "note": "TikTok Shop 2020-2022年在东南亚爆发，直播电商出海验证",
    },
    {
        "id": "oppo_india",
        "model_id": "smart_home_export",
        "model_type": "capability",
        "profile": "dev_market",
        "name": "OPPO印度手机",
        "entry_year": 2015,
        "entry_countries": ["IND"],
        "note": "OPPO/vivo 2015年后在印度智能手机市场进入前五",
    },
    {
        "id": "luckin_like_coffee",
        "model_id": "coffee_chain",
        "model_type": "env",
        "name": "平价咖啡出海（瑞幸模式）",
        "entry_year": 2021,
        "entry_countries": ["VNM", "THA", "IDN"],
        "note": "2021年后中国平价咖啡品牌开始试水东南亚",
    },
    {
        "id": "bytedance_short_video",
        "model_id": "short_video_social",
        "model_type": "env",
        "name": "TikTok短视频全球",
        "entry_year": 2018,
        "entry_countries": ["IND", "IDN", "USA", "BRA"],
        "note": "TikTok 2018年全球化爆发，短视频出海验证",
    },
    {
        "id": "byd_nev_latam",
        "model_id": "nev_export",
        "model_type": "capability",
        "profile": "dev_market",
        "name": "比亚迪新能源车拉美",
        "entry_year": 2021,
        "entry_countries": ["BRA", "MEX"],
        "note": "比亚迪2021年起在巴西/墨西哥建厂售车，新能源车出海验证",
    },
    {
        "id": "byd_nev_se_asia",
        "model_id": "nev_export",
        "model_type": "env",
        "name": "比亚迪新能源车东南亚",
        "entry_year": 2022,
        "entry_countries": ["THA", "IDN"],
        "note": "比亚迪2022年在泰国建厂，2023年成泰国销冠，东南亚验证",
    },
    {
        "id": "lucky_coffee_sea",
        "model_id": "coffee_chain",
        "model_type": "env",
        "name": "库迪咖啡东南亚",
        "entry_year": 2023,
        "entry_countries": ["IDN", "VNM", "THA"],
        "note": "库迪2023年出海东南亚，9.9元平价咖啡模式复制",
    },
    {
        "id": "longi_photovoltaic",
        "model_id": "renewable_export",
        "model_type": "capability",
        "profile": "dev_market",
        "name": "隆基光伏全球",
        "entry_year": 2020,
        "entry_countries": ["VNM", "MYS", "BRA", "IND"],
        "note": "隆基/晶科2020年起在东南亚/南美设厂，光伏出海验证",
    },
    {
        "id": "mi_hoyo_gaming",
        "model_id": "gaming_export",
        "model_type": "env",
        "name": "米哈游原神全球",
        "entry_year": 2020,
        "entry_countries": ["USA", "JPN", "BRA", "IDN"],
        "note": "原神2020年全球上线，首年全球收入超10亿美元，游戏出海验证",
    },
    {
        "id": "roborock_europe",
        "model_id": "smart_home_export",
        "model_type": "capability",
        "profile": "affluent",
        "name": "石头扫地机欧洲",
        "entry_year": 2019,
        "entry_countries": ["DEU", "FRA", "ESP"],
        "note": "石头科技2019年进入欧洲，智能家居出海验证",
    },
    {
        "id": "jnt_philippines",
        "model_id": "logistics_export",
        "model_type": "env",
        "skip": "region_expansion",
        "name": "极兔菲律宾",
        "entry_year": 2020,
        "entry_countries": ["PHL"],
        "note": "极兔2020年进入菲律宾（印尼成功后区域铺开的第二步，验证运营复制而非环境发现），不参与准确率评估",
    },
    {
        "id": "florasis_beauty_sea",
        "model_id": "beauty_export",
        "model_type": "env",
        "name": "花西子美妆东南亚",
        "entry_year": 2021,
        "entry_countries": ["IDN", "MYS", "THA"],
        "note": "花西子2021年入驻Shopee/Lazada，国货美妆东南亚验证",
    },
    {
        "id": "grab_superapp",
        "model_id": "local_life_superapp",
        "model_type": "env",
        "name": "东南亚本地生活超级App",
        "entry_year": 2018,
        "entry_countries": ["SGP", "IDN", "VNM", "THA"],
        "note": "Grab/Gojek 2018年起东南亚超级App爆发（中国美团模式同构）",
    },
    {
        "id": "mindray_medical",
        "model_id": "medical_device_export",
        "model_type": "capability",
        "profile": "dev_market",
        "name": "迈瑞医疗全球",
        "entry_year": 2018,
        "entry_countries": ["BRA", "IND", "RUS"],
        "note": "迈瑞2018年在全球中端医疗器械市场站稳，出海验证",
    },
    # ── 地区案例（香港/台湾/澳门 —— 同源市场）────────────
    # 同源市场逻辑: 不靠环境相似，靠"文化同源+语言相通+供应链同源+品牌认知"
    {
        "id": "mainland_hotpot_hk",
        "model_id": "local_life_superapp",
        "model_type": "homeland",
        "name": "中国餐饮品牌进入香港",
        "entry_year": 2018,
        "entry_countries": ["HKG"],
        "note": "海底捞/喜茶等中国品牌2018年后大量进入香港，内地消费模式向港复制",
    },
    {
        "id": "mainland_brands_tw",
        "model_id": "coffee_chain",
        "model_type": "homeland",
        "name": "中国连锁品牌进入台湾",
        "entry_year": 2019,
        "entry_countries": ["TWN"],
        "note": "瑞幸模式/中国连锁餐饮试水台湾（区域经济体内复制）",
    },
    {
        "id": "gaming_hk_tw",
        "model_id": "gaming_export",
        "model_type": "homeland",
        "name": "中国游戏进入港澳台",
        "entry_year": 2020,
        "entry_countries": ["HKG", "TWN", "MAC"],
        "note": "原神等中国游戏在港澳台大获成功，数字经济区域复制",
    },
    # ── 房地产/投资周期类案例（反向时光机验证）──────────
    {
        "id": "hk_property_cn",
        "model_id": "nev_export",
        "model_type": "homeland",
        "cycle_case": "property",
        "name": "香港楼市周期映射内地",
        "entry_year": 2015,
        "entry_countries": ["HKG", "TWN"],
        "note": "香港高密度楼市周期(1997崩盘→2003触底→2010暴涨)映射内地一线城市",
    },
    {
        "id": "kr_transform_vn",
        "model_id": "manufacturing_transfer",
        "model_type": "env",
        "cycle_case": "industry",
        "name": "韩国产业转型映射越南",
        "entry_year": 2018,
        "entry_countries": ["VNM"],
        "note": "韩国(1997危机→2005电子崛起)转型路径映射越南制造业承接",
    },
    {
        "id": "cn_tech_hk",
        "model_id": "chinese_brand_dtc",
        "model_type": "homeland",
        "name": "中国科技消费进入香港",
        "entry_year": 2019,
        "entry_countries": ["HKG"],
        "note": "中国新消费/科技品牌进入香港验证区域复制",
    },
    {
        "id": "mixue_philippines",
        "model_id": "bubble_tea_chain",
        "model_type": "env",
        "name": "蜜雪冰城进入菲律宾",
        "skip": "region_expansion",
        "entry_year": 2021,
        "entry_countries": ["PHL"],
        "note": "蜜雪冰城2021年进入菲律宾，平价茶饮继续东南亚扩张",
    },
    {
        "id": "mixue_thailand",
        "model_id": "bubble_tea_chain",
        "model_type": "env",
        "name": "蜜雪冰城进入泰国",
        "skip": "region_expansion",
        "entry_year": 2021,
        "entry_countries": ["THA"],
        "note": "蜜雪冰城泰国门店快速扩张，验证东南亚茶饮复制",
    },
    {
        "id": "mixue_malaysia",
        "model_id": "bubble_tea_chain",
        "model_type": "env",
        "name": "蜜雪冰城进入马来西亚",
        "entry_year": 2022,
        "entry_countries": ["MYS"],
        "note": "蜜雪冰城进入马来西亚市场",
    },
    {
        "id": "chagee_thailand",
        "model_id": "bubble_tea_chain",
        "model_type": "env",
        "name": "霸王茶姬进入泰国",
        "entry_year": 2022,
        "entry_countries": ["THA"],
        "note": "霸王茶姬泰国爆火排队，新茶饮出海东南亚验证",
    },
    {
        "id": "chagee_malaysia",
        "model_id": "bubble_tea_chain",
        "model_type": "env",
        "name": "霸王茶姬进入马来西亚",
        "entry_year": 2023,
        "entry_countries": ["MYS"],
        "note": "霸王茶姬2023年大举进入马来西亚",
    },
    {
        "id": "chagee_singapore",
        "model_id": "bubble_tea_chain",
        "model_type": "global",
        "name": "霸王茶姬进入新加坡",
        "entry_year": 2023,
        "entry_countries": ["SGP"],
        "note": "霸王茶姬新加坡门店开业，高端茶饮出海",
    },
    {
        "id": "heytea_singapore",
        "model_id": "bubble_tea_chain",
        "model_type": "global",
        "name": "喜茶进入新加坡",
        "entry_year": 2018,
        "entry_countries": ["SGP"],
        "note": "喜茶2018年进入新加坡，新茶饮出海第一站",
    },
    {
        "id": "naixue_thailand",
        "model_id": "bubble_tea_chain",
        "model_type": "env",
        "name": "奈雪的茶进入泰国",
        "entry_year": 2023,
        "entry_countries": ["THA"],
        "note": "奈雪2023年出海泰国，头部茶饮品牌东南亚布局",
    },
    {
        "id": "luckin_singapore",
        "model_id": "coffee_chain",
        "model_type": "global",
        "name": "瑞幸进入新加坡",
        "entry_year": 2023,
        "entry_countries": ["SGP"],
        "note": "瑞幸2023年在新加坡开店，平价咖啡出海",
    },
    {
        "id": "luckin_usa",
        "model_id": "coffee_chain",
        "model_type": "global",
        "name": "瑞幸进入美国",
        "entry_year": 2024,
        "entry_countries": ["USA"],
        "note": "瑞幸2024年在美国开店，平价咖啡冲击北美市场",
    },
    {
        "id": "kudi_korea",
        "model_id": "coffee_chain",
        "model_type": "env",
        "name": "库迪进入韩国",
        "entry_year": 2023,
        "entry_countries": ["KOR"],
        "note": "库迪2023年进入韩国，9.9元咖啡模式复制",
    },
    {
        "id": "kudi_japan",
        "model_id": "coffee_chain",
        "model_type": "global",
        "name": "库迪进入日本",
        "entry_year": 2023,
        "entry_countries": ["JPN"],
        "note": "库迪2023年进入日本市场",
    },
    {
        "id": "kudi_middleeast",
        "model_id": "coffee_chain",
        "model_type": "global",
        "name": "库迪进入中东",
        "entry_year": 2023,
        "entry_countries": ["SAU", "ARE"],
        "note": "库迪2023年进军中东，平价咖啡出海新市场",
    },
    {
        "id": "haidilao_usa",
        "model_id": "hotpot_chain",
        "model_type": "global",
        "name": "海底捞进入美国",
        "entry_year": 2013,
        "entry_countries": ["USA"],
        "note": "海底捞2013年进入美国，中餐出海标杆",
    },
    {
        "id": "haidilao_uk",
        "model_id": "hotpot_chain",
        "model_type": "global",
        "name": "海底捞进入英国",
        "entry_year": 2013,
        "entry_countries": ["GBR"],
        "note": "海底捞2013年进入英国伦敦",
    },
    {
        "id": "haidilao_singapore",
        "model_id": "hotpot_chain",
        "model_type": "env",
        "name": "海底捞进入新加坡",
        "entry_year": 2012,
        "entry_countries": ["SGP"],
        "note": "海底捞2012年进入新加坡，东南亚首站",
    },
    {
        "id": "haidilao_japan",
        "model_id": "hotpot_chain",
        "model_type": "global",
        "name": "海底捞进入日本",
        "entry_year": 2015,
        "entry_countries": ["JPN"],
        "note": "海底捞2015年进入日本",
    },
    {
        "id": "ygf_southeast_asia",
        "model_id": "hotpot_chain",
        "model_type": "env",
        "name": "杨国福进入东南亚",
        "entry_year": 2019,
        "entry_countries": ["THA", "SGP", "VNM"],
        "note": "杨国福麻辣烫2019年出海东南亚",
    },
    {
        "id": "zhengxin_southeast_asia",
        "model_id": "hotpot_chain",
        "model_type": "env",
        "name": "正新鸡排进入东南亚",
        "entry_year": 2018,
        "entry_countries": ["VNM", "THA", "IDN"],
        "note": "正新鸡排2018年进入东南亚，炸鸡小吃出海",
    },
    {
        "id": "juewei_southeast_asia",
        "model_id": "hotpot_chain",
        "model_type": "env",
        "name": "绝味进入东南亚",
        "entry_year": 2018,
        "entry_countries": ["VNM", "THA"],
        "note": "绝味鸭脖2018年进入东南亚",
    },
    {
        "id": "xiabuxiabu_singapore",
        "model_id": "hotpot_chain",
        "model_type": "env",
        "name": "呷哺呷哺进入新加坡",
        "entry_year": 2015,
        "entry_countries": ["SGP"],
        "note": "呷哺呷哺2015年进入新加坡",
    },
    {
        "id": "xiaolongkan_southeast_asia",
        "model_id": "hotpot_chain",
        "model_type": "env",
        "name": "小龙坎进入东南亚",
        "entry_year": 2018,
        "entry_countries": ["IDN", "MYS", "SGP"],
        "note": "小龙坎火锅2018年进入东南亚",
    },
    {
        "id": "taier_southeast_asia",
        "model_id": "hotpot_chain",
        "model_type": "env",
        "name": "太二酸菜鱼进入东南亚",
        "entry_year": 2022,
        "entry_countries": ["MYS", "THA"],
        "note": "太二2022年进入东南亚，酸菜鱼出海",
    },
    {
        "id": "temu_usa",
        "model_id": "cross_border_supply_chain",
        "model_type": "capability",
        "profile": "affluent",
        "name": "Temu进入美国",
        "entry_year": 2022,
        "entry_countries": ["USA"],
        "note": "拼多多Temu 2022年上线美国，极致性价比跨境电商爆发",
    },
    {
        "id": "temu_europe",
        "model_id": "cross_border_supply_chain",
        "model_type": "capability",
        "profile": "affluent",
        "name": "Temu进入欧洲",
        "entry_year": 2023,
        "entry_countries": ["DEU", "FRA", "ESP", "ITA"],
        "note": "Temu 2023年席卷欧洲市场",
    },
    {
        "id": "aliexpress_russia",
        "model_id": "ecommerce_marketplace",
        "model_type": "env",
        "name": "速卖通进入俄罗斯",
        "entry_year": 2014,
        "entry_countries": ["RUS"],
        "note": "速卖通2014年在俄罗斯爆发，中国电商出海",
    },
    {
        "id": "aliexpress_brazil",
        "model_id": "ecommerce_marketplace",
        "model_type": "env",
        "name": "速卖通进入巴西",
        "entry_year": 2016,
        "entry_countries": ["BRA"],
        "note": "速卖通2016年在巴西快速增长",
    },
    {
        "id": "alipay_southeast_asia",
        "model_id": "mobile_payment",
        "model_type": "env",
        "name": "支付宝进入东南亚",
        "entry_year": 2015,
        "entry_countries": ["THA", "IDN", "MYS"],
        "note": "支付宝2015年起覆盖东南亚，移动支付出海",
    },
    {
        "id": "wechatpay_asia",
        "model_id": "mobile_payment",
        "model_type": "env",
        "name": "微信支付进入日韩东南亚",
        "entry_year": 2016,
        "entry_countries": ["JPN", "KOR", "THA"],
        "note": "微信支付2016年布局海外线下扫码",
    },
    {
        "id": "ant_india",
        "model_id": "fintech_lending",
        "model_type": "env",
        "name": "蚂蚁进入印度",
        "entry_year": 2015,
        "entry_countries": ["IND"],
        "note": "蚂蚁2015年投资Paytm，消费金融出海印度",
    },
    {
        "id": "kuaishou_brazil",
        "model_id": "short_video_social",
        "model_type": "env",
        "name": "快手进入巴西",
        "entry_year": 2018,
        "entry_countries": ["BRA"],
        "note": "快手2018年出海巴西，短视频拉美验证",
    },
    {
        "id": "kuaishou_indonesia",
        "model_id": "short_video_social",
        "model_type": "env",
        "name": "快手进入印尼",
        "entry_year": 2019,
        "entry_countries": ["IDN"],
        "note": "快手2019年进入印尼市场",
    },
    {
        "id": "joyy_middleeast",
        "model_id": "short_video_social",
        "model_type": "env",
        "name": "欢聚进入中东",
        "entry_year": 2017,
        "entry_countries": ["SAU", "ARE"],
        "note": "欢聚时代BIGO 2017年在中东爆发，直播社交出海",
    },
    {
        "id": "genshin_japan",
        "model_id": "gaming_export",
        "model_type": "global",
        "name": "原神进入日本",
        "entry_year": 2020,
        "entry_countries": ["JPN"],
        "note": "原神2020年在日本大获成功，二次元游戏出海",
    },
    {
        "id": "genshin_korea",
        "model_id": "gaming_export",
        "model_type": "global",
        "name": "原神进入韩国",
        "entry_year": 2020,
        "entry_countries": ["KOR"],
        "note": "原神2020年在韩国畅销榜登顶",
    },
    {
        "id": "star_rail_global",
        "model_id": "gaming_export",
        "model_type": "global",
        "name": "星穹铁道进入全球",
        "entry_year": 2023,
        "entry_countries": ["USA", "JPN", "KOR"],
        "note": "崩坏星穹铁道2023年全球上线即登顶",
    },
    {
        "id": "king_glory_southeast_asia",
        "model_id": "gaming_export",
        "model_type": "env",
        "name": "王者荣耀进入东南亚",
        "entry_year": 2018,
        "entry_countries": ["THA", "VNM", "IDN"],
        "note": "王者荣耀海外版AOV 2018年在东南亚电竞化运营",
    },
    {
        "id": "lilith_global",
        "model_id": "gaming_export",
        "model_type": "global",
        "name": "莉莉丝进入全球",
        "entry_year": 2018,
        "entry_countries": ["USA", "DEU", "JPN"],
        "note": "万国觉醒2018年海外收入爆发",
    },
    {
        "id": "netease_japan",
        "model_id": "gaming_export",
        "model_type": "global",
        "name": "网易进入日本",
        "entry_year": 2019,
        "entry_countries": ["JPN"],
        "note": "网易《荒野行动》2018-2019年在日本登顶",
    },
    {
        "id": "xiaomi_india",
        "model_id": "chinese_brand_dtc",
        "model_type": "capability",
        "profile": "dev_market",
        "name": "小米进入印度",
        "entry_year": 2014,
        "entry_countries": ["IND"],
        "note": "小米2014年进入印度，性价比手机登顶第一",
    },
    {
        "id": "xiaomi_europe",
        "model_id": "chinese_brand_dtc",
        "model_type": "capability",
        "profile": "affluent",
        "name": "小米进入欧洲",
        "entry_year": 2017,
        "entry_countries": ["ESP", "ITA", "FRA", "DEU"],
        "note": "小米2017年起横扫欧洲中端市场",
    },
    {
        "id": "huawei_europe",
        "model_id": "chinese_brand_dtc",
        "model_type": "capability",
        "profile": "affluent",
        "name": "华为进入欧洲",
        "entry_year": 2012,
        "entry_countries": ["DEU", "FRA", "GBR", "ESP"],
        "note": "华为2012年起在欧洲高端市场站稳",
    },
    {
        "id": "honor_europe",
        "model_id": "chinese_brand_dtc",
        "model_type": "capability",
        "profile": "affluent",
        "name": "荣耀进入欧洲",
        "entry_year": 2020,
        "entry_countries": ["DEU", "FRA", "ESP"],
        "note": "荣耀独立后2020年重启欧洲市场",
    },
    {
        "id": "vivo_southeast_asia",
        "model_id": "chinese_brand_dtc",
        "model_type": "capability",
        "profile": "dev_market",
        "name": "vivo进入东南亚",
        "entry_year": 2016,
        "entry_countries": ["VNM", "THA", "IDN"],
        "note": "vivo 2016年起在东南亚占据前五",
    },
    {
        "id": "realme_india",
        "model_id": "chinese_brand_dtc",
        "model_type": "capability",
        "profile": "dev_market",
        "name": "realme进入印度",
        "entry_year": 2018,
        "entry_countries": ["IND"],
        "note": "realme 2018年进入印度，性价比手机爆发",
    },
    {
        "id": "transsion_south_asia",
        "model_id": "chinese_brand_dtc",
        "model_type": "capability",
        "profile": "dev_market",
        "name": "传音进入南亚",
        "entry_year": 2018,
        "entry_countries": ["BGD", "PAK"],
        "note": "传音2018年后进入孟加拉/巴基斯坦，非洲模式复制南亚",
    },
    {
        "id": "dji_global",
        "model_id": "chinese_brand_dtc",
        "model_type": "capability",
        "profile": "affluent",
        "name": "大疆进入全球",
        "entry_year": 2015,
        "entry_countries": ["USA", "DEU", "JPN"],
        "note": "大疆无人机2015年起占全球70%+份额",
    },
    {
        "id": "anker_global",
        "model_id": "cross_border_supply_chain",
        "model_type": "capability",
        "profile": "affluent",
        "name": "安克进入全球",
        "entry_year": 2015,
        "entry_countries": ["USA", "JPN", "DEU"],
        "note": "安克创新2015年起成为全球充电品类第一",
    },
    {
        "id": "insta360_global",
        "model_id": "chinese_brand_dtc",
        "model_type": "capability",
        "profile": "affluent",
        "name": "影石进入全球",
        "entry_year": 2018,
        "entry_countries": ["USA", "JPN", "DEU"],
        "note": "影石Insta360 2018年起成为全球全景相机第一",
    },
    {
        "id": "roborock_usa",
        "model_id": "smart_home_export",
        "model_type": "capability",
        "profile": "affluent",
        "name": "石头进入美国",
        "entry_year": 2020,
        "entry_countries": ["USA"],
        "note": "石头科技2020年进入美国，扫地机器人出海",
    },
    {
        "id": "roborock_japan",
        "model_id": "smart_home_export",
        "model_type": "capability",
        "profile": "affluent",
        "name": "石头进入日本",
        "entry_year": 2021,
        "entry_countries": ["JPN"],
        "note": "石头科技2021年进入日本市场",
    },
    {
        "id": "ecovacs_europe",
        "model_id": "smart_home_export",
        "model_type": "capability",
        "profile": "affluent",
        "name": "科沃斯进入欧洲",
        "entry_year": 2018,
        "entry_countries": ["DEU", "FRA", "ESP"],
        "note": "科沃斯2018年在欧洲扫地机器人市场份额领先",
    },
    {
        "id": "dreame_europe",
        "model_id": "smart_home_export",
        "model_type": "capability",
        "profile": "affluent",
        "name": "追觅进入欧洲",
        "entry_year": 2021,
        "entry_countries": ["DEU", "FRA", "ESP"],
        "note": "追觅2021年起在欧洲快速增长",
    },
    {
        "id": "haier_usa",
        "model_id": "home_appliance_export",
        "model_type": "capability",
        "profile": "affluent",
        "name": "海尔进入美国",
        "entry_year": 2016,
        "entry_countries": ["USA"],
        "note": "海尔收购GE家电后2016年进入美国主流市场",
    },
    {
        "id": "haier_europe",
        "model_id": "home_appliance_export",
        "model_type": "capability",
        "profile": "affluent",
        "name": "海尔进入欧洲",
        "entry_year": 2016,
        "entry_countries": ["DEU", "FRA", "GBR", "ITA"],
        "note": "海尔收购Candy后2016年进入欧洲",
    },
    {
        "id": "midea_southeast_asia",
        "model_id": "home_appliance_export",
        "model_type": "capability",
        "profile": "dev_market",
        "name": "美的进入东南亚",
        "entry_year": 2015,
        "entry_countries": ["THA", "VNM", "IDN"],
        "note": "美的2015年在东南亚家电市场份额领先",
    },
    {
        "id": "tcl_usa",
        "model_id": "home_appliance_export",
        "model_type": "capability",
        "profile": "affluent",
        "name": "TCL进入美国",
        "entry_year": 2015,
        "entry_countries": ["USA"],
        "note": "TCL 2015年在美国电视市场份额进入前三",
    },
    {
        "id": "hisense_europe",
        "model_id": "home_appliance_export",
        "model_type": "capability",
        "profile": "affluent",
        "name": "海信进入欧洲",
        "entry_year": 2016,
        "entry_countries": ["DEU", "FRA", "ESP"],
        "note": "海信2016年赞助欧洲杯，进入欧洲主流市场",
    },
    {
        "id": "byd_israel",
        "model_id": "nev_export",
        "model_type": "global",
        "name": "比亚迪进入以色列",
        "entry_year": 2022,
        "entry_countries": ["ISR"],
        "note": "比亚迪2022年成为以色列新能源车销冠",
    },
    {
        "id": "byd_australia",
        "model_id": "nev_export",
        "model_type": "global",
        "name": "比亚迪进入澳大利亚",
        "entry_year": 2022,
        "entry_countries": ["AUS"],
        "note": "比亚迪2022年进入澳洲市场",
    },
    {
        "id": "byd_norway",
        "model_id": "nev_export",
        "model_type": "global",
        "profile": "affluent",
        "name": "比亚迪进入挪威",
        "entry_year": 2021,
        "entry_countries": ["NOR"],
        "note": "比亚迪2021年进入挪威，欧洲首发市场",
    },
    {
        "id": "nio_norway",
        "model_id": "nev_export",
        "model_type": "global",
        "profile": "affluent",
        "name": "蔚来进入挪威",
        "entry_year": 2021,
        "entry_countries": ["NOR"],
        "note": "蔚来2021年进入挪威，欧洲出海第一站",
    },
    {
        "id": "nio_europe",
        "model_id": "nev_export",
        "model_type": "capability",
        "profile": "affluent",
        "name": "蔚来进入欧洲",
        "entry_year": 2022,
        "entry_countries": ["DEU", "NLD", "SWE", "DNK"],
        "note": "蔚来2022年在欧洲四国落地",
    },
    {
        "id": "xpeng_norway",
        "model_id": "nev_export",
        "model_type": "global",
        "profile": "affluent",
        "name": "小鹏进入挪威",
        "entry_year": 2020,
        "entry_countries": ["NOR"],
        "note": "小鹏2020年进入挪威，新势力出海欧洲",
    },
    {
        "id": "gwm_thailand",
        "model_id": "nev_export",
        "model_type": "env",
        "name": "长城进入泰国",
        "entry_year": 2021,
        "entry_countries": ["THA"],
        "note": "长城汽车2021年收购泰国工厂，东南亚布局",
    },
    {
        "id": "mg_uk",
        "model_id": "nev_export",
        "model_type": "capability",
        "profile": "affluent",
        "name": "名爵进入英国",
        "entry_year": 2017,
        "entry_countries": ["GBR"],
        "note": "名爵2017年在英国销量爆发，上汽出海",
    },
    {
        "id": "chery_russia",
        "model_id": "nev_export",
        "model_type": "env",
        "name": "奇瑞进入俄罗斯",
        "entry_year": 2020,
        "entry_countries": ["RUS"],
        "note": "奇瑞2020年在俄罗斯市场份额进入前五",
    },
    {
        "id": "yadea_southeast_asia",
        "model_id": "ev_two_wheeler",
        "model_type": "env",
        "name": "雅迪进入东南亚",
        "entry_year": 2020,
        "entry_countries": ["VNM", "THA", "IDN"],
        "note": "雅迪2020年进军东南亚电动两轮车市场",
    },
    {
        "id": "niu_europe",
        "model_id": "ev_two_wheeler",
        "model_type": "global",
        "name": "小牛进入欧洲",
        "entry_year": 2017,
        "entry_countries": ["DEU", "FRA", "NLD"],
        "note": "小牛电动2017年进入欧洲市场",
    },
    {
        "id": "jnt_vietnam",
        "model_id": "logistics_export",
        "model_type": "env",
        "name": "极兔进入越南",
        "entry_year": 2019,
        "entry_countries": ["VNM"],
        "note": "极兔2019年进入越南，东南亚快速扩张",
    },
    {
        "id": "jnt_thailand",
        "model_id": "logistics_export",
        "model_type": "env",
        "name": "极兔进入泰国",
        "entry_year": 2019,
        "entry_countries": ["THA"],
        "note": "极兔2019年进入泰国市场",
    },
    {
        "id": "jnt_malaysia",
        "model_id": "logistics_export",
        "model_type": "env",
        "name": "极兔进入马来西亚",
        "skip": "region_expansion",
        "entry_year": 2020,
        "entry_countries": ["MYS"],
        "note": "极兔2020年进入马来西亚",
    },
    {
        "id": "jnt_brazil",
        "model_id": "logistics_export",
        "model_type": "env",
        "name": "极兔进入巴西",
        "skip": "region_expansion",
        "entry_year": 2021,
        "entry_countries": ["BRA"],
        "note": "极兔2021年进入巴西，跨洲扩张",
    },
    {
        "id": "jnt_middleeast",
        "model_id": "logistics_export",
        "model_type": "env",
        "name": "极兔进入中东",
        "entry_year": 2021,
        "entry_countries": ["SAU", "ARE"],
        "note": "极兔2021年进入沙特/阿联酋",
    },
    {
        "id": "cainiao_southeast_asia",
        "model_id": "logistics_export",
        "model_type": "env",
        "name": "菜鸟进入东南亚",
        "entry_year": 2018,
        "entry_countries": ["IDN", "THA", "MYS"],
        "note": "菜鸟2018年布局东南亚物流网络",
    },
]


# 区域定义（世界银行区域，用于区域先行者加成）
REGIONS = {
    "southeast_asia": {"IDN", "VNM", "THA", "PHL", "MYS", "SGP", "KHM", "MMR", "LAO", "BRN"},
    "south_asia": {"IND", "PAK", "BGD", "LKA", "NPL", "BTN"},
    "africa": {"NGA", "KEN", "ETH", "TZA", "GHA", "ZAF", "EGY", "MAR", "DZA", "TUN",
               "UGA", "RWA", "CMR", "CIV", "SEN", "MLI", "BFA", "NER", "TCD", "AGO",
               "MOZ", "ZMB", "ZWE", "COD", "COG", "GAB"},
    "latam": {"BRA", "MEX", "COL", "PER", "CHL", "ARG", "ECU", "BOL", "PRY", "URY", "VEN"},
    "europe": {"DEU", "FRA", "ESP", "ITA", "GBR", "POL", "ROU", "HUN", "CZE", "SVK",
               "HRV", "SRB", "GRC", "PRT", "NLD", "BEL", "CHE", "SWE", "NOR", "DNK",
               "FIN", "IRL", "AUT", "BLR", "UKR", "RUS", "TUR"},
    "middle_east": {"SAU", "ARE", "IRN", "IRQ", "ISR", "JOR", "LBN", "SYR", "YEM", "OMN", "KWT", "QAT", "BHR"},
    "central_asia": {"KAZ", "UZB", "KGZ", "TJK", "TKM", "MNG"},
}


def _region_of(iso3: str) -> str | None:
    """返回国家所属区域"""
    for region, members in REGIONS.items():
        if iso3 in members:
            return region
    return None


def _region_peers(model_id: str, current_case_id: str) -> set:
    """同模式其他成功案例进入的国家（当前案例的"区域先行者"邻国池）"""
    peers = set()
    for c in KNOWN_CASES:
        if c["id"] == current_case_id or c["model_id"] != model_id:
            continue
        # 同模式其他案例成功进入的国家，其区域成员 = 邻国池
        for iso3 in c["entry_countries"]:
            region = _region_of(iso3)
            if region:
                peers |= REGIONS[region]
    return peers


class BacktestEngine:
    """历史验证引擎"""

    # 华语同源市场（中国模式复制优先序）
    SINOSPHERE = ["TWN", "HKG", "MAC", "SGP"]

    def __init__(self, collector: WorldBankCollector | None = None):
        self.collector = collector or WorldBankCollector()

    # ── 同源市场案例 ──────────────────────────────────────

    def _homeland_case(self, case: dict, top_n: int = 15) -> dict:
        """同源市场验证：港澳台/新加坡等华语文化圈，中国模式复制优先
        评分 = 市场规模(人口) + 购买力(人均GDP) + 数字化(互联网)，
        同源圈内排序，真实进入地区应在圈内前列。
        """
        entry_year = case["entry_year"]
        years = list(range(entry_year - 1, entry_year + 2))

        # 同源市场评分（圈内所有成员参与排名）
        scores = {}
        for iso3 in self.SINOSPHERE:
            pop = self.collector.get_country_avg(iso3, "population", years)
            gdp_pc = self.collector.get_country_avg(iso3, "gdp_pc", years)
            internet = self.collector.get_country_avg(iso3, "internet", years)
            if pop is None or gdp_pc is None:
                continue
            # 市场规模分（对数压缩） + 购买力 + 数字化
            size = min(1.0, (pop or 0) / 25_000_000)      # 2500万人口封顶
            power = min(1.0, (gdp_pc or 0) / 60000)       # 6万美元封顶
            digit = min(1.0, (internet or 0) / 100)
            score = size * 0.4 + power * 0.35 + digit * 0.25
            scores[iso3] = {"score": round(score, 4), "size": size,
                            "power": power, "digit": digit}

        ranked = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
        ranks = {iso3: i + 1 for i, (iso3, _) in enumerate(ranked[:top_n])}

        hits = []
        for iso3 in case["entry_countries"]:
            hits.append({
                "iso3": iso3,
                "name": COUNTRY_CN.get(iso3, iso3),
                "rank": ranks.get(iso3),
                "score": scores.get(iso3, {}).get("score"),
                "in_top": iso3 in ranks,
            })
        passed = any(h["in_top"] for h in hits)
        return {
            "case": case,
            "model": "homeland",
            "hits": hits,
            "passed": passed,
            "top3": [
                {"iso3": iso3, "name": COUNTRY_CN.get(iso3, iso3), "score": s["score"]}
                for iso3, s in ranked[:3]
            ],
        }

    # ── 单个案例验证 ──────────────────────────────────────

    def run_case(self, case: dict, top_n: int = 15) -> dict:
        """验证一个案例：
        1. env 型 → 环境相似匹配（分位数模式，增强发展阶段相似性）
        2. capability 型 → 供应链优势模型
        """
        model_type = case.get("model_type", "env")
        if model_type == "capability":
            from .capability_model import CapabilityExportModel
            cm = CapabilityExportModel(self.collector)
            return cm.backtest_case(case, top_n=top_n)
        if model_type == "homeland":
            return self._homeland_case(case, top_n=top_n)
        if model_type == "global":
            from .global_model import GlobalExportModel
            gm = GlobalExportModel(self.collector)
            return gm.backtest_case(case, top_n=top_n)

        # ── env 型：环境相似匹配（分位数） ──────────────
        model_id = case["model_id"]
        entry_year = case["entry_year"]
        from .playbook import PLAYBOOK_BY_ID
        pb = PLAYBOOK_BY_ID.get(model_id)
        if not pb:
            return {"case": case, "error": f"模式 {model_id} 不存在"}
        golden = pb.get("golden_years", [entry_year - 4, entry_year])
        years = list(range(golden[0], golden[1] + 1))

        # 中国快照（用百分位表达，发展阶段相似性）
        ref = {}
        for dim_key in ENV_DIMENSIONS:
            v = self.collector.get_country_avg(CHINA_ISO3, dim_key, years)
            if v is not None:
                ref[dim_key] = v

        # 目标国在 entry_year 前后的环境（同样转百分位）
        cand_years = list(range(entry_year - 1, entry_year + 2))
        world = {}
        for iso3 in self.collector.available_countries():
            if iso3 == CHINA_ISO3:
                continue
            pop = self.collector.get_country_avg(iso3, "population", cand_years)
            if pop is None or pop < 3_000_000:
                continue
            avgs = {}
            for dim_key in ENV_DIMENSIONS:
                v = self.collector.get_country_avg(iso3, dim_key, cand_years)
                if v is not None:
                    avgs[dim_key] = v
            if len(avgs) >= 5:
                world[iso3] = avgs

        # 转成百分位：参考值 + 候选值都换成"当时全球百分位"
        ref_pct = {}
        for dim_key in ref:
            p = self.collector.percentile_of(CHINA_ISO3, dim_key, years)
            if p is not None:
                ref_pct[dim_key] = p
        world_pct = {}
        for iso3, avgs in world.items():
            wp = {}
            for dim_key in avgs:
                p = self.collector.percentile_of(iso3, dim_key, cand_years)
                if p is not None:
                    wp[dim_key] = p
            if len(wp) >= 5:
                world_pct[iso3] = wp

        # 匹配（百分位模式：0-1 之间直接比较）
        matcher = EnvironmentMatcher(pb.get("dim_weights"), mode="percentile")
        # 多取一些国家（含邻国加成机会），加成后再截断 top_n
        ranked_all = matcher.rank_countries(ref_pct, world_pct, top_n=max(top_n * 3, 60))
        ranked = ranked_all[:]

        # 区域先行者加成：同区域已有成功案例（案例库中同模式其他案例的目标国）→ 邻国加分
        # 例: 蜜雪成功进入印尼 → 越南/菲律宾/泰国等东南亚邻国优先级提高
        try:
            from .backtest import _region_of, _region_peers
            peers = _region_peers(model_id, case.get("id"))
            if peers:
                for r in ranked:
                    if r["iso3"] in peers:
                        r["score"] = min(0.9999, r["score"] * 1.35)  # +35% 邻国加成
        except Exception:
            pass

        # 同源市场加成：华语文化圈（港澳台+新加坡）匹配中国模式时加分
        # 港澳台虽是高收入经济体，但与内地"语言相通/文化同源/物流便捷/品牌认知高"，
        # 中国模式向它们复制是"同源市场"逻辑（用户 2026-08-08 提出）
        try:
            SINOSPHERE = {"HKG", "TWN", "MAC", "SGP"}
            for r in ranked:
                if r["iso3"] in SINOSPHERE:
                    r["score"] = min(0.9999, r["score"] * 1.6)  # +60% 同源市场加成
        except Exception:
            pass

        # 重新排序并截断
        ranked.sort(key=lambda x: x["score"], reverse=True)
        ranked = ranked[:top_n]
        ranks = {r["iso3"]: i + 1 for i, r in enumerate(ranked)}
        scores = {r["iso3"]: r["score"] for r in ranked}

        hits = []
        for iso3 in case["entry_countries"]:
            in_top = iso3 in ranks
            hits.append({
                "iso3": iso3,
                "name": COUNTRY_CN.get(iso3, iso3),
                "rank": ranks.get(iso3),
                "score": scores.get(iso3),
                "in_top": in_top,
            })

        passed = any(h["in_top"] for h in hits)
        return {
            "case": case,
            "model": "env_percentile",
            "ref_years": years,
            "cand_years": cand_years,
            "hits": hits,
            "passed": passed,
            "top3": [
                {"iso3": r["iso3"], "name": COUNTRY_CN.get(r["iso3"], r["iso3"]),
                 "score": r["score"]}
                for r in ranked[:3]
            ],
        }

    # ── 全量回测 ──────────────────────────────────────────

    def run(self, top_n: int = 15) -> dict:
        results = []
        passed_count = 0
        skipped_count = 0
        for case in KNOWN_CASES:
            if case.get("skip"):
                skipped_count += 1
                logger.info("[回测] %s: ⏭️ 跳过 (%s)", case["name"], case["skip"])
                continue
            r = self.run_case(case, top_n=top_n)
            results.append(r)
            if r.get("passed"):
                passed_count += 1
            logger.info("[回测] %s: %s", case["name"], "✅" if r.get("passed") else "❌")

        total = len(results)
        return {
            "mode": "backtest",
            "run_at": datetime.now().isoformat(),
            "total_cases": total,
            "skipped_cases": skipped_count,
            "passed_cases": passed_count,
            "pass_rate": round(passed_count / total, 3) if total else 0,
            "top_n": top_n,
            "results": results,
        }

    def to_report(self, data: dict) -> str:
        lines = [
            "# 🧭 出海时光机 · 历史验证报告（Backtest）",
            "",
            f"- 案例数: {data['total_cases']}",
            f"- 通过数: {data['passed_cases']}（目标国在 Top {data['top_n']} 内）",
            f"- **通过率: {data['pass_rate']:.0%}**",
            "",
            "## 逐案例验证",
            "",
        ]
        for r in data["results"]:
            c = r["case"]
            mark = "✅" if r.get("passed") else "❌"
            lines.append(f"### {mark} {c['name']}（{c['id']}）")
            lines.append(f"- 模式: {c['model_id']} | 进入年份: {c['entry_year']}")
            lines.append(f"- 真实进入: {', '.join(h['name'] for h in r['hits'])}")
            lines.append(f"- 回测排名: " + ", ".join(
                f"{h['name']} 第{h['rank']}名({(h.get('score') or h.get('total') or 0):.0%})" if h["rank"] else f"{h['name']} 未进Top{data['top_n']}"
                for h in r["hits"]
            ))
            top3 = "、".join(f"{t['name']}({(t.get('score') or t.get('total') or 0):.0%})" for t in r.get("top3", []))
            lines.append(f"- 引擎当时Top3: {top3}")
            lines.append(f"- 备注: {c.get('note', '')}")
            lines.append("")
        return "\n".join(lines)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    engine = BacktestEngine()
    data = engine.run()
    print(engine.to_report(data))

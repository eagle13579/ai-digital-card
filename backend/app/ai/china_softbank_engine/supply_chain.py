"""
产业链双向链接引擎 (Supply Chain Dual-Link Engine)
====================================================
海容方法论落地（2026-08-08）：
「用产业链的逻辑去思考现象和链接的方式去思考现象」——事件不是孤立的，它会沿产业链双向传导。

核心思想（海容原话）：
  美国说要控制中国的芯片 → 芯片的上游是光模块 → 光模块的上游是铜箔 → PCB → 再往上走是金属（铜）
  → 有这种双向链接的思路，就可以找到相应的产业/公司/机会 → 并且可以进行一定的预测

设计：
  - 图谱：节点=产业链环节（name/cn/上下游/代表公司/弹性系数/国产化率），边=上下游关系（带传导系数）
  - 事件注入：事件冲击某一环节 → 沿产业链双向传播（上游=供给冲击，下游=需求冲击）
  - 传导：每跳衰减（transmission 系数）+ 弹性放大（elasticity 系数）
  - 输出：受益环节/受损环节/传导路径/预测窗口（时间轴）→ 对应代表公司 → 机会清单
  - 双向：既是「上游受限→下游涨价」的正向链，也是「下游爆发→上游需求」的反向链

参考方法论：
  - MiroFish（群体智能预测引擎，github.com/666ghj/MiroFish 70.7k★）：事件注入→多智能体演化→预测报告
  - 帕玛拉特/美元潮汐套利模式：事件沿产业链传导产生套利窗口

版本: v1.0.0
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# ============================================================
# 产业链图谱（内置种子，后续可从 knowledge-sync 加载扩充）
# ============================================================
# 每个节点:
#   id: 唯一标识
#   name: 中文名
#   type: raw_material(原材料)/component(零部件)/device(设备)/product(成品)/service(服务)/infra(基础设施)
#   companies: 代表公司（真实 A股/美股/港股 龙头，带 ticker）
#   elasticity: 弹性系数(1.0=平均，>1 高弹性，<1 低弹性) —— 对上游价格的敏感度
#   domestic_rate: 国产化率 0-1（低=卡脖子点，高=国产替代已完成）
#   policy_weight: 政策敏感度 0-1（高科技制裁/补贴/关税的敏感度）

CHAIN_GRAPH: Dict[str, Dict[str, Any]] = {
    # ---------- 算力/芯片产业链（海容例：美国限芯片 → 光模块 → 铜箔 → PCB → 金属铜）----------
    "ai_chip": {
        "id": "ai_chip", "name": "AI芯片/GPU", "type": "device",
        "companies": [{"ticker": "NVDA", "name": "英伟达", "mkt": "US"},
                      {"ticker": "688041", "name": "海光信息", "mkt": "CN"},
                      {"ticker": "688256", "name": "寒武纪", "mkt": "CN"},
                      {"ticker": "002371", "name": "北方华创", "mkt": "CN"}],
        "elasticity": 1.4, "domestic_rate": 0.25, "policy_weight": 0.95,
        "upstream": [{"node": "eda_equip", "coef": 0.7}, {"node": "wafer", "coef": 0.6},
                     {"node": "optical_module", "coef": 0.3}],
        "downstream": [{"node": "ai_server", "coef": 0.9}, {"node": "smartphone", "coef": 0.4}],
    },
    "eda_equip": {
        "id": "eda_equip", "name": "EDA/半导体设备", "type": "device",
        "companies": [{"ticker": "688012", "name": "中微公司", "mkt": "CN"},
                      {"ticker": "002371", "name": "北方华创", "mkt": "CN"},
                      {"ticker": "688120", "name": "华海清科", "mkt": "CN"}],
        "elasticity": 1.6, "domestic_rate": 0.15, "policy_weight": 0.98,
        "upstream": [{"node": "rare_metal", "coef": 0.4}],
        "downstream": [{"node": "ai_chip", "coef": 0.7}],
    },
    "wafer": {
        "id": "wafer", "name": "晶圆/硅片", "type": "raw_material",
        "companies": [{"ticker": "688126", "name": "沪硅产业", "mkt": "CN"},
                      {"ticker": "TSM", "name": "台积电", "mkt": "US"},
                      {"ticker": "SMIC", "name": "中芯国际", "mkt": "HK"}],
        "elasticity": 1.2, "domestic_rate": 0.3, "policy_weight": 0.85,
        "upstream": [{"node": "poly_silicon", "coef": 0.5}, {"node": "rare_metal", "coef": 0.3}],
        "downstream": [{"node": "ai_chip", "coef": 0.6}],
    },
    "optical_module": {
        "id": "optical_module", "name": "光模块", "type": "component",
        "companies": [{"ticker": "300308", "name": "中际旭创", "mkt": "CN"},
                      {"ticker": "002281", "name": "光迅科技", "mkt": "CN"},
                      {"ticker": "300502", "name": "新易盛", "mkt": "CN"}],
        "elasticity": 1.8, "domestic_rate": 0.45, "policy_weight": 0.7,
        "upstream": [{"node": "copper_foil", "coef": 0.5}, {"node": "pcb", "coef": 0.6},
                     {"node": "optical_chip", "coef": 0.7}],
        "downstream": [{"node": "ai_server", "coef": 0.8}, {"node": "data_center", "coef": 0.9},
                       {"node": "ai_chip", "coef": 0.3}],
    },
    "optical_chip": {
        "id": "optical_chip", "name": "光芯片", "type": "component",
        "companies": [{"ticker": "688048", "name": "长光华芯", "mkt": "CN"},
                      {"ticker": "300502", "name": "新易盛", "mkt": "CN"}],
        "elasticity": 2.0, "domestic_rate": 0.2, "policy_weight": 0.9,
        "upstream": [{"node": "copper_foil", "coef": 0.3}, {"node": "rare_metal", "coef": 0.4}],
        "downstream": [{"node": "optical_module", "coef": 0.7}],
    },
    "copper_foil": {
        "id": "copper_foil", "name": "铜箔", "type": "raw_material",
        "companies": [{"ticker": "002636", "name": "金安国纪", "mkt": "CN"},
                      {"ticker": "600884", "name": "杉杉股份", "mkt": "CN"},
                      {"ticker": "688778", "name": "厦钨新能", "mkt": "CN"}],
        "elasticity": 1.9, "domestic_rate": 0.6, "policy_weight": 0.5,
        "upstream": [{"node": "copper", "coef": 0.85}],
        "downstream": [{"node": "pcb", "coef": 0.9}, {"node": "optical_module", "coef": 0.5},
                       {"node": "battery", "coef": 0.6}],
    },
    "pcb": {
        "id": "pcb", "name": "PCB印制电路板", "type": "component",
        "companies": [{"ticker": "002463", "name": "沪电股份", "mkt": "CN"},
                      {"ticker": "300476", "name": "胜宏科技", "mkt": "CN"},
                      {"ticker": "002938", "name": "鹏鼎控股", "mkt": "CN"}],
        "elasticity": 1.7, "domestic_rate": 0.7, "policy_weight": 0.5,
        "upstream": [{"node": "copper_foil", "coef": 0.85}, {"node": "copper", "coef": 0.5},
                     {"node": "resin", "coef": 0.3}],
        "downstream": [{"node": "ai_server", "coef": 0.8}, {"node": "optical_module", "coef": 0.6},
                       {"node": "smartphone", "coef": 0.5}, {"node": "ev", "coef": 0.4}],
    },
    "copper": {
        "id": "copper", "name": "金属铜/电解铜", "type": "raw_material",
        "companies": [{"ticker": "601899", "name": "紫金矿业", "mkt": "CN"},
                      {"ticker": "603993", "name": "洛阳钼业", "mkt": "CN"},
                      {"ticker": "000630", "name": "铜陵有色", "mkt": "CN"},
                      {"ticker": "FCX", "name": "Freeport", "mkt": "US"}],
        "elasticity": 2.2, "domestic_rate": 0.8, "policy_weight": 0.6,
        "upstream": [{"node": "mine", "coef": 0.9}],
        "downstream": [{"node": "copper_foil", "coef": 0.85}, {"node": "pcb", "coef": 0.5},
                       {"node": "power_grid", "coef": 0.7}, {"node": "ev", "coef": 0.6},
                       {"node": "data_center", "coef": 0.5}],
    },
    "rare_metal": {
        "id": "rare_metal", "name": "稀有金属/稀土", "type": "raw_material",
        "companies": [{"ticker": "600111", "name": "北方稀土", "mkt": "CN"},
                      {"ticker": "603799", "name": "华友钴业", "mkt": "CN"},
                      {"ticker": "002460", "name": "赣锋锂业", "mkt": "CN"}],
        "elasticity": 2.4, "domestic_rate": 0.75, "policy_weight": 0.9,
        "upstream": [{"node": "mine", "coef": 0.9}],
        "downstream": [{"node": "wafer", "coef": 0.3}, {"node": "eda_equip", "coef": 0.4},
                       {"node": "battery", "coef": 0.7}, {"node": "ev", "coef": 0.5}],
    },
    "poly_silicon": {
        "id": "poly_silicon", "name": "多晶硅", "type": "raw_material",
        "companies": [{"ticker": "600438", "name": "通威股份", "mkt": "CN"},
                      {"ticker": "688303", "name": "大全能源", "mkt": "CN"}],
        "elasticity": 1.5, "domestic_rate": 0.9, "policy_weight": 0.5,
        "upstream": [{"node": "mine", "coef": 0.5}],
        "downstream": [{"node": "wafer", "coef": 0.5}, {"node": "solar", "coef": 0.9}],
    },
    "resin": {
        "id": "resin", "name": "树脂/化工材料", "type": "raw_material",
        "companies": [{"ticker": "600309", "name": "万华化学", "mkt": "CN"},
                      {"ticker": "002648", "name": "卫星化学", "mkt": "CN"}],
        "elasticity": 1.1, "domestic_rate": 0.8, "policy_weight": 0.3,
        "upstream": [{"node": "oil_gas", "coef": 0.8}],
        "downstream": [{"node": "pcb", "coef": 0.3}],
    },
    "oil_gas": {
        "id": "oil_gas", "name": "石油天然气", "type": "raw_material",
        "companies": [{"ticker": "601857", "name": "中国石油", "mkt": "CN"},
                      {"ticker": "600028", "name": "中国石化", "mkt": "CN"},
                      {"ticker": "XOM", "name": "Exxon", "mkt": "US"}],
        "elasticity": 0.8, "domestic_rate": 0.7, "policy_weight": 0.4,
        "upstream": [{"node": "mine", "coef": 0.6}],
        "downstream": [{"node": "resin", "coef": 0.8}, {"node": "power_grid", "coef": 0.4}],
    },
    "mine": {
        "id": "mine", "name": "矿山资源", "type": "infra",
        "companies": [{"ticker": "601899", "name": "紫金矿业", "mkt": "CN"},
                      {"ticker": "603993", "name": "洛阳钼业", "mkt": "CN"}],
        "elasticity": 2.0, "domestic_rate": 0.9, "policy_weight": 0.5,
        "upstream": [], "downstream": [{"node": "copper", "coef": 0.9}, {"node": "rare_metal", "coef": 0.9},
                                       {"node": "poly_silicon", "coef": 0.5}, {"node": "oil_gas", "coef": 0.6}],
    },
    # ---------- AI 服务器/数据中心 ----------
    "ai_server": {
        "id": "ai_server", "name": "AI服务器", "type": "device",
        "companies": [{"ticker": "000977", "name": "浪潮信息", "mkt": "CN"},
                      {"ticker": "603019", "name": "中科曙光", "mkt": "CN"},
                      {"ticker": "DELL", "name": "戴尔", "mkt": "US"}],
        "elasticity": 1.3, "domestic_rate": 0.5, "policy_weight": 0.6,
        "upstream": [{"node": "ai_chip", "coef": 0.8}, {"node": "pcb", "coef": 0.6},
                     {"node": "optical_module", "coef": 0.6}, {"node": "power_grid", "coef": 0.4}],
        "downstream": [{"node": "data_center", "coef": 0.9}],
    },
    "data_center": {
        "id": "data_center", "name": "数据中心/云", "type": "service",
        "companies": [{"ticker": "600845", "name": "宝信软件", "mkt": "CN"},
                      {"ticker": "MSFT", "name": "微软", "mkt": "US"},
                      {"ticker": "GOOGL", "name": "谷歌", "mkt": "US"}],
        "elasticity": 1.0, "domestic_rate": 0.6, "policy_weight": 0.5,
        "upstream": [{"node": "ai_server", "coef": 0.9}, {"node": "optical_module", "coef": 0.8},
                     {"node": "power_grid", "coef": 0.5}, {"node": "copper", "coef": 0.5}],
        "downstream": [],
    },
    "power_grid": {
        "id": "power_grid", "name": "电力/电网", "type": "infra",
        "companies": [{"ticker": "600406", "name": "国电南瑞", "mkt": "CN"},
                      {"ticker": "601985", "name": "中国核电", "mkt": "CN"},
                      {"ticker": "VST", "name": "Vistra", "mkt": "US"}],
        "elasticity": 1.0, "domestic_rate": 0.9, "policy_weight": 0.6,
        "upstream": [{"node": "copper", "coef": 0.7}, {"node": "oil_gas", "coef": 0.4}],
        "downstream": [{"node": "data_center", "coef": 0.5}, {"node": "ai_server", "coef": 0.4},
                       {"node": "ev", "coef": 0.5}],
    },
    # ---------- 终端消费 ----------
    "smartphone": {
        "id": "smartphone", "name": "智能手机", "type": "product",
        "companies": [{"ticker": "AAPL", "name": "苹果", "mkt": "US"},
                      {"ticker": "002475", "name": "立讯精密", "mkt": "CN"},
                      {"ticker": "000725", "name": "京东方A", "mkt": "CN"}],
        "elasticity": 0.9, "domestic_rate": 0.7, "policy_weight": 0.3,
        "upstream": [{"node": "ai_chip", "coef": 0.4}, {"node": "pcb", "coef": 0.5},
                     {"node": "battery", "coef": 0.5}],
        "downstream": [],
    },
    "ev": {
        "id": "ev", "name": "新能源汽车", "type": "product",
        "companies": [{"ticker": "002594", "name": "比亚迪", "mkt": "CN"},
                      {"ticker": "TSLA", "name": "特斯拉", "mkt": "US"},
                      {"ticker": "601633", "name": "长城汽车", "mkt": "CN"}],
        "elasticity": 1.1, "domestic_rate": 0.8, "policy_weight": 0.5,
        "upstream": [{"node": "battery", "coef": 0.8}, {"node": "copper", "coef": 0.6},
                     {"node": "pcb", "coef": 0.4}],
        "downstream": [],
    },
    "battery": {
        "id": "battery", "name": "动力电池", "type": "component",
        "companies": [{"ticker": "300750", "name": "宁德时代", "mkt": "CN"},
                      {"ticker": "002594", "name": "比亚迪", "mkt": "CN"},
                      {"ticker": "300014", "name": "亿纬锂能", "mkt": "CN"}],
        "elasticity": 1.4, "domestic_rate": 0.85, "policy_weight": 0.6,
        "upstream": [{"node": "rare_metal", "coef": 0.7}, {"node": "copper_foil", "coef": 0.6}],
        "downstream": [{"node": "ev", "coef": 0.8}, {"node": "smartphone", "coef": 0.3}],
    },
    "solar": {
        "id": "solar", "name": "光伏", "type": "product",
        "companies": [{"ticker": "601012", "name": "隆基绿能", "mkt": "CN"},
                      {"ticker": "002459", "name": "晶澳科技", "mkt": "CN"}],
        "elasticity": 1.6, "domestic_rate": 0.95, "policy_weight": 0.5,
        "upstream": [{"node": "poly_silicon", "coef": 0.9}],
        "downstream": [],
    },
    "lithium": {
        "id": "lithium", "name": "碳酸锂/锂矿", "type": "raw_material",
        "companies": [{"ticker": "002466", "name": "天齐锂业", "mkt": "CN"}, {"ticker": "002460", "name": "赣锋锂业", "mkt": "CN"}, {"ticker": "300390", "name": "天华新能", "mkt": "CN"}],
        "elasticity": 2.6, "domestic_rate": 0.65, "policy_weight": 0.6,
        "upstream": [{"node": "mine", "coef": 0.9}],
        "downstream": [{"node": "cathode", "coef": 0.9}, {"node": "battery", "coef": 0.5}],
    },
    "cathode": {
        "id": "cathode", "name": "正极材料", "type": "raw_material",
        "companies": [{"ticker": "002245", "name": "蔚蓝锂芯", "mkt": "CN"}, {"ticker": "300073", "name": "当升科技", "mkt": "CN"}],
        "elasticity": 1.8, "domestic_rate": 0.8, "policy_weight": 0.4,
        "upstream": [{"node": "lithium", "coef": 0.9}, {"node": "rare_metal", "coef": 0.6}],
        "downstream": [{"node": "battery", "coef": 0.9}],
    },
    "anode": {
        "id": "anode", "name": "负极材料", "type": "raw_material",
        "companies": [{"ticker": "300035", "name": "中科电气", "mkt": "CN"}, {"ticker": "603659", "name": "璞泰来", "mkt": "CN"}],
        "elasticity": 1.6, "domestic_rate": 0.85, "policy_weight": 0.3,
        "upstream": [{"node": "mine", "coef": 0.5}],
        "downstream": [{"node": "battery", "coef": 0.9}],
    },
    "electrolyte": {
        "id": "electrolyte", "name": "电解液", "type": "raw_material",
        "companies": [{"ticker": "002709", "name": "天赐材料", "mkt": "CN"}, {"ticker": "300037", "name": "新宙邦", "mkt": "CN"}],
        "elasticity": 1.7, "domestic_rate": 0.85, "policy_weight": 0.3,
        "upstream": [{"node": "resin", "coef": 0.6}],
        "downstream": [{"node": "battery", "coef": 0.9}],
    },
    "separator": {
        "id": "separator", "name": "隔膜", "type": "raw_material",
        "companies": [{"ticker": "300568", "name": "星源材质", "mkt": "CN"}, {"ticker": "002812", "name": "恩捷股份", "mkt": "CN"}],
        "elasticity": 1.5, "domestic_rate": 0.75, "policy_weight": 0.3,
        "upstream": [{"node": "resin", "coef": 0.5}],
        "downstream": [{"node": "battery", "coef": 0.9}],
    },
    "pv_wafer": {
        "id": "pv_wafer", "name": "光伏硅片", "type": "raw_material",
        "companies": [{"ticker": "601012", "name": "隆基绿能", "mkt": "CN"}, {"ticker": "688223", "name": "晶科能源", "mkt": "CN"}],
        "elasticity": 1.9, "domestic_rate": 0.95, "policy_weight": 0.4,
        "upstream": [{"node": "poly_silicon", "coef": 0.9}],
        "downstream": [{"node": "pv_cell", "coef": 0.9}],
    },
    "pv_cell": {
        "id": "pv_cell", "name": "光伏电池片", "type": "component",
        "companies": [{"ticker": "688599", "name": "天合光能", "mkt": "CN"}, {"ticker": "002459", "name": "晶澳科技", "mkt": "CN"}],
        "elasticity": 1.8, "domestic_rate": 0.95, "policy_weight": 0.4,
        "upstream": [{"node": "pv_wafer", "coef": 0.9}, {"node": "silver", "coef": 0.4}],
        "downstream": [{"node": "pv_module", "coef": 0.9}],
    },
    "pv_module": {
        "id": "pv_module", "name": "光伏组件", "type": "product",
        "companies": [{"ticker": "601012", "name": "隆基绿能", "mkt": "CN"}, {"ticker": "688223", "name": "晶科能源", "mkt": "CN"}],
        "elasticity": 1.5, "domestic_rate": 0.95, "policy_weight": 0.4,
        "upstream": [{"node": "pv_cell", "coef": 0.9}, {"node": "glass", "coef": 0.4}],
        "downstream": [{"node": "solar", "coef": 0.9}],
    },
    "inverter": {
        "id": "inverter", "name": "逆变器", "type": "component",
        "companies": [{"ticker": "300274", "name": "阳光电源", "mkt": "CN"}, {"ticker": "688390", "name": "固德威", "mkt": "CN"}],
        "elasticity": 1.6, "domestic_rate": 0.8, "policy_weight": 0.4,
        "upstream": [{"node": "copper", "coef": 0.5}, {"node": "pcb", "coef": 0.4}],
        "downstream": [{"node": "solar", "coef": 0.8}, {"node": "power_grid", "coef": 0.6}],
    },
    "glass": {
        "id": "glass", "name": "光伏玻璃", "type": "raw_material",
        "companies": [{"ticker": "601865", "name": "福莱特", "mkt": "CN"}, {"ticker": "300393", "name": "中来股份", "mkt": "CN"}],
        "elasticity": 1.4, "domestic_rate": 0.95, "policy_weight": 0.3,
        "upstream": [{"node": "oil_gas", "coef": 0.5}],
        "downstream": [{"node": "pv_module", "coef": 0.4}],
    },
    "silver": {
        "id": "silver", "name": "白银/银浆", "type": "raw_material",
        "companies": [{"ticker": "601899", "name": "紫金矿业", "mkt": "CN"}, {"ticker": "000630", "name": "铜陵有色", "mkt": "CN"}],
        "elasticity": 2.3, "domestic_rate": 0.7, "policy_weight": 0.4,
        "upstream": [{"node": "mine", "coef": 0.9}],
        "downstream": [{"node": "pv_cell", "coef": 0.4}, {"node": "solar", "coef": 0.3}],
    },
    "memory": {
        "id": "memory", "name": "存储芯片(HBM/DRAM)", "type": "device",
        "companies": [{"ticker": "603986", "name": "兆易创新", "mkt": "CN"}, {"ticker": "688008", "name": "澜起科技", "mkt": "CN"}, {"ticker": "MU", "name": "美光", "mkt": "US"}],
        "elasticity": 2.0, "domestic_rate": 0.3, "policy_weight": 0.9,
        "upstream": [{"node": "wafer", "coef": 0.6}, {"node": "eda_equip", "coef": 0.5}],
        "downstream": [{"node": "ai_server", "coef": 0.7}, {"node": "smartphone", "coef": 0.5}],
    },
    "packaging": {
        "id": "packaging", "name": "半导体封测", "type": "service",
        "companies": [{"ticker": "002156", "name": "通富微电", "mkt": "CN"}, {"ticker": "600584", "name": "长电科技", "mkt": "CN"}],
        "elasticity": 1.3, "domestic_rate": 0.5, "policy_weight": 0.8,
        "upstream": [{"node": "wafer", "coef": 0.7}, {"node": "ai_chip", "coef": 0.5}],
        "downstream": [{"node": "ai_server", "coef": 0.6}, {"node": "smartphone", "coef": 0.4}],
    },
    "llm": {
        "id": "llm", "name": "大模型/AI应用", "type": "service",
        "companies": [{"ticker": "002230", "name": "科大讯飞", "mkt": "CN"}, {"ticker": "300418", "name": "昆仑万维", "mkt": "CN"}, {"ticker": "MSFT", "name": "微软", "mkt": "US"}],
        "elasticity": 1.5, "domestic_rate": 0.5, "policy_weight": 0.7,
        "upstream": [{"node": "ai_chip", "coef": 0.6}, {"node": "data_center", "coef": 0.7}],
        "downstream": [],
    },
    "robot": {
        "id": "robot", "name": "人形机器人", "type": "product",
        "companies": [{"ticker": "300124", "name": "汇川技术", "mkt": "CN"}, {"ticker": "002472", "name": "双环传动", "mkt": "CN"}, {"ticker": "688017", "name": "绿的谐波", "mkt": "CN"}],
        "elasticity": 2.2, "domestic_rate": 0.4, "policy_weight": 0.8,
        "upstream": [{"node": "ai_chip", "coef": 0.5}, {"node": "battery", "coef": 0.5}, {"node": "rare_metal", "coef": 0.4}],
        "downstream": [],
    },
    "innov_drug": {
        "id": "innov_drug", "name": "创新药", "type": "product",
        "companies": [{"ticker": "688235", "name": "百济神州", "mkt": "CN"}, {"ticker": "600276", "name": "恒瑞医药", "mkt": "CN"}, {"ticker": "002821", "name": "凯莱英", "mkt": "CN"}],
        "elasticity": 1.3, "domestic_rate": 0.6, "policy_weight": 0.5,
        "upstream": [{"node": "cxo", "coef": 0.7}, {"node": "resin", "coef": 0.3}],
        "downstream": [],
    },
    "cxo": {
        "id": "cxo", "name": "CXO研发外包", "type": "service",
        "companies": [{"ticker": "603259", "name": "药明康德", "mkt": "CN"}, {"ticker": "300347", "name": "泰格医药", "mkt": "CN"}],
        "elasticity": 1.2, "domestic_rate": 0.7, "policy_weight": 0.4,
        "upstream": [],
        "downstream": [{"node": "innov_drug", "coef": 0.7}],
    },
    "medical_device": {
        "id": "medical_device", "name": "医疗器械", "type": "product",
        "companies": [{"ticker": "300760", "name": "迈瑞医疗", "mkt": "CN"}, {"ticker": "688271", "name": "联影医疗", "mkt": "CN"}],
        "elasticity": 1.1, "domestic_rate": 0.5, "policy_weight": 0.4,
        "upstream": [{"node": "rare_metal", "coef": 0.3}, {"node": "resin", "coef": 0.3}],
        "downstream": [],
    },
    "defense": {
        "id": "defense", "name": "军工电子", "type": "device",
        "companies": [{"ticker": "002179", "name": "中航光电", "mkt": "CN"}, {"ticker": "600893", "name": "航发动力", "mkt": "CN"}],
        "elasticity": 1.4, "domestic_rate": 0.7, "policy_weight": 0.9,
        "upstream": [{"node": "ai_chip", "coef": 0.4}, {"node": "rare_metal", "coef": 0.5}, {"node": "copper", "coef": 0.4}],
        "downstream": [],
    },
    "satellite": {
        "id": "satellite", "name": "卫星互联网", "type": "infra",
        "companies": [{"ticker": "002465", "name": "海格通信", "mkt": "CN"}, {"ticker": "688311", "name": "盟升电子", "mkt": "CN"}],
        "elasticity": 1.7, "domestic_rate": 0.4, "policy_weight": 0.9,
        "upstream": [{"node": "ai_chip", "coef": 0.4}, {"node": "optical_module", "coef": 0.3}],
        "downstream": [],
    },
    "wind": {
        "id": "wind", "name": "风电", "type": "product",
        "companies": [{"ticker": "600875", "name": "东方电气", "mkt": "CN"}, {"ticker": "300274", "name": "阳光电源", "mkt": "CN"}],
        "elasticity": 1.4, "domestic_rate": 0.9, "policy_weight": 0.6,
        "upstream": [{"node": "rare_metal", "coef": 0.4}, {"node": "copper", "coef": 0.5}],
        "downstream": [{"node": "power_grid", "coef": 0.7}],
    },
    "nuclear": {
        "id": "nuclear", "name": "核电", "type": "product",
        "companies": [{"ticker": "601985", "name": "中国核电", "mkt": "CN"}, {"ticker": "003816", "name": "中国广核", "mkt": "CN"}],
        "elasticity": 1.2, "domestic_rate": 0.9, "policy_weight": 0.7,
        "upstream": [{"node": "mine", "coef": 0.5}],
        "downstream": [{"node": "power_grid", "coef": 0.8}],
    },
    "hydrogen": {
        "id": "hydrogen", "name": "氢能", "type": "product",
        "companies": [{"ticker": "600989", "name": "宝丰能源", "mkt": "CN"}, {"ticker": "002733", "name": "雄韬股份", "mkt": "CN"}],
        "elasticity": 2.0, "domestic_rate": 0.5, "policy_weight": 0.8,
        "upstream": [{"node": "oil_gas", "coef": 0.5}],
        "downstream": [{"node": "ev", "coef": 0.4}],
    },
    "white_wine": {
        "id": "white_wine", "name": "白酒", "type": "product",
        "companies": [{"ticker": "600519", "name": "贵州茅台", "mkt": "CN"}, {"ticker": "000858", "name": "五粮液", "mkt": "CN"}],
        "elasticity": 0.8, "domestic_rate": 1.0, "policy_weight": 0.3,
        "upstream": [{"node": "grain", "coef": 0.6}],
        "downstream": [],
    },
    "dairy": {
        "id": "dairy", "name": "乳制品", "type": "product",
        "companies": [{"ticker": "600887", "name": "伊利股份", "mkt": "CN"}, {"ticker": "002570", "name": "贝因美", "mkt": "CN"}],
        "elasticity": 0.7, "domestic_rate": 1.0, "policy_weight": 0.2,
        "upstream": [{"node": "grain", "coef": 0.5}],
        "downstream": [],
    },
    "home_appliance": {
        "id": "home_appliance", "name": "家电", "type": "product",
        "companies": [{"ticker": "000333", "name": "美的集团", "mkt": "CN"}, {"ticker": "000651", "name": "格力电器", "mkt": "CN"}],
        "elasticity": 1.0, "domestic_rate": 0.9, "policy_weight": 0.3,
        "upstream": [{"node": "copper", "coef": 0.5}, {"node": "pcb", "coef": 0.3}],
        "downstream": [],
    },
    "grain": {
        "id": "grain", "name": "粮食/农产品", "type": "raw_material",
        "companies": [{"ticker": "600598", "name": "北大荒", "mkt": "CN"}, {"ticker": "002311", "name": "海大集团", "mkt": "CN"}],
        "elasticity": 1.0, "domestic_rate": 0.9, "policy_weight": 0.5,
        "upstream": [{"node": "mine", "coef": 0.3}, {"node": "oil_gas", "coef": 0.3}],
        "downstream": [{"node": "white_wine", "coef": 0.6}, {"node": "dairy", "coef": 0.5}],
    },
    "steel": {
        "id": "steel", "name": "钢铁", "type": "raw_material",
        "companies": [{"ticker": "600019", "name": "宝钢股份", "mkt": "CN"}, {"ticker": "000708", "name": "中信特钢", "mkt": "CN"}],
        "elasticity": 1.3, "domestic_rate": 0.95, "policy_weight": 0.4,
        "upstream": [{"node": "mine", "coef": 0.7}, {"node": "coal", "coef": 0.6}],
        "downstream": [{"node": "ev", "coef": 0.4}, {"node": "wind", "coef": 0.4}],
    },
    "aluminum": {
        "id": "aluminum", "name": "铝", "type": "raw_material",
        "companies": [{"ticker": "601600", "name": "中国铝业", "mkt": "CN"}, {"ticker": "000807", "name": "云铝股份", "mkt": "CN"}],
        "elasticity": 1.8, "domestic_rate": 0.85, "policy_weight": 0.4,
        "upstream": [{"node": "mine", "coef": 0.8}, {"node": "coal", "coef": 0.5}],
        "downstream": [{"node": "ev", "coef": 0.5}, {"node": "pv_module", "coef": 0.4}],
    },
    "coal": {
        "id": "coal", "name": "煤炭", "type": "raw_material",
        "companies": [{"ticker": "601088", "name": "中国神华", "mkt": "CN"}, {"ticker": "601898", "name": "中煤能源", "mkt": "CN"}],
        "elasticity": 1.1, "domestic_rate": 0.95, "policy_weight": 0.4,
        "upstream": [{"node": "mine", "coef": 0.8}],
        "downstream": [{"node": "steel", "coef": 0.6}, {"node": "aluminum", "coef": 0.5}, {"node": "power_grid", "coef": 0.6}],
    },
    "gold": {
        "id": "gold", "name": "黄金", "type": "raw_material",
        "companies": [{"ticker": "600547", "name": "山东黄金", "mkt": "CN"}, {"ticker": "600489", "name": "中金黄金", "mkt": "CN"}],
        "elasticity": 2.0, "domestic_rate": 0.8, "policy_weight": 0.5,
        "upstream": [{"node": "mine", "coef": 0.9}],
        "downstream": [],
    },
}

# 事件模板（真实世界事件 → 冲击环节 + 方向 + 强度 + 时间窗口）
# direction: "supply"（上游供给受限→下游涨价） / "demand"（下游需求爆发→上游受益）
# 海容例：美国控制芯片 = 供给冲击（芯片供给受限）→ 但国产替代受益 → 光模块/铜箔/PCB/铜 沿链传导
EVENT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "us_chip_restriction": {
        "id": "us_chip_restriction", "name": "美国芯片出口管制",
        "impact_node": "ai_chip", "direction": "supply", "strength": 0.8,
        "window_months": 12,
        "description": "美国对中国芯片/半导体设备出口管制升级 → AI芯片供给受限 → 国产替代加速 + 上游材料涨价传导",
        "policy_weight_scale": 1.3,
    },
    "ai_dc_boom": {
        "id": "ai_dc_boom", "name": "AI数据中心建设潮",
        "impact_node": "data_center", "direction": "demand", "strength": 0.9,
        "window_months": 24,
        "description": "全球AI数据中心资本开支持续扩张 → 上游服务器/光模块/PCB/铜需求爆发",
        "policy_weight_scale": 1.0,
    },
    "copper_price_up": {
        "id": "copper_price_up", "name": "铜价上涨周期",
        "impact_node": "copper", "direction": "supply", "strength": 0.7,
        "window_months": 18,
        "description": "铜矿供给紧张+新能源/算力需求双增 → 铜价上行 → 铜箔/PCB成本传导",
        "policy_weight_scale": 1.0,
    },
    "export_control_materials": {
        "id": "export_control_materials", "name": "稀有金属出口管制",
        "impact_node": "rare_metal", "direction": "supply", "strength": 0.75,
        "window_months": 12,
        "description": "中国对稀土/稀有金属出口管制 → 全球半导体/电池材料供给受限 → 上游矿企受益",
        "policy_weight_scale": 1.2,
    },
    "ev_demand_surge": {
        "id": "ev_demand_surge", "name": "新能源汽车渗透率提升",
        "impact_node": "ev", "direction": "demand", "strength": 0.6,
        "window_months": 36,
        "description": "全球新能源车渗透率持续提升 → 电池/铜/PCB需求增长",
        "policy_weight_scale": 1.0,
    },
}


class SupplyChainEngine:
    """产业链双向链接引擎"""

    def __init__(self, graph: Optional[Dict] = None):
        self.graph = graph or CHAIN_GRAPH
        # 反向邻接（下游→上游 反向边），用于双向传播
        self._reverse_edges: Dict[str, List[Dict]] = {}
        for nid, node in self.graph.items():
            for up in node.get("upstream", []):
                self._reverse_edges.setdefault(up["node"], []).append(
                    {"node": nid, "coef": up["coef"]})

    # ---------- 核心：事件 → 双向传播 ----------
    def propagate(self, event: Dict[str, Any], max_hops: int = 4) -> Dict[str, Any]:
        """事件注入 → 沿产业链双向传播（正向+反向）→ 各环节冲击分"""
        impact_node = event.get("impact_node")
        if impact_node not in self.graph:
            return {"error": f"unknown node {impact_node}", "results": []}

        direction = event.get("direction", "demand")  # supply=上游供给冲击, demand=下游需求冲击
        strength = float(event.get("strength", 0.5))
        scale = float(event.get("policy_weight_scale", 1.0))

        # 冲击分记录: {node_id: {score, path, hops, direction}}
        impact = {}
        visited = set()

        def _forward(node_id: str, cur_score: float, path: List[str], hops: int, direction_flow: str):
            """沿产业链传导：direction_flow='down'=向下游, 'up'=向上游
            分数模型：每跳 cur * coef(≤1衰减) * 弹性(局部放大) * 国产替代(局部加成)
            保证随跳数单调递减（coef 连乘 < 1），避免多路径指数爆炸
            """
            if hops > max_hops:
                return
            key = (node_id, hops)
            if key in visited:
                return
            visited.add(key)

            node = self.graph[node_id]
            # 弹性放大（每跳最多一次，限制 ≤2.5 防爆炸）
            elasticity = min(node.get("elasticity", 1.0), 2.5)
            # 全局距离衰减：每跳 ×0.6（路径越长影响越弱，5跳后 ≈0.078）
            dist_decay = 0.6 ** hops
            score = cur_score * elasticity * dist_decay
            # 国产替代逻辑：供给受限时国产化率低的环节 = 替代受益大（上限 +40%）
            if direction == "supply" and direction_flow == "down":
                subst = min((1 - node.get("domestic_rate", 0.5)) * 0.5, 0.4)
                score *= (1 + subst)

            if node_id not in impact or score > impact[node_id]["score"]:
                impact[node_id] = {
                    "score": round(score, 2),
                    "path": path + [node_id],
                    "hops": hops,
                    "direction": direction_flow,
                    "name": node["name"],
                    "type": node.get("type", ""),
                }

            # 继续传播（coef 连乘天然衰减：路径越长分数越低）
            if direction_flow == "down":
                for edge in node.get("downstream", []):
                    _forward(edge["node"], score * edge["coef"], impact[node_id]["path"], hops + 1, "down")
            else:
                for edge in node.get("upstream", []):
                    _forward(edge["node"], score * edge["coef"], impact[node_id]["path"], hops + 1, "up")

        # 起点：冲击环节自身
        start_score = strength * scale * self.graph[impact_node].get("elasticity", 1.0)
        impact[impact_node] = {
            "score": round(start_score, 2),
            "path": [impact_node],
            "hops": 0,
            "direction": "origin",
            "name": self.graph[impact_node]["name"],
            "type": self.graph[impact_node].get("type", ""),
        }
        visited = set()
        visited.add((impact_node, 0))
        node = self.graph[impact_node]

        # 双向：向下游传播 + 向上游传播（海容核心：双向链接）
        for edge in node.get("downstream", []):
            _forward(edge["node"], start_score * edge["coef"], [impact_node], 1, "down")
        visited = set()
        visited.add((impact_node, 0))
        for edge in node.get("upstream", []):
            _forward(edge["node"], start_score * edge["coef"], [impact_node], 1, "up")

        # 分类受益/受损
        results = []
        for nid, info in sorted(impact.items(), key=lambda x: -x[1]["score"]):
            node = self.graph[nid]
            direction_label = "受益" if info["direction"] != "origin" else "冲击源"
            # 受损判定：仅当冲击环节本身是科技设备类(芯片/设备/存储)时才触发国产替代受损逻辑
            # 原材料冲击(铜/稀土/油)是成本传导，不该标"进口依赖受损"
            impact_node_type = self.graph[impact_node].get("type", "")
            is_tech_supply = (direction == "supply" and impact_node_type in ("device", "component", "service"))
            if is_tech_supply and info["direction"] == "down" and info["hops"] >= 2:
                if node.get("domestic_rate", 0.5) < 0.35:
                    direction_label = "受损(进口依赖)"
            if direction == "demand" and info["direction"] == "up" and info["hops"] >= 2:
                direction_label = "受益(上游需求)"
            if info["direction"] == "origin":
                direction_label = "冲击源"

            results.append({
                "node_id": nid,
                "name": node["name"],
                "type": node.get("type", ""),
                "score": info["score"],
                "direction": direction_label,
                "hops": info["hops"],
                "path": [self.graph[p]["name"] for p in info["path"]],
                "companies": node.get("companies", []),
                "domestic_rate": node.get("domestic_rate", 0.5),
            })
        return {
            "event": event.get("name", ""),
            "event_id": event.get("id", ""),
            "description": event.get("description", ""),
            "direction": direction,
            "window_months": event.get("window_months", 12),
            "impact_node": self.graph[impact_node]["name"],
            "results": results,
        }

    # ---------- 预测时间轴 ----------
    def forecast(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """预测时间轴：沿产业链传导的时间节奏（上游先动→下游后动）"""
        base = datetime.now()
        direction = event.get("direction", "demand")
        if direction == "supply":
            # 供给冲击：上游(0-3月) → 中游(3-6月) → 下游(6-12月)
            phases = [
                {"phase": "冲击初期(0-3月)", "start": base, "end": base + timedelta(days=90),
                 "desc": "冲击环节价格异动，上游材料最先反应"},
                {"phase": "传导中期(3-6月)", "start": base + timedelta(days=90), "end": base + timedelta(days=180),
                 "desc": "中游成本传导/国产替代加速，替代标的启动"},
                {"phase": "兑现期(6-12月)", "start": base + timedelta(days=180), "end": base + timedelta(days=365),
                 "desc": "下游终端涨价/供应链重构，龙头格局重塑"},
            ]
        else:
            phases = [
                {"phase": "需求启动(0-3月)", "start": base, "end": base + timedelta(days=90),
                 "desc": "终端需求数据验证，下游最先受益"},
                {"phase": "景气扩散(3-6月)", "start": base + timedelta(days=90), "end": base + timedelta(days=180),
                 "desc": "订单向上游传导，中游设备/材料放量"},
                {"phase": "供给瓶颈(6-24月)", "start": base + timedelta(days=180), "end": base + timedelta(days=720),
                 "desc": "上游资源/材料价格弹性爆发，资源股主升"},
            ]
        return {
            "event": event.get("name", ""),
            "direction": direction,
            "phases": phases,
            "window_months": event.get("window_months", 12),
        }

    # ---------- 机会提取（受益环节 → 代表公司 → 可交易清单）----------
    def extract_opportunities(self, event: Dict[str, Any], top_n: int = 8) -> List[Dict[str, Any]]:
        prop = self.propagate(event)
        if "error" in prop:
            return []
        opps = []
        for r in prop["results"]:
            if "受益" not in r["direction"]:
                continue
            for c in r["companies"][:3]:
                opps.append({
                    "node": r["name"],
                    "path": " → ".join(r["path"]),
                    "score": r["score"],
                    "ticker": c["ticker"],
                    "company": c["name"],
                    "mkt": c.get("mkt", ""),
                    "domestic_rate": r["domestic_rate"],
                    "why": f"{prop['event']} 传导至 {r['name']}（{r['direction']}）",
                })
        opps.sort(key=lambda x: -x["score"])
        return opps[:top_n]

    # ---------- 报告 ----------
    def to_report(self, event: Dict[str, Any]) -> str:
        prop = self.propagate(event)
        fc = self.forecast(event)
        if "error" in prop:
            return f"### 🔗 产业链传导\n\n错误: {prop['error']}"
        lines = [
            f"### 🔗 产业链双向传导（{prop['event']}）",
            "",
            f"**事件**: {prop.get('description', '')}",
            f"**冲击环节**: {prop['impact_node']} | **传导方向**: {'上游供给冲击' if prop['direction'] == 'supply' else '下游需求爆发'} | **窗口**: {prop['window_months']}个月",
            "",
            "| 环节 | 方向 | 冲击分 | 传导路径 | 代表公司 |",
            "|:-----|:-----|:------|:---------|:---------|",
        ]
        for r in prop["results"][:10]:
            companies = " / ".join(c["name"] for c in r["companies"][:2])
            lines.append(f"| {r['name']} | {r['direction']} | {r['score']} | {'→'.join(r['path'][-3:])} | {companies} |")
        lines.append("")
        lines.append("**预测时间轴**:")
        for ph in fc["phases"]:
            lines.append(f"- {ph['phase']}: {ph['desc']}")
        lines.append("")
        lines.append("**机会清单**（受益标的 Top6）:")
        for opp in self.extract_opportunities(event, top_n=6):
            lines.append(f"- 🎯 {opp['company']}({opp['ticker']}) — {opp['node']} 冲击分{opp['score']} | {opp['path']}")
        return "\n".join(lines)


# ============================================================
# 预设场景（一键演示海容例：美国限芯片 → 光模块 → 铜箔 → PCB → 金属铜）
# ============================================================
def build_preset_scenarios() -> Dict[str, Dict[str, Any]]:
    eng = SupplyChainEngine()
    return {
        "us_chip_restriction": {
            "event": EVENT_TEMPLATES["us_chip_restriction"],
            "report": eng.to_report(EVENT_TEMPLATES["us_chip_restriction"]),
            "opportunities": eng.extract_opportunities(EVENT_TEMPLATES["us_chip_restriction"], top_n=8),
            "propagation": eng.propagate(EVENT_TEMPLATES["us_chip_restriction"]),
            "forecast": eng.forecast(EVENT_TEMPLATES["us_chip_restriction"]),
        },
        "ai_dc_boom": {
            "event": EVENT_TEMPLATES["ai_dc_boom"],
            "report": eng.to_report(EVENT_TEMPLATES["ai_dc_boom"]),
            "opportunities": eng.extract_opportunities(EVENT_TEMPLATES["ai_dc_boom"], top_n=8),
            "propagation": eng.propagate(EVENT_TEMPLATES["ai_dc_boom"]),
            "forecast": eng.forecast(EVENT_TEMPLATES["ai_dc_boom"]),
        },
    }


if __name__ == "__main__":
    eng = SupplyChainEngine()
    print("=" * 70)
    print("场景1: 美国芯片出口管制（海容例）")
    print("=" * 70)
    print(eng.to_report(EVENT_TEMPLATES["us_chip_restriction"]))
    print()
    print("=" * 70)
    print("场景2: AI数据中心建设潮")
    print("=" * 70)
    print(eng.to_report(EVENT_TEMPLATES["ai_dc_boom"]))

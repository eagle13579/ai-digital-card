"""
双链发现 + 群体智能预判引擎 (Dual-Link Discovery & Swarm Forecast)
===================================================================
2026-08-08 海容指示：学习 MiroFish + Obsidian 两大工具的逻辑融入产业链系统

【Obsidian 双向链接逻辑】（D:\obsidian = Obsidian 软件/笔记工具）
  - 每篇笔记是一个节点，[[双链]] 建立节点间双向链接
  - 从任意节点沿链接跳转 → 发现隐藏路径/关联知识
  - 图谱视图可视化节点网络
  → 落地: discover() 从任意产业链节点出发沿上下游双链跳转，发现机会路径+关联公司

【MiroFish 群体智能预测逻辑】（github.com/666ghj/MiroFish 70.7k★，盛大出品）
  - 种子信息 → 实体图谱 → 生成模拟配置(人设/事件/平台)
  - OASIS 多智能体自由交互、社会演化（每轮各自行动→互相影响）
  - 多轮收敛后 ReportAgent 生成预测报告
  → 落地: swarm_forecast() 把每个产业链环节当作智能体，事件冲击后多轮交互演化
    （每轮: 环节根据上下游状态调整自身价格/供需/情绪 → 传给相邻环节 → 收敛预测）

版本: v1.0.0
"""

import json
from typing import Dict, Any, List, Optional

from .supply_chain import CHAIN_GRAPH, EVENT_TEMPLATES


class DualLinkEngine:
    """Obsidian 双链 + MiroFish 群体智能 融合引擎"""

    def __init__(self, graph: Optional[Dict] = None):
        self.graph = graph or CHAIN_GRAPH
        # 反向邻接（Obsidian 双链：每条边都是双向的）
        self._back_edges: Dict[str, List[Dict]] = {}
        for nid, node in self.graph.items():
            for up in node.get("upstream", []):
                self._back_edges.setdefault(up["node"], []).append({"node": nid, "coef": up["coef"]})
            for dn in node.get("downstream", []):
                self._back_edges.setdefault(dn["node"], []).append({"node": nid, "coef": dn["coef"]})

    # ============================================================
    # Obsidian 双链发现：从任意节点沿链接跳转
    # ============================================================
    def discover(self, seed: str, max_hops: int = 3) -> Dict[str, Any]:
        """从任意节点/关键词出发，沿双向链接跳转，发现机会路径
        seed 可以是节点id或中文名或关键词（模糊匹配）
        """
        # 定位种子节点（精确匹配优先，再模糊）
        target = None
        # 常用词 alias 映射（用户口语 → 标准节点）
        alias_map = {
            "铜": "copper", "金属铜": "copper", "电解铜": "copper", "铜矿": "copper",
            "芯片": "ai_chip", "gpu": "ai_chip", "显卡": "ai_chip",
            "光模块": "optical_module", "光": "optical_module", "光通讯": "optical_module",
            "pcb": "pcb", "电路板": "pcb", "印制电路板": "pcb",
            "稀土": "rare_metal", "锂": "rare_metal", "钴": "rare_metal",
            "服务器": "ai_server", "数据中心": "data_center", "云": "data_center",
            "电池": "battery", "新能源车": "ev", "电动车": "ev", "汽车": "ev",
            "手机": "smartphone", "光伏": "solar", "硅": "poly_silicon",
            "设备": "eda_equip", "晶圆": "wafer", "硅片": "wafer",
            "矿": "mine", "电力": "power_grid", "电网": "power_grid",
            "树脂": "resin", "油": "oil_gas", "气": "oil_gas",
        }
        if seed in alias_map:
            target = alias_map[seed]
        if target is None:
            for nid, node in self.graph.items():
                if nid == seed or node["name"] == seed:
                    target = nid
                    break
        if target is None:
            # 模糊匹配选最短名（避免「铜」先撞上「铜箔」）
            fuzzy = None
            for nid, node in self.graph.items():
                if seed in node["name"]:
                    if fuzzy is None or len(node["name"]) < len(self.graph[fuzzy]["name"]):
                        fuzzy = nid
            target = fuzzy
        # 关键词模糊匹配（在公司和描述里找）
        if target is None:
            for nid, node in self.graph.items():
                for c in node.get("companies", []):
                    if seed.lower() in c["name"].lower() or seed.lower() in str(c.get("ticker", "")).lower():
                        target = nid
                        break
                if target:
                    break
        if target is None:
            return {"error": f"未找到节点/关键词: {seed}", "seed": seed, "results": []}

        # BFS 双向跳转（Obsidian 双链精髓：正反向都走）
        from collections import deque
        visited = {target}
        frontier = [(target, 0, [self.graph[target]["name"]])]
        results = []
        while frontier:
            cur, depth, path = frontier.pop(0)
            if depth > max_hops:
                continue
            node = self.graph[cur]
            results.append({
                "node_id": cur, "name": node["name"], "type": node.get("type", ""),
                "hops": depth, "path": path,
                "companies": node.get("companies", []),
                "domestic_rate": node.get("domestic_rate", 0.5),
                "elasticity": node.get("elasticity", 1.0),
            })
            if depth >= max_hops:
                continue
            # 下游
            for edge in node.get("downstream", []):
                if edge["node"] not in visited:
                    visited.add(edge["node"])
                    frontier.append((edge["node"], depth + 1, path + [self.graph[edge["node"]]["name"]]))
            # 上游（反向 = 双链）
            for edge in node.get("upstream", []):
                if edge["node"] not in visited:
                    visited.add(edge["node"])
                    frontier.append((edge["node"], depth + 1, path + [self.graph[edge["node"]]["name"]]))
            # 反向邻居（别人指向它）
            for edge in self._back_edges.get(cur, []):
                if edge["node"] not in visited:
                    visited.add(edge["node"])
                    frontier.append((edge["node"], depth + 1, path + [self.graph[edge["node"]]["name"]]))

        results.sort(key=lambda x: x["hops"])
        return {
            "seed": seed,
            "seed_node": self.graph[target]["name"],
            "logic": "Obsidian 双向链接：从种子节点沿上下游+反向链接跳转，发现关联产业与公司",
            "found": len(results),
            "results": results,
        }

    def find_path(self, a: str, b: str) -> List[List[str]]:
        """找任意两节点间的所有传导路径（双链最短路径）"""
        na = nb = None
        for nid, node in self.graph.items():
            if nid == a or node["name"] == a or a in node["name"]:
                na = nid
            if nid == b or node["name"] == b or b in node["name"]:
                nb = nid
        if not na or not nb or na == nb:
            return []
        # BFS 找所有路径（限制长度）
        all_paths = []
        from collections import deque
        q = deque([[na]])
        while q:
            path = q.popleft()
            if len(path) > 5:
                continue
            cur = path[-1]
            if cur == nb:
                all_paths.append([self.graph[p]["name"] for p in path])
                continue
            node = self.graph[cur]
            nbrs = [e["node"] for e in node.get("downstream", [])] + \
                   [e["node"] for e in node.get("upstream", [])] + \
                   [e["node"] for e in self._back_edges.get(cur, [])]
            for nb_ in nbrs:
                if nb_ not in path:
                    q.append(path + [nb_])
        # 去重（保留路径字符串唯一）
        seen = set()
        unique = []
        for p in all_paths:
            key = "|".join(p)
            if key not in seen:
                seen.add(key)
                unique.append(p)
        return unique[:10]

    # ============================================================
    # MiroFish 群体智能预判：产业链环节=智能体，多轮交互演化
    # ============================================================
    def swarm_forecast(self, event: Dict[str, Any], rounds: int = 4) -> Dict[str, Any]:
        """群体智能预测：每个产业链环节是智能体，事件冲击后多轮交互演化
        每轮: 环节根据冲击强度+上下游状态 调整自身(价格/供需/情绪) → 传播给相邻
        收敛: 多轮后达到平衡 → 输出预测（涨价/受益/受损/替代机会）
        """
        impact_node = event.get("impact_node")
        if impact_node not in self.graph:
            return {"error": f"unknown node {impact_node}"}

        direction = event.get("direction", "demand")
        strength = float(event.get("strength", 0.5))
        scale = float(event.get("policy_weight_scale", 1.0))

        # 初始化所有环节智能体状态
        agents = {}
        for nid, node in self.graph.items():
            agents[nid] = {
                "price_pressure": 0.0,   # 价格压力 (-1..1, 正=涨价压力)
                "demand_change": 0.0,     # 需求变化 (-1..1)
                "supply_change": 0.0,     # 供给变化 (-1..1)
                "sentiment": 0.0,         # 情绪 (-1..1)
                "node": node["name"],
                "type": node.get("type", ""),
                "elasticity": node.get("elasticity", 1.0),
                "domestic_rate": node.get("domestic_rate", 0.5),
            }

        # 事件冲击种子（第0轮）
        seed = strength * scale
        if direction == "supply":
            agents[impact_node]["supply_change"] = -seed          # 供给收缩
            agents[impact_node]["price_pressure"] = seed * 1.5    # 涨价压力大
            # 国产替代需求：供给受限 → 冲击节点的上游材料需求↑（替代采购）
            agents[impact_node]["demand_change"] = seed * 0.4
        else:
            agents[impact_node]["demand_change"] = seed           # 需求爆发
            agents[impact_node]["price_pressure"] = seed * 0.8
        agents[impact_node]["sentiment"] = seed

        history = []
        for rnd in range(1, rounds + 1):
            # 每轮：每个环节根据 自身状态 + 上下游邻居状态 更新
            new_state = {k: dict(v) for k, v in agents.items()}
            for nid, node in self.graph.items():
                ag = agents[nid]
                # 从上游接收（上游涨价 → 本环节成本↑ → 涨价压力）
                up_pressure = 0.0
                for up in node.get("upstream", []):
                    up_ag = agents[up["node"]]
                    up_pressure += up_ag["price_pressure"] * up["coef"] * 0.6
                # 从下游接收（下游需求↑ → 本环节需求↑）
                dn_pressure = 0.0
                for dn in node.get("downstream", []):
                    dn_ag = agents[dn["node"]]
                    dn_pressure += dn_ag["demand_change"] * dn["coef"] * 0.6
                # 从反向邻居接收（别人依赖我 → 我的需求）
                back_pressure = 0.0
                for be in self._back_edges.get(nid, []):
                    b_ag = agents[be["node"]]
                    back_pressure += b_ag["demand_change"] * be["coef"] * 0.5

                # 状态更新（带衰减）
                decay = 0.85
                new_state[nid]["price_pressure"] = ag["price_pressure"] * decay + \
                    (up_pressure + dn_pressure) * ag["elasticity"] * 0.4
                new_state[nid]["demand_change"] = ag["demand_change"] * decay + \
                    (dn_pressure + back_pressure) * 0.5
                new_state[nid]["supply_change"] = ag["supply_change"] * decay + up_pressure * 0.3
                # 情绪 = 供需差 + 自身
                new_state[nid]["sentiment"] = ag["sentiment"] * decay + \
                    (new_state[nid]["demand_change"] - new_state[nid]["supply_change"]) * 0.6

            agents = new_state
            # 记录快照（收敛检查）
            max_delta = max(abs(agents[k]["price_pressure"] - old_ag["price_pressure"])
                            for k, old_ag in history[-1].items()) if history else 99.0
            history.append({k: dict(v) for k, v in agents.items()})
            if max_delta < 0.01 and rnd >= 2:
                break

        # 收敛结果 → 分类
        results = []
        for nid, ag in agents.items():
            node = self.graph[nid]
            # 受益判定: 需求↑ 且 涨价压力↑ 且 供给没崩
            score = ag["price_pressure"] * 0.5 + ag["demand_change"] * 0.3 + ag["sentiment"] * 0.2
            if ag["supply_change"] < -0.2 and ag["domestic_rate"] < 0.4:
                label = "受损(进口依赖)"
                score -= 0.5
            elif ag["price_pressure"] > 0.15:
                label = "受益(涨价)"
            elif ag["demand_change"] > 0.1:
                label = "受益(需求)"
            elif ag["supply_change"] < -0.1:
                label = "承压(供给)"
            else:
                label = "平稳"
            results.append({
                "node_id": nid, "name": ag["node"], "type": ag["type"],
                "label": label, "score": round(score, 3),
                "price_pressure": round(ag["price_pressure"], 3),
                "demand_change": round(ag["demand_change"], 3),
                "supply_change": round(ag["supply_change"], 3),
                "sentiment": round(ag["sentiment"], 3),
                "companies": node.get("companies", []),
            })

        results.sort(key=lambda x: -x["score"])
        return {
            "event": event.get("name", ""),
            "event_id": event.get("id", ""),
            "logic": "MiroFish 群体智能预判：产业链每环节=智能体，事件冲击后多轮交互演化收敛",
            "rounds_actual": len(history),
            "direction": direction,
            "results": results,
        }

    def swarm_report(self, event: Dict[str, Any]) -> str:
        """群体智能预判 Markdown 报告"""
        f = self.swarm_forecast(event)
        if "error" in f:
            return f"### 🧠 群体智能预判\n\n错误: {f['error']}"
        lines = [
            f"### 🧠 群体智能预判（{f['event']}）",
            "",
            f"**逻辑**: {f['logic']}（共 {f['rounds_actual']} 轮演化收敛）",
            "",
            "| 环节 | 预判 | 价格压力 | 需求 | 供给 | 情绪 | 代表公司 |",
            "|:-----|:-----|:--------|:-----|:-----|:-----|:---------|",
        ]
        for r in f["results"][:12]:
            companies = " / ".join(c["name"] for c in r["companies"][:2])
            lines.append(f"| {r['name']} | {r['label']} | {r['price_pressure']:.2f} | {r['demand_change']:+.2f} | {r['supply_change']:+.2f} | {r['sentiment']:+.2f} | {companies} |")
        lines.append("")
        # 预判结论
        winners = [r for r in f["results"] if "受益" in r["label"]][:5]
        losers = [r for r in f["results"] if "受损" in r["label"] or "承压" in r["label"]][:3]
        lines.append("**预判结论**:")
        if winners:
            lines.append("- 🟢 受益链: " + " → ".join(r["name"] for r in winners))
        if losers:
            lines.append("- 🔴 承压链: " + " → ".join(r["name"] for r in losers))
        return "\n".join(lines)


def build_dual_link_preset() -> Dict[str, Any]:
    eng = DualLinkEngine()
    return {
        "engine": "双链发现+群体智能预判引擎 v1.0.0",
        "sources": [
            "Obsidian 双向链接: 节点+双链，任意节点沿链接跳转发现隐藏路径",
            "MiroFish 群体智能: 种子→图谱→多智能体演化→预测 (github.com/666ghj/MiroFish 70.7k★)",
        ],
        "discover_demo": eng.discover("铜", max_hops=2),
        "find_path_demo": eng.find_path("光模块", "金属铜"),
        "swarm_demo": eng.swarm_report(EVENT_TEMPLATES["us_chip_restriction"]),
        "swarm_data": eng.swarm_forecast(EVENT_TEMPLATES["us_chip_restriction"]),
    }


if __name__ == "__main__":
    eng = DualLinkEngine()
    print("=" * 70)
    print("【Obsidian 双链】从「铜」出发跳转发现")
    print("=" * 70)
    d = eng.discover("铜", max_hops=2)
    for r in d["results"][:12]:
        comps = " / ".join(c["name"] for c in r["companies"][:2])
        print(f"  [{r['hops']}] {r['name']} ({r['type']}) → {'→'.join(r['path'][-2:])} | {comps}")
    print()
    print("=" * 70)
    print("【Obsidian 双链】光模块 → 金属铜 传导路径")
    print("=" * 70)
    for p in eng.find_path("光模块", "金属铜"):
        print("  ", " → ".join(p))
    print()
    print("=" * 70)
    print("【MiroFish 群体智能】美国芯片管制 预判")
    print("=" * 70)
    print(eng.swarm_report(EVENT_TEMPLATES["us_chip_restriction"]))

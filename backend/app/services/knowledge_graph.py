"""
AI数字名片 — 名片人际关系知识图谱 (Knowledge Graph)
=====================================================
从 User / Brochure / Tag / MatchRecord / TrustNetwork 表聚合数据，
构建 person-company-industry-tag 图谱，支持网络查询、洞察分析、连接推荐。

节点类型: person, company, industry, tag, location
边类型:   works_at, tagged_as, matched, trusted, same_industry, same_company, same_location
"""
from __future__ import annotations

import json
import logging
from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.tag import UserTag, MatchRecord
from app.models.trust import TrustNetwork

logger = logging.getLogger(__name__)


# ── 数据结构 ──────────────────────────────────────────────────────────────


class GraphNode:
    """图谱节点"""

    def __init__(self, node_id: str, node_type: str, label: str, **attrs):
        self.id = node_id
        self.type = node_type
        self.label = label
        self.attrs = attrs  # 额外属性

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            **self.attrs,
        }


class GraphEdge:
    """图谱边"""

    def __init__(self, source: str, target: str, relation: str, weight: float = 1.0, **attrs):
        self.source = source
        self.target = target
        self.relation = relation
        self.weight = weight
        self.attrs = attrs

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
            "weight": self.weight,
            **self.attrs,
        }


class KnowledgeGraph:
    """名片人际关系知识图谱构建器"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.nodes: dict[str, GraphNode] = {}  # id -> node
        self.edges: list[GraphEdge] = []

    # ── 节点构建 ──────────────────────────────────────────────────────────

    def _add_person_node(self, user: User) -> str:
        nid = f"person:{user.id}"
        if nid not in self.nodes:
            self.nodes[nid] = GraphNode(
                node_id=nid,
                node_type="person",
                label=user.name or f"用户#{user.id}",
                user_id=user.id,
                name=user.name,
                company=user.company,
                title=user.title,
                avatar=user.avatar,
                intro=user.intro[:200] if user.intro else "",
            )
        return nid

    def _add_company_node(self, company_name: str) -> str:
        if not company_name:
            return ""
        nid = f"company:{company_name}"
        if nid not in self.nodes:
            self.nodes[nid] = GraphNode(
                node_id=nid,
                node_type="company",
                label=company_name,
                name=company_name,
            )
        return nid

    def _add_tag_node(self, tag: str) -> str:
        if not tag:
            return ""
        nid = f"tag:{tag}"
        if nid not in self.nodes:
            self.nodes[nid] = GraphNode(
                node_id=nid,
                node_type="tag",
                label=tag,
                name=tag,
            )
        return nid

    def _add_industry_node(self, industry: str) -> str:
        """从 brochure purpose 或 tag 推断行业"""
        if not industry:
            return ""
        nid = f"industry:{industry}"
        if nid not in self.nodes:
            self.nodes[nid] = GraphNode(
                node_id=nid,
                node_type="industry",
                label=industry,
                name=industry,
            )
        return nid

    # ── 边构建 ────────────────────────────────────────────────────────────

    def _add_edge(self, source: str, target: str, relation: str,
                  weight: float = 1.0, **attrs):
        """添加边，若已存在同类边则累加权重"""
        self.edges.append(GraphEdge(source, target, relation, weight, **attrs))

    # ── 图谱构建 ──────────────────────────────────────────────────────────

    async def build(self) -> dict[str, Any]:
        """从数据库聚合构建完整知识图谱，返回 {nodes, edges, stats}"""
        self.nodes.clear()
        self.edges.clear()

        # 1. 加载用户及其企业
        result = await self.db.execute(select(User))
        users: list[User] = list(result.scalars().all())
        logger.info("知识图谱: 加载 %d 个用户", len(users))

        for u in users:
            pid = self._add_person_node(u)
            # works_at: 用户 -> 公司
            if u.company:
                cid = self._add_company_node(u.company)
                if cid:
                    self._add_edge(pid, cid, "works_at", weight=1.0)

        # 2. 加载用户标签
        result = await self.db.execute(select(UserTag))
        tags: list[UserTag] = list(result.scalars().all())
        logger.info("知识图谱: 加载 %d 个标签", len(tags))

        tag_count: dict[str, int] = defaultdict(int)
        for t in tags:
            pid = f"person:{t.user_id}"
            if pid not in self.nodes:
                continue  # 用户可能已被删除
            tid = self._add_tag_node(t.tag)
            if tid:
                self._add_edge(pid, tid, "tagged_as",
                               weight=t.weight,
                               tag_type=t.tag_type,
                               source=t.source)
                tag_count[t.tag] += 1

        # 从频次高的标签推断行业节点
        for tag_name, count in tag_count.items():
            if count >= 2:  # 至少2人使用 -> 视为行业标签
                iid = self._add_industry_node(tag_name)
                tid = f"tag:{tag_name}"
                # industry <-> tag 关联
                self._add_edge(tid, iid, "represents_industry", weight=min(count, 10))

        # 3. 匹配关系
        result = await self.db.execute(
            select(MatchRecord).where(MatchRecord.status.in_(["matched", "confirmed"]))
        )
        matches: list[MatchRecord] = list(result.scalars().all())
        logger.info("知识图谱: 加载 %d 条匹配记录", len(matches))

        for m in matches:
            a = f"person:{m.user_a_id}"
            b = f"person:{m.user_b_id}"
            if a in self.nodes and b in self.nodes:
                self._add_edge(a, b, "matched",
                               weight=m.match_score,
                               match_id=m.id,
                               status=m.status)
                # 共同标签 -> same_industry 边
                if m.common_tags and m.common_tags != "[]":
                    try:
                        common = json.loads(m.common_tags)
                        for ct in common:
                            # 确保标签节点存在
                            self._add_tag_node(ct)
                            iid = self._add_industry_node(ct)
                            if iid:
                                self._add_edge(a, iid, "same_industry", weight=0.8)
                                self._add_edge(b, iid, "same_industry", weight=0.8)
                    except (json.JSONDecodeError, TypeError):
                        pass

        # 4. 信任关系
        result = await self.db.execute(select(TrustNetwork))
        trusts: list[TrustNetwork] = list(result.scalars().all())
        logger.info("知识图谱: 加载 %d 条信任关系", len(trusts))

        for t in trusts:
            a = f"person:{t.user_id}"
            b = f"person:{t.trusted_user_id}"
            if a in self.nodes and b in self.nodes:
                self._add_edge(a, b, "trusted", weight=1.0, trust_id=t.id)

        # 5. 同公司关联
        company_users: dict[str, list[str]] = defaultdict(list)
        for u in users:
            if u.company:
                company_users[u.company].append(f"person:{u.id}")
        for company, person_ids in company_users.items():
            if len(person_ids) >= 2:
                cid = f"company:{company}"
                for i in range(len(person_ids)):
                    for j in range(i + 1, len(person_ids)):
                        self._add_edge(person_ids[i], person_ids[j],
                                       "same_company", weight=0.7)

        # 6. 同行业关联（通过标签）
        tag_users: dict[str, list[str]] = defaultdict(list)
        for t in tags:
            pid = f"person:{t.user_id}"
            if pid in self.nodes:
                tag_users[t.tag].append(pid)
        for tag_name, person_ids in tag_users.items():
            if len(person_ids) >= 2:
                for i in range(len(person_ids)):
                    for j in range(i + 1, len(person_ids)):
                        self._add_edge(person_ids[i], person_ids[j],
                                       "same_industry", weight=0.5,
                                       via_tag=tag_name)

        # 去重合并同类边（累加权重）
        self._deduplicate_edges()

        stats = {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "node_types": self._count_node_types(),
            "edge_types": self._count_edge_types(),
        }

        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
            "stats": stats,
        }

    def _deduplicate_edges(self):
        """合并 source-target-relation 相同的边，权重累加"""
        seen: dict[tuple[str, str, str], float] = {}
        merged: list[GraphEdge] = []
        extras: dict[tuple[str, str, str], dict] = {}

        for e in self.edges:
            key = (e.source, e.target, e.relation)
            if key in seen:
                seen[key] += e.weight
            else:
                seen[key] = e.weight
                extras[key] = e.attrs
                merged.append(e)

        for me in merged:
            key = (me.source, me.target, me.relation)
            me.weight = round(seen[key], 2)

        self.edges = merged

    def _count_node_types(self) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for n in self.nodes.values():
            counts[n.type] += 1
        return dict(counts)

    def _count_edge_types(self) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for e in self.edges:
            counts[e.relation] += 1
        return dict(counts)

    # ── 用户子图 ──────────────────────────────────────────────────────────

    async def get_user_network(self, user_id: int, depth: int = 2) -> dict[str, Any]:
        """获取指定用户的 ego 网络（自我中心网络）"""
        await self.build()
        pid = f"person:{user_id}"
        if pid not in self.nodes:
            return {"nodes": [], "edges": [], "central": None}

        # BFS 提取子图
        visited_nodes: set[str] = {pid}
        visited_edges: list[GraphEdge] = []
        frontier = {pid}
        for _ in range(depth):
            if not frontier:
                break
            next_frontier: set[str] = set()
            for e in self.edges:
                if e.source in frontier and e.target not in visited_nodes:
                    visited_nodes.add(e.target)
                    next_frontier.add(e.target)
                    visited_edges.append(e)
                elif e.target in frontier and e.source not in visited_nodes:
                    visited_nodes.add(e.source)
                    next_frontier.add(e.source)
                    visited_edges.append(e)
            frontier = next_frontier

        # 也收录连接这些节点的边
        edge_set = {(e.source, e.target, e.relation) for e in visited_edges}
        for e in self.edges:
            key = (e.source, e.target, e.relation)
            if key not in edge_set and e.source in visited_nodes and e.target in visited_nodes:
                visited_edges.append(e)
                edge_set.add(key)

        central = self.nodes[pid].to_dict()
        return {
            "central": central,
            "nodes": [self.nodes[nid].to_dict() for nid in visited_nodes],
            "edges": [e.to_dict() for e in visited_edges],
        }

    # ── 用户洞察 ──────────────────────────────────────────────────────────

    async def get_user_insights(self, user_id: int) -> dict[str, Any]:
        """分析用户在图谱中的位置和关系洞察"""
        await self.build()
        pid = f"person:{user_id}"
        if pid not in self.nodes:
            return {"error": "用户不在图谱中"}

        # 统计关联
        connected_people: set[str] = set()
        tags: list[str] = []
        companies: set[str] = set()
        industries: set[str] = set()
        match_count = 0
        trust_given = 0
        trust_received = 0

        for e in self.edges:
            if e.source == pid:
                if e.target.startswith("person:"):
                    connected_people.add(e.target)
                if e.relation == "works_at":
                    companies.add(e.target.replace("company:", ""))
                if e.relation == "tagged_as":
                    tags.append(e.target.replace("tag:", ""))
                if e.relation == "matched":
                    match_count += 1
                if e.relation == "trusted":
                    trust_given += 1
            if e.target == pid:
                if e.source.startswith("person:"):
                    connected_people.add(e.source)
                if e.relation == "trusted":
                    trust_received += 1
                if e.relation == "matched":
                    match_count += 1
            # same_industry / same_company
            if e.relation in ("same_industry", "same_company"):
                if e.source == pid:
                    connected_people.add(e.target)
                elif e.target == pid:
                    connected_people.add(e.source)

            if e.relation == "same_industry" and (e.source == pid or e.target == pid):
                via = e.attrs.get("via_tag", "")
                if via:
                    industries.add(via)

        degree = len(connected_people)
        centrality = round(degree / max(len(self.nodes) - 1, 1), 4) if len(self.nodes) > 1 else 0

        return {
            "user_id": user_id,
            "name": self.nodes[pid].attrs.get("name", ""),
            "company": self.nodes[pid].attrs.get("company", ""),
            "degree": degree,
            "centrality": centrality,
            "tags": list(set(tags)),
            "companies": list(companies),
            "industries": list(set(industries)),
            "match_count": match_count,
            "trust_given": trust_given,
            "trust_received": trust_received,
            "network_size": len(connected_people),
        }

    # ── 连接推荐 ──────────────────────────────────────────────────────────

    async def recommend_connections(
        self,
        user_id: int,
        limit: int = 10,
        min_score: float = 0.3,
    ) -> list[dict[str, Any]]:
        """基于知识图谱为当前用户推荐新连接"""
        await self.build()
        pid = f"person:{user_id}"
        if pid not in self.nodes:
            return []

        # 已有连接的用户（排除）
        existing: set[str] = {pid}
        for e in self.edges:
            if e.source == pid and e.target.startswith("person:"):
                existing.add(e.target)
            if e.target == pid and e.source.startswith("person:"):
                existing.add(e.source)

        # 为每个候选计算推荐分数
        candidates: dict[str, float] = defaultdict(float)
        reasons: dict[str, list[str]] = defaultdict(list)

        for nid, node in self.nodes.items():
            if nid in existing or node.type != "person":
                continue

            score = 0.0
            reasons_list = []

            # 1. 共同标签匹配
            my_tags = self._get_person_tags(pid)
            their_tags = self._get_person_tags(nid)
            common_tags = set(my_tags) & set(their_tags)
            if common_tags:
                tag_score = len(common_tags) * 0.3
                score += tag_score
                reasons_list.append(f"共同标签: {', '.join(list(common_tags)[:3])}")

            # 2. 同公司
            my_company = self._get_person_company(pid)
            their_company = self._get_person_company(nid)
            if my_company and my_company == their_company:
                score += 0.5
                reasons_list.append(f"同公司: {my_company}")

            # 3. 共同信任人（朋友的朋友）
            my_trusts = self._get_person_trusted(pid)
            their_trusts = self._get_person_trusted(nid)
            common_trusts = my_trusts & their_trusts
            if common_trusts:
                trust_score = len(common_trusts) * 0.4
                score += trust_score
                reasons_list.append(f"{len(common_trusts)} 位共同信任人")

            # 4. 同行（same_industry 边）
            for e in self.edges:
                if e.relation == "same_industry":
                    if (e.source == pid and e.target == nid) or (e.target == pid and e.source == nid):
                        score += 0.3
                        via = e.attrs.get("via_tag", "")
                        if via:
                            reasons_list.append(f"同行: {via}")
                        break

            if score >= min_score:
                candidates[nid] = round(min(score, 5.0), 2)
                reasons[nid] = reasons_list

        # 排序取 topN
        ranked = sorted(candidates.items(), key=lambda x: -x[1])
        results = []
        for nid, score in ranked[:limit]:
            node = self.nodes[nid]
            results.append({
                "user_id": node.attrs.get("user_id"),
                "name": node.attrs.get("name", ""),
                "company": node.attrs.get("company", ""),
                "title": node.attrs.get("title", ""),
                "avatar": node.attrs.get("avatar", ""),
                "score": score,
                "reasons": reasons.get(nid, []),
            })

        return results

    # ── 辅助方法 ──────────────────────────────────────────────────────────

    def _get_person_tags(self, pid: str) -> set[str]:
        tags = set()
        for e in self.edges:
            if e.source == pid and e.relation == "tagged_as":
                tags.add(e.target.replace("tag:", ""))
        return tags

    def _get_person_company(self, pid: str) -> str:
        for e in self.edges:
            if e.source == pid and e.relation == "works_at":
                return e.target.replace("company:", "")
        return ""

    def _get_person_trusted(self, pid: str) -> set[str]:
        trusted = set()
        for e in self.edges:
            if e.source == pid and e.relation == "trusted" and e.target.startswith("person:"):
                trusted.add(e.target)
            if e.target == pid and e.relation == "trusted" and e.source.startswith("person:"):
                trusted.add(e.source)
        return trusted

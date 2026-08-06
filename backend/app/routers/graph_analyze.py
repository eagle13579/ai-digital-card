"""Graph Analyze API — 知识图谱分析与查询端点。

GET    /api/graph/status       — 图谱基本统计（节点、边、社区、God节点）
GET    /api/graph/god-nodes    — Top-10 God节点（最高度中心性节点）
GET    /api/graph/query?q=xxx  — 图谱查询（模糊节点名搜索）
POST   /api/graph/rebuild      — 触发图谱重建（从 graph.json 重新加载）
"""
import json
import logging
import os
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

import networkx as nx

# ── 加载 baize_libs ───────────────────────────────────────────────
sys.path.insert(0, 'D:/baize_libs')
from graph_tools.graph_analyze import god_nodes as _god_nodes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/graph", tags=["知识图谱分析"])

# ── 全局惰性加载的图 ────────────────────────────────────────────────
_GRAPH_PATH = Path(os.path.dirname(os.path.abspath(__file__))) / ".." / ".." / "graphify-out" / "graph.json"
_graph: nx.Graph | None = None


# ── 请求/响应模型 ──────────────────────────────────────────────────


class GraphStatusResponse(BaseModel):
    nodes: int = 0
    edges: int = 0
    communities: int = 0
    god_nodes: list[dict] = []


class GodNodeItem(BaseModel):
    node_id: str
    label: str = ""
    degree: int = 0


class GodNodesResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: list[GodNodeItem] = []


class QueryResult(BaseModel):
    node_id: str
    label: str = ""
    degree: int = 0
    community: int | None = None


class QueryResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: list[QueryResult] = []


class RebuildResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: dict | None = None


# ── 辅助函数 ──────────────────────────────────────────────────────


def _resolve_graph_path() -> Path:
    """Resolve the absolute path to graph.json."""
    p = _GRAPH_PATH.resolve()
    if p.exists():
        return p
    # fallback: try explicit path
    fallback = Path("D:/AI数智名片/backend/graphify-out/graph.json")
    if fallback.exists():
        return fallback
    return p


def _ensure_loaded() -> nx.Graph:
    """Lazy-load the graph from graph.json. Returns the cached graph."""
    global _graph
    if _graph is not None:
        return _graph
    return _rebuild_graph()


def _rebuild_graph() -> nx.Graph:
    """Load graph.json and build a NetworkX graph."""
    global _graph
    graph_path = _resolve_graph_path()
    if not graph_path.exists():
        logger.warning("graph.json not found at %s", graph_path)
        _graph = nx.Graph()
        return _graph

    try:
        with open(graph_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        logger.exception("Failed to load graph.json: %s", exc)
        _graph = nx.Graph()
        return _graph

    # graph.json 是 NetworkX 标准的 node_link_data 格式
    # 包含: nodes, links, directed, multigraph, graph, hyperedges
    try:
        G: nx.Graph = nx.node_link_graph(data, directed=False, multigraph=False, edges='links')
    except Exception as exc:
        logger.exception("Failed to node_link_graph: %s", exc)
        G = nx.Graph()

    _graph = G
    logger.info("Graph loaded: %d nodes, %d edges", G.number_of_nodes(), G.number_of_edges())
    return G


def _get_top_god_nodes(G: nx.Graph, top_n: int = 10) -> list[dict]:
    """Return top-N god nodes as dicts with node_id, label, degree."""
    if G.number_of_nodes() == 0:
        return []
    top = _god_nodes(G, top_n=top_n)
    results = []
    for node_id, degree in top:
        label = G.nodes[node_id].get("label", "") if node_id in G else ""
        results.append({"node_id": str(node_id), "label": str(label), "degree": int(degree)})
    return results


def _community_count(G: nx.Graph) -> int:
    """Count unique communities from node attributes (pre-computed by graphify)."""
    communities: set = set()
    for _, attrs in G.nodes(data=True):
        c = attrs.get("community")
        if c is not None:
            communities.add(c)
    return len(communities) if communities else G.number_of_nodes()


def _get_community_map(G: nx.Graph) -> dict:
    """Build node -> community mapping from node attributes (pre-computed by graphify)."""
    mapping: dict = {}
    for node_id, attrs in G.nodes(data=True):
        c = attrs.get("community")
        if c is not None:
            mapping[node_id] = c
    # Fallback: if no community attributes, assign all to community 0
    if not mapping:
        for node_id in G.nodes():
            mapping[node_id] = 0
    return mapping


# ── API 端点 ──────────────────────────────────────────────────────


@router.get("/status", response_model=GraphStatusResponse, summary="图谱状态")
async def api_graph_status():
    """返回知识图谱的基本统计数据：节点数、边数、社区数、Top-10 God节点。"""
    G = _ensure_loaded()
    comm_count = _community_count(G)
    god_list = _get_top_god_nodes(G)

    return GraphStatusResponse(
        nodes=G.number_of_nodes(),
        edges=G.number_of_edges(),
        communities=comm_count,
        god_nodes=god_list,
    )


@router.get("/god-nodes", response_model=GodNodesResponse, summary="God节点")
async def api_graph_god_nodes():
    """返回知识图谱中 Top-10 最高度中心性节点（God节点）。"""
    G = _ensure_loaded()
    god_list = _get_top_god_nodes(G)
    items = [GodNodeItem(**g) for g in god_list]
    return GodNodesResponse(code=0, message="success", data=items)


@router.get("/query", response_model=QueryResponse, summary="查询图谱")
async def api_graph_query(
    q: str = Query(..., min_length=1, description="搜索关键词（节点名模糊匹配）"),
):
    """在知识图谱中模糊搜索节点名称/标签。

    返回匹配的节点 ID、标签、度数、所属社区。
    """
    G = _ensure_loaded()
    if G.number_of_nodes() == 0:
        return QueryResponse(code=1, message="图谱为空", data=[])

    q_lower = q.lower().strip()
    node_to_comm = _get_community_map(G)

    results: list[QueryResult] = []
    for node_id in G.nodes():
        label = str(G.nodes[node_id].get("label", node_id))
        if q_lower in label.lower() or q_lower in str(node_id).lower():
            degree = G.degree(node_id)
            results.append(QueryResult(
                node_id=str(node_id),
                label=label,
                degree=int(degree),
                community=node_to_comm.get(node_id),
            ))

    # Sort by degree descending
    results.sort(key=lambda r: r.degree, reverse=True)
    # Limit to top 50
    results = results[:50]

    return QueryResponse(code=0, message="success", data=results)


@router.post("/rebuild", response_model=RebuildResponse, summary="重建图谱")
async def api_graph_rebuild():
    """从 graph.json 重新加载并构建知识图谱。"""
    try:
        G = _rebuild_graph()
        comm_count = _community_count(G)
        god_list = _get_top_god_nodes(G)
        return RebuildResponse(
            code=0,
            message="图谱重建完成",
            data={
                "nodes": G.number_of_nodes(),
                "edges": G.number_of_edges(),
                "communities": comm_count,
                "god_nodes": god_list,
            },
        )
    except Exception as exc:
        logger.exception("Rebuild failed")
        raise HTTPException(status_code=500, detail=f"图谱重建失败: {exc}")

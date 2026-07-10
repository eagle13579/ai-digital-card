"""
AI Agent 活跃看板路由 — 提供 Agent 状态监控和调用统计
=======================================================

端点:
  GET /api/v1/admin/agents/status  → 所有 Agent 当前状态
  GET /api/v1/admin/agents/stats   → Agent 调用统计(累计调用次数/最后活跃时间)

数据来源:
  - AgentCallTracker: 内存计数器，追踪所有 Agent 调用
  - 其他模块通过 AgentCallTracker.record_call(agent_name) 上报调用
"""
import logging
import time
from collections import defaultdict
from datetime import datetime
from threading import Lock

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/agents", tags=["AI Agent 活跃看板"])


# ======================================================================
# 内存计数器 — 全局单例，线程安全
# ======================================================================

class AgentCallTracker:
    """Agent 调用追踪器（线程安全的内存计数器）。

    用法:
        # 在任意 Agent 调用处记录
        AgentCallTracker.record_call("rag_bot")
        AgentCallTracker.record_call("bandit_engine")

        # 获取统计
        stats = AgentCallTracker.get_stats()
        status = AgentCallTracker.get_status()
    """

    _lock = Lock()
    _call_counts: dict[str, int] = defaultdict(int)
    _last_active: dict[str, float] = {}  # agent_name -> timestamp

    _AGENT_DESCRIPTIONS: dict[str, str] = {
        "rag_bot": "RAG 知识库问答机器人",
        "bandit_engine": "上下文 Bandit 推荐引擎",
        "brochure_gen": "AI 画册生成 Agent",
        "chat_assist": "AI 对话助手",
        "deepseek_proxy": "DeepSeek 代理路由",
        "sag_pipeline": "SAG 三管道 Agent",
        "hybrid_pipeline": "Hybrid 混合管道 Agent",
        "social_match": "社交匹配 Agent",
        "crm_agent": "CRM 智能 Agent",
    }

    @classmethod
    def record_call(cls, agent_name: str) -> None:
        """记录一次 Agent 调用。"""
        with cls._lock:
            cls._call_counts[agent_name] += 1
            cls._last_active[agent_name] = time.time()

    @classmethod
    def get_status(cls) -> list[dict]:
        """获取所有 Agent 的当前状态。

        Returns:
            每个 Agent 包含:
              - name: Agent 标识名
              - description: Agent 中文描述
              - active: 是否有过调用记录
              - last_active_iso: 最后活跃时间 (ISO 格式，None 表示从未调用)
        """
        with cls._lock:
            now = time.time()
            results = []
            all_agents = set(cls._AGENT_DESCRIPTIONS.keys()) | set(cls._call_counts.keys())
            for name in sorted(all_agents):
                last_ts = cls._last_active.get(name)
                last_active_iso = (
                    datetime.fromtimestamp(last_ts).isoformat()
                    if last_ts is not None
                    else None
                )
                results.append({
                    "name": name,
                    "description": cls._AGENT_DESCRIPTIONS.get(name, "未知 Agent"),
                    "active": last_ts is not None,
                    "last_active_iso": last_active_iso,
                })
            return results

    @classmethod
    def get_stats(cls) -> dict:
        """获取 Agent 调用统计。

        Returns:
            agents: 每个 Agent 的调用次数和最后活跃时间
            total_calls: 所有 Agent 累计调用总数
            active_agent_count: 有调用记录的 Agent 数量
        """
        with cls._lock:
            agents_list = []
            total = 0
            for name in sorted(cls._call_counts.keys()):
                cnt = cls._call_counts[name]
                total += cnt
                last_ts = cls._last_active.get(name)
                last_active_iso = (
                    datetime.fromtimestamp(last_ts).isoformat()
                    if last_ts is not None
                    else None
                )
                agents_list.append({
                    "name": name,
                    "call_count": cnt,
                    "last_active_iso": last_active_iso,
                })
            return {
                "agents": agents_list,
                "total_calls": total,
                "active_agent_count": len(agents_list),
            }


# ======================================================================
# 端点
# ======================================================================


@router.get("/status")
async def agent_status():
    """所有 Agent 状态。

    返回每个 Agent 是否活跃及其最后活跃时间。
    """
    try:
        status_list = AgentCallTracker.get_status()
        return {
            "agents": status_list,
            "total_agent_count": len(status_list),
            "active_count": sum(1 for a in status_list if a["active"]),
        }
    except Exception as e:
        logger.error("获取 Agent 状态失败: %s", e)
        return {"error": "无法获取 Agent 状态", "agents": [], "total_agent_count": 0, "active_count": 0}


@router.get("/stats")
async def agent_stats():
    """Agent 调用统计 — 累计调用次数 / 最后活跃时间。"""
    try:
        return AgentCallTracker.get_stats()
    except Exception as e:
        logger.error("获取 Agent 统计失败: %s", e)
        return {"error": "无法获取 Agent 统计", "agents": [], "total_calls": 0, "active_agent_count": 0}

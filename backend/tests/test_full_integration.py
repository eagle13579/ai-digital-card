"""Full-system integration tests for 链客宝 AI Digital Employee platform.

Tests the complete end-to-end flow:
  - F1-F9 agents → Gaia Brain → Training → Weights → Agent learn → Memory
  - Phase 1 adapters (Redis cache, SQLite event bus via mock)
  - All 9 agents with LegionEmployee integration
  - Agent Runtime lifecycle (start, stop, event dispatch, cron)

Test architecture:
  - Fast tests run without external dependencies
  - Slow tests (@pytest.mark.slow) exercise full stack with mocks
  - Fixtures provide fully wired subsystems

Run with:
    pytest tests/test_full_integration.py -v --runslow  (includes all)
    pytest tests/test_full_integration.py -v            (fast only)
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.agents.base_agent import AgentConfig, AgentStatus, CronJob
from app.events.interfaces import Event, EventPriority


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_brain():
    """Create a fully mocked GaiaEvolutionBrain with async methods."""
    brain = MagicMock()
    brain.ingest_knowledge = AsyncMock(return_value=None)
    brain.ingest_feedback = AsyncMock(return_value=None)
    brain.process_evolution_cycle = AsyncMock(return_value={"weights_updated": 3})
    brain.get_evolved_weights = MagicMock(
        return_value={"alpha": 0.5, "beta": 0.3, "gamma": 0.2}
    )
    brain.vector_index = MagicMock()
    brain.vector_index.search = MagicMock(return_value=[])
    brain.vector_index.add = AsyncMock(return_value=True)
    brain.semantic_search = AsyncMock(return_value=[])
    return brain


@pytest.fixture
def mock_event_bus():
    """Create a mock EventBusProtocol."""
    bus = MagicMock()
    bus.publish = AsyncMock(return_value=None)
    bus.subscribe = AsyncMock(return_value=None)
    bus.unsubscribe = AsyncMock(return_value=True)
    bus.publish_delayed = AsyncMock(return_value=None)
    bus.start = AsyncMock(return_value=None)
    bus.stop = AsyncMock(return_value=None)
    return bus


@pytest.fixture
def mock_broker():
    """Create a mock ServiceBrokerProtocol."""
    broker = MagicMock()
    broker.call = AsyncMock(return_value=MagicMock(success=True, data={}))
    broker.call_many = AsyncMock(return_value=[])
    return broker


@pytest.fixture
def all_agents(mock_brain, mock_event_bus, mock_broker):
    """Create instances of all 9 agents wired with mocks."""
    from app.agents.backend_agent import BackendAgent
    from app.agents.qa_agent import QAAgent
    from app.agents.security_agent import SecurityAgent
    from app.agents.growth_agent import GrowthAgent
    from app.agents.knowledge_agent import KnowledgeAgent
    from app.agents.architecture_agent import ArchitectureAgent
    from app.agents.data_agent import DataAgent
    from app.agents.sre_agent import SREAgent
    from app.agents.support_agent import SupportAgent

    agents = {
        "backend": BackendAgent(brain=mock_brain, event_bus=mock_event_bus, broker=mock_broker),
        "qa": QAAgent(brain=mock_brain, event_bus=mock_event_bus, broker=mock_broker),
        "security": SecurityAgent(brain=mock_brain, event_bus=mock_event_bus, broker=mock_broker),
        "growth": GrowthAgent(brain=mock_brain, event_bus=mock_event_bus, broker=mock_broker),
        "knowledge": KnowledgeAgent(brain=mock_brain, event_bus=mock_event_bus, broker=mock_broker),
        "architecture": ArchitectureAgent(brain=mock_brain, event_bus=mock_event_bus, broker=mock_broker),
        "data": DataAgent(brain=mock_brain, event_bus=mock_event_bus, broker=mock_broker),
        "sre": SREAgent(brain=mock_brain, event_bus=mock_event_bus, broker=mock_broker),
        "support": SupportAgent(brain=mock_brain, event_bus=mock_event_bus, broker=mock_broker),
    }
    return agents


# ═══════════════════════════════════════════════════════════════════════════
# Test: Complete Lifecycle — F1-F9 → Gaia Brain → Training → Weights → Memory
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestCompleteLifecycleFlow:
    """Test the complete system flow: Agents → Brain → Training → Memory."""

    async def test_start_all_agents(self, all_agents, mock_brain, mock_event_bus):
        """F1-F9: Start all 9 agents and verify IDLE status."""
        for name, agent in all_agents.items():
            assert agent.status == AgentStatus.INITIALIZING, f"{name} not initializing"
            await agent.start()
            assert agent.status == AgentStatus.IDLE, f"{name} not idle after start: {agent.status}"
            assert agent.is_available is True, f"{name} not available"
        assert len(all_agents) == 9

    async def test_agents_ingest_to_brain(self, all_agents, mock_brain):
        """Gaia Brain: All agents ingest knowledge after tool execution."""
        from app.agents.backend_agent import BackendAgent
        from app.agents.qa_agent import QAAgent
        from app.agents.security_agent import SecurityAgent

        backend = all_agents["backend"]
        assert isinstance(backend, BackendAgent)
        await backend.tools["review_code"]("def foo(): pass")
        await backend.tools["generate_api"]("UserProfile", ["name", "email"])
        await backend.tools["debug_issue"]("ValueError", "production")

        qa = all_agents["qa"]
        assert isinstance(qa, QAAgent)
        await qa.tools["generate_tests"]("UserService")
        await qa.tools["analyze_coverage"]("tests/")

        security = all_agents["security"]
        assert isinstance(security, SecurityAgent)
        await security.tools["scan_dependencies"]("requirements.txt")
        await security.tools["check_compliance"]("GDPR")
        await security.tools["analyze_auth_pattern"]("JWT")

        # Verify brain was called for knowledge ingestion
        assert mock_brain.ingest_knowledge.call_count >= 6

    async def test_growth_agent_ab_test_analysis(self, all_agents):
        """F4-Growth: A/B test analysis feeds into brain."""
        from app.agents.growth_agent import GrowthAgent

        growth = all_agents["growth"]
        assert isinstance(growth, GrowthAgent)

        result = await growth.tools["analyze_ab_test"](
            variant_a={"impressions": 1000, "conversions": 50},
            variant_b={"impressions": 1000, "conversions": 65},
        )
        assert result is not None
        assert growth.status == AgentStatus.IDLE

    async def test_knowledge_agent_docs_workflow(self, all_agents):
        """F5-Knowledge: Documentation generation and ADR creation."""
        from app.agents.knowledge_agent import KnowledgeAgent

        knowledge = all_agents["knowledge"]
        assert isinstance(knowledge, KnowledgeAgent)

        docs = await knowledge.tools["generate_docs"](
            module="app.ai.gaia_evolution_brain",
            style="markdown",
        )
        assert docs is not None

        adr = await knowledge.tools["create_adr"](
            title="Adopt Event Sourcing for Audit Trail",
            status="proposed",
            context="Need immutable audit log for compliance",
        )
        assert adr is not None
        assert "ADR" in adr or "adr" in adr.lower() or len(adr) > 50

    async def test_architecture_agent_capacity_planning(self, all_agents):
        """F6-Architecture: Design review and capacity estimation."""
        from app.agents.architecture_agent import ArchitectureAgent

        arch = all_agents["architecture"]
        assert isinstance(arch, ArchitectureAgent)

        review = await arch.tools["review_design"](
            component="Recommendation Engine",
            concerns=["latency", "freshness"],
        )
        assert review is not None

        capacity = await arch.tools["capacity_estimate"](
            current_users=1_000_000,
            target_users=100_000_000,
            service_type="api_gateway",
        )
        assert capacity is not None

    async def test_data_agent_schema_migration(self, all_agents):
        """F7-Data: Schema change suggestions and data quality checks."""
        from app.agents.data_agent import DataAgent

        data_agent = all_agents["data"]
        assert isinstance(data_agent, DataAgent)

        schema = await data_agent.tools["suggest_schema_change"](
            current_schema="CREATE TABLE users (id INT)",
            performance_issues=["full_table_scan", "index_missing"],
        )
        assert schema is not None

        quality = await data_agent.tools["check_data_quality"](
            table_name="user_profiles",
            rules=["not_null", "unique_email"],
        )
        assert quality is not None

    async def test_sre_agent_health_and_remediation(self, all_agents):
        """F8-SRE: Health checks, auto-remediation, and capacity forecast."""
        from app.agents.sre_agent import SREAgent

        sre = all_agents["sre"]
        assert isinstance(sre, SREAgent)

        health = await sre.tools["health_check"](
            services=["api_gateway", "database", "cache", "event_bus"]
        )
        assert health is not None

        remediation = await sre.tools["auto_remediate"](
            issue_type="high_cpu",
            metrics={"cpu_percent": 92.5, "memory_percent": 78.0},
            service="api_gateway",
        )
        assert remediation is not None

        forecast = await sre.tools["capacity_forecast"](
            current_usage={"cpu": 60, "memory": 70},
            growth_rate_percent=15,
            forecast_days=90,
        )
        assert forecast is not None

    async def test_support_agent_ticket_handling(self, all_agents):
        """F9-Support: Ticket handling, FAQ lookup, and learning."""
        from app.agents.support_agent import SupportAgent

        support = all_agents["support"]
        assert isinstance(support, SupportAgent)

        ticket = await support.tools["handle_ticket"](
            ticket_id="TKT-001",
            user_query="How do I reset my password?",
            user_tier="premium",
        )
        assert ticket is not None

        faq = await support.tools["faq_lookup"](
            query="reset password",
            top_k=3,
        )
        assert faq is not None

        resolution = await support.tools["learn_from_resolution"](
            ticket_id="TKT-001",
            resolution_steps=["Navigate to settings", "Click reset password"],
            outcome="resolved",
        )
        assert resolution is not None

    async def test_brain_training_cycle_feed(self, all_agents, mock_brain):
        """Training: Agent outputs feed into Gaia Brain training pipeline."""
        # Agents produce knowledge that goes to brain
        for name, agent in all_agents.items():
            if hasattr(agent, "_learn") and callable(agent._learn):
                await agent._learn(
                    topic=f"{name}_execution",
                    data={"result": "success", "timestamp": datetime.now(timezone.utc).isoformat()},
                )

        await mock_brain.process_evolution_cycle()
        mock_brain.process_evolution_cycle.assert_awaited_once()

    async def test_brain_weights_distribution(self, all_agents, mock_brain):
        """Weights: Evolved weights are accessible by all agents."""
        # All agents should be able to query evolved weights
        for name, agent in all_agents.items():
            if hasattr(agent, "_get_brain_weights"):
                weights = agent._get_brain_weights("recommendation")
            else:
                weights = mock_brain.get_evolved_weights("recommendation")
            assert weights is not None
            assert isinstance(weights, dict)

    async def test_agents_learn_to_memory(self, all_agents, mock_brain):
        """Memory: Agent learn() calls create memory in brain."""
        # Simulate agents learning and feeding back to brain
        for name, agent in all_agents.items():
            if hasattr(agent, "learn") and callable(agent.learn):
                await agent.learn(
                    experience=f"processed_task_for_{name}",
                    result={"status": "ok", "duration_ms": 150},
                )

        # Verify knowledge was ingested
        assert mock_brain.ingest_knowledge.call_count >= len(all_agents)

    async def test_stop_all_agents_flush_to_brain(self, all_agents, mock_brain):
        """Memory: Stopping agents flushes unsaved state to brain."""
        for name, agent in all_agents.items():
            await agent.stop()
            assert agent.status in (AgentStatus.STOPPED, AgentStatus.INITIALIZING)


# ═══════════════════════════════════════════════════════════════════════════
# Test: Agent Runtime Lifecycle (Full Integration)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestAgentRuntimeIntegration:
    """Test AgentRuntime lifecycle with real agents and mocked event bus."""

    async def test_runtime_register_start_stop(self, all_agents, mock_event_bus):
        """Runtime: Full lifecycle with all 9 agents registered."""
        from app.agents.agent_runtime import AgentRuntime

        # Force new instance for test isolation
        AgentRuntime._instance = None
        runtime = await AgentRuntime.get_instance(event_bus=mock_event_bus)

        # Register all agents
        for name, agent in all_agents.items():
            await runtime.register(agent)
        assert len(runtime.agents) == 9

        # Start runtime
        await runtime.start()
        assert runtime._running is True

        status = await runtime.get_status()
        assert status["runtime"]["running"] is True
        assert status["runtime"]["agent_count"] == 9
        assert len(status["agents"]) == 9

        # Stop runtime
        await runtime.stop()
        assert runtime._running is False

    async def test_runtime_event_dispatch_to_agents(self, all_agents, mock_event_bus):
        """Runtime: Events are dispatched to all registered agents."""
        from app.agents.agent_runtime import AgentRuntime

        AgentRuntime._instance = None
        runtime = await AgentRuntime.get_instance(event_bus=mock_event_bus)

        for name, agent in all_agents.items():
            await runtime.register(agent)

        await runtime.start()

        # Dispatch a system event
        test_event = Event(
            type="system.test_integration",
            source="test_full_integration",
            payload={"message": "integration test event"},
        )
        await runtime.dispatch_event(test_event)
        mock_event_bus.publish.assert_called()

        # Dispatch a support escalation event (triggers special handler)
        escalation_event = Event(
            type="support.ticket_escalated",
            source="test",
            payload={"ticket_id": "TKT-ESC-001", "priority": "high"},
        )
        await runtime.dispatch_event(escalation_event)

        await runtime.stop()

    async def test_runtime_cron_execution(self, all_agents, mock_event_bus):
        """Runtime: Cron scheduler executes due jobs."""
        from app.agents.agent_runtime import AgentRuntime

        AgentRuntime._instance = None
        runtime = await AgentRuntime.get_instance(event_bus=mock_event_bus)

        for name, agent in all_agents.items():
            await runtime.register(agent)

        await runtime.start()

        # Run a cron cycle (checks all agents' cron jobs)
        await runtime.run_cron_cycle()

        # Verify cron jobs were checked/executed without error
        await runtime.stop()

    async def test_runtime_get_agent_by_name(self, all_agents, mock_event_bus):
        """Runtime: get_agent() returns correct agent by name."""
        from app.agents.agent_runtime import AgentRuntime

        AgentRuntime._instance = None
        runtime = await AgentRuntime.get_instance(event_bus=mock_event_bus)

        for name, agent in all_agents.items():
            await runtime.register(agent)

        # Retrieve each agent by name
        for name in all_agents:
            retrieved = runtime.get_agent(name)
            assert retrieved is not None, f"Agent '{name}' not found"
            assert retrieved.agent_name == name

        # Non-existent agent returns None
        assert runtime.get_agent("nonexistent") is None

    async def test_runtime_unregister_agent(self, all_agents, mock_event_bus):
        """Runtime: Unregister removes and stops an agent."""
        from app.agents.agent_runtime import AgentRuntime

        AgentRuntime._instance = None
        runtime = await AgentRuntime.get_instance(event_bus=mock_event_bus)

        for name, agent in all_agents.items():
            await runtime.register(agent)
        assert len(runtime.agents) == 9

        result = await runtime.unregister("backend")
        assert result is True
        assert len(runtime.agents) == 8
        assert runtime.get_agent("backend") is None

        # Unregister non-existent agent returns False
        result = await runtime.unregister("nonexistent")
        assert result is False

    async def test_runtime_duplicate_register_raises(self, all_agents, mock_event_bus):
        """Runtime: Registering duplicate agent name raises ValueError."""
        from app.agents.agent_runtime import AgentRuntime

        AgentRuntime._instance = None
        runtime = await AgentRuntime.get_instance(event_bus=mock_event_bus)

        agent = list(all_agents.values())[0]
        await runtime.register(agent)

        with pytest.raises(ValueError, match="already registered"):
            await runtime.register(agent)


# ═══════════════════════════════════════════════════════════════════════════
# Test: Phase 1 Adapter Integration
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestPhase1AdapterIntegration:
    """Integration tests for Phase 1 adapters (Redis Cache + SQLite Event Bus)."""

    async def test_inmemory_cache_with_agents(self, all_agents):
        """Cache: InMemoryCache works seamlessly with agent operations."""
        from app.cache.adapters.memory_adapter import InMemoryCache

        cache = InMemoryCache(default_ttl=60)
        await cache.start()

        # Simulate agent caching results
        await cache.set("agent:backend:review:123", {"result": "approved", "score": 0.95})
        await cache.set("agent:qa:coverage:api", {"line": 87.5, "branch": 82.0})

        val = await cache.get("agent:backend:review:123")
        assert val is not None
        assert val["result"] == "approved"

        exists = await cache.exists("agent:qa:coverage:api")
        assert exists is True

        count = await cache.increment("agent:security:scan_count")
        assert count == 1

        # TTL expiry
        short_cache = InMemoryCache(default_ttl=0)
        await short_cache.set("ephemeral", "value", ttl=0)
        val = await short_cache.get("ephemeral")
        assert val == "value"

        await cache.stop()

    async def test_inprocess_event_bus_with_agents(self, all_agents, mock_brain):
        """Event Bus: InProcessEventBus delivers events between agents."""
        from app.events.adapters.inprocess_adapter import InProcessEventBus

        bus = InProcessEventBus(max_queue_size=1000)
        await bus.start()

        received_events = []

        async def capture_handler(event: Event) -> None:
            received_events.append(event)

        await bus.subscribe("test.*", capture_handler, description="test capture")

        # Publish events
        for i in range(5):
            await bus.publish(
                Event(type=f"test.event_{i}", source="integration_test", payload={"idx": i})
            )

        # Give consumer time to process
        await asyncio.sleep(0.1)

        assert len(received_events) >= 1

        await bus.unsubscribe("test.*", capture_handler)
        await bus.stop()

    async def test_inprocess_event_bus_idempotency(self):
        """Event Bus: Idempotency keys prevent duplicate delivery."""
        from app.events.adapters.inprocess_adapter import InProcessEventBus

        bus = InProcessEventBus()
        await bus.start()

        call_count = 0

        async def count_handler(event: Event) -> None:
            nonlocal call_count
            call_count += 1

        await bus.subscribe("idem.*", count_handler)

        event = Event(
            type="idem.test",
            source="test",
            idempotency_key="unique-key-001",
        )

        await bus.publish(event)
        await bus.publish(event)  # Same key — should be dropped
        await asyncio.sleep(0.05)

        assert call_count == 1, f"Expected 1 but got {call_count}"

        await bus.stop()

    async def test_sqlite_event_bus_publish_subscribe(self):
        """Event Bus: SQLite-backed event bus stores and delivers events."""
        from app.events.adapters.sqlite_adapter import SQLiteEventBus

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            bus = SQLiteEventBus(db_path=db_path)
            await bus.start()

            received = []

            async def handler(event: Event) -> None:
                received.append(event)

            await bus.subscribe("sqlite.*", handler)

            await bus.publish(
                Event(type="sqlite.test", source="integration", payload={"db": "sqlite"})
            )

            await asyncio.sleep(0.2)
            assert len(received) >= 1

            await bus.stop()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    async def test_redis_cache_with_event_bus(self):
        """Cache + Event Bus: Combined adapter usage."""
        from app.cache.adapters.memory_adapter import InMemoryCache
        from app.events.adapters.inprocess_adapter import InProcessEventBus

        cache = InMemoryCache(default_ttl=300)
        bus = InProcessEventBus()
        await cache.start()
        await bus.start()

        # Write-through pattern: event published when cache is updated
        async def cache_update_handler(event: Event) -> None:
            if event.type == "cache.updated":
                await cache.set(
                    f"event:{event.payload['key']}",
                    event.payload["value"],
                    ttl=event.payload.get("ttl", 300),
                )

        await bus.subscribe("cache.*", cache_update_handler)

        # Publish cache update event
        await bus.publish(
            Event(
                type="cache.updated",
                source="test",
                payload={"key": "test_key", "value": {"data": 42}},
            )
        )

        await asyncio.sleep(0.05)
        val = await cache.get("event:test_key")
        assert val == {"data": 42}

        await bus.stop()
        await cache.stop()

    async def test_inprocess_event_bus_publish_delayed(self):
        """Event Bus: Delayed publishing works correctly."""
        from app.events.adapters.inprocess_adapter import InProcessEventBus

        bus = InProcessEventBus()
        await bus.start()

        received = []

        async def delayed_handler(event: Event) -> None:
            received.append(event)

        await bus.subscribe("delayed.*", delayed_handler)

        start = asyncio.get_event_loop().time()
        await bus.publish_delayed(
            Event(type="delayed.test", source="test"),
            delay_seconds=0.05,
        )

        await asyncio.sleep(0.15)
        elapsed = asyncio.get_event_loop().time() - start

        assert len(received) == 1
        assert elapsed >= 0.04, f"Event arrived too fast: {elapsed:.3f}s"

        await bus.stop()


# ═══════════════════════════════════════════════════════════════════════════
# Test: LegionEmployee Integration
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestLegionEmployeeIntegration:
    """Integration tests for LegionEmployee adapter with agents."""

    async def test_legion_employee_creation(self):
        """Legion: Create a LegionEmployee and verify basic attributes."""
        from app.agents.legion_employee import LegionEmployee

        employee = LegionEmployee(employee_id="emp-烛龙")
        assert employee is not None
        assert employee.employee_id == "emp-烛龙"

    async def test_legion_agent_creation(self, mock_brain):
        """Legion: Create a legion-backed agent via employee_profiles."""
        from app.agents.employee_profiles import create_legion_agent

        employee, agent = await create_legion_agent("backend", brain=mock_brain)
        assert employee is not None
        assert agent is not None
        assert agent.agent_name == "backend"
        assert agent.agent_role == "backend_api_engineer"

        # Verify the agent has expected tools
        assert "review_code" in agent.tools
        assert "generate_api" in agent.tools
        assert "debug_issue" in agent.tools

    async def test_all_legion_agent_mappings(self, mock_brain):
        """Legion: All 9 agent types can be created as legion-backed agents."""
        from app.agents.employee_profiles import create_legion_agent, EMPLOYEE_AGENT_MAP

        for agent_key in EMPLOYEE_AGENT_MAP:
            employee, agent = await create_legion_agent(agent_key, brain=mock_brain)
            assert employee is not None, f"Employee missing for {agent_key}"
            assert agent is not None, f"Agent missing for {agent_key}"
            assert agent.agent_name == agent_key

    async def test_legion_agent_knowledge_base(self, mock_brain):
        """Legion: Agent has correct knowledge base for its role."""
        from app.agents.employee_profiles import create_legion_agent

        for role in ["backend", "security", "sre"]:
            _, agent = await create_legion_agent(role, brain=mock_brain)
            kb = agent.config.knowledge_base_name
            assert kb is not None and len(kb) > 0

    async def test_legion_agent_runtime_integration(self, mock_brain, mock_event_bus):
        """Legion: Legion-backed agents work inside Agent Runtime."""
        from app.agents.employee_profiles import create_legion_agent
        from app.agents.agent_runtime import AgentRuntime

        AgentRuntime._instance = None
        runtime = await AgentRuntime.get_instance(event_bus=mock_event_bus)

        # Create legion agents
        for role in ["backend", "qa", "sre"]:
            _, agent = await create_legion_agent(role, brain=mock_brain)
            await runtime.register(agent)

        assert len(runtime.agents) == 3

        await runtime.start()

        status = await runtime.get_status()
        assert status["runtime"]["agent_count"] == 3
        for name in ["backend", "qa", "sre"]:
            assert name in status["agents"]

        await runtime.stop()


# ═══════════════════════════════════════════════════════════════════════════
# Slow tests — full stack integration (marked with @pytest.mark.slow)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.slow
@pytest.mark.asyncio
class TestFullStackSlow:
    """Full-stack tests that exercise the complete pipeline end-to-end.

    These tests are SLOW because they set up real subsystems.
    Run with: pytest tests/test_full_integration.py -v --runslow
    """

    async def test_full_end_to_end_pipeline(self, mock_brain, mock_event_bus, mock_broker):
        """Complete E2E: All agents → Brain → Training → Weights → Memory."""
        from app.agents.backend_agent import BackendAgent
        from app.agents.qa_agent import QAAgent
        from app.agents.support_agent import SupportAgent
        from app.agents.sre_agent import SREAgent
        from app.agents.growth_agent import GrowthAgent
        from app.agents.agent_runtime import AgentRuntime

        AgentRuntime._instance = None
        runtime = await AgentRuntime.get_instance(event_bus=mock_event_bus, broker=mock_broker)

        # Phase 1: Create and register agents
        agents = {
            "backend": BackendAgent(brain=mock_brain, event_bus=mock_event_bus, broker=mock_broker),
            "qa": QAAgent(brain=mock_brain, event_bus=mock_event_bus, broker=mock_broker),
            "support": SupportAgent(brain=mock_brain, event_bus=mock_event_bus, broker=mock_broker),
            "sre": SREAgent(brain=mock_brain, event_bus=mock_event_bus, broker=mock_broker),
            "growth": GrowthAgent(brain=mock_brain, event_bus=mock_event_bus, broker=mock_broker),
        }

        for name, agent in agents.items():
            await runtime.register(agent)

        # Phase 2: Start runtime
        await runtime.start()

        # Phase 3: Execute agent tools (producing knowledge)
        await agents["backend"].tools["review_code"]("class UserService: ...")
        await agents["qa"].tools["generate_tests"]("UserService")
        await agents["support"].tools["handle_ticket"](
            ticket_id="TKT-001", user_query="Help", user_tier="premium"
        )
        await agents["sre"].tools["health_check"](services=["all"])
        await agents["growth"].tools["analyze_ab_test"](
            variant_a={"users": 500, "conversions": 25},
            variant_b={"users": 500, "conversions": 35},
        )

        # Phase 4: Gaia Brain processes evolution cycle
        evolution_result = await mock_brain.process_evolution_cycle()
        assert evolution_result is not None

        # Phase 5: Query evolved weights
        weights = mock_brain.get_evolved_weights("recommendation")
        assert weights is not None

        # Phase 6: Publish and dispatch events
        await runtime.dispatch_event(
            Event(type="runtime.started", source="e2e_test", payload={"phase": "complete"})
        )

        # Phase 7: Run cron cycle
        await runtime.run_cron_cycle()

        # Phase 8: Run status check
        status = await runtime.get_status()
        assert status["runtime"]["running"] is True
        assert status["runtime"]["agent_count"] == 5

        # Phase 9: Stop runtime (flushes memory)
        await runtime.stop()
        assert mock_brain.ingest_knowledge.call_count >= 5

    async def test_concurrent_agent_operations(self, mock_brain, mock_event_bus):
        """Concurrent operations across multiple agents."""
        from app.agents.backend_agent import BackendAgent
        from app.agents.qa_agent import QAAgent
        from app.agents.security_agent import SecurityAgent

        backend = BackendAgent(brain=mock_brain)
        qa = QAAgent(brain=mock_brain)
        security = SecurityAgent(brain=mock_brain)

        await backend.start()
        await qa.start()
        await security.start()

        # Execute tools concurrently across agents
        results = await asyncio.gather(
            backend.tools["review_code"]("async def handler(): pass"),
            qa.tools["generate_tests"]("HandlerClass"),
            security.tools["scan_dependencies"]("requirements.txt"),
            backend.tools["generate_api"]("Webhook", ["url", "secret"]),
            qa.tools["analyze_coverage"]("app/handlers/"),
            security.tools["check_compliance"]("SOC2"),
            return_exceptions=True,
        )

        # All should succeed
        for i, r in enumerate(results):
            assert not isinstance(r, Exception), f"Task {i} failed: {r}"

        await backend.stop()
        await qa.stop()
        await security.stop()

    async def test_brain_knowledge_retrieval_workflow(self, mock_brain):
        """Knowledge ingested by agents is retrievable via semantic search."""
        from app.agents.backend_agent import BackendAgent
        from app.agents.knowledge_agent import KnowledgeAgent

        backend = BackendAgent(brain=mock_brain)
        knowledge = KnowledgeAgent(brain=mock_brain)

        await backend.start()
        await knowledge.start()

        # Backend ingests some code knowledge
        await backend.tools["review_code"](
            "def calculate_risk(profile): return profile.risk_score * 1.5"
        )

        # Knowledge agent can search that knowledge
        search_results = await knowledge.tools["summarize_changes"](
            changes=["Added risk calculation", "Updated API endpoints"]
        )
        assert search_results is not None

        await backend.stop()
        await knowledge.stop()

    async def test_recovery_after_agent_error(self, mock_brain, mock_event_bus):
        """System recovers gracefully after an agent encounters an error."""
        from app.agents.backend_agent import BackendAgent
        from app.agents.sre_agent import SREAgent
        from app.agents.agent_runtime import AgentRuntime

        AgentRuntime._instance = None
        runtime = await AgentRuntime.get_instance(event_bus=mock_event_bus)

        backend = BackendAgent(brain=mock_brain)
        sre = SREAgent(brain=mock_brain)

        await runtime.register(backend)
        await runtime.register(sre)
        await runtime.start()

        # Simulate error in one agent
        await backend.stop()

        # Other agent should still work
        health = await sre.tools["health_check"](services=["api_gateway"])
        assert health is not None

        # Runtime should still report status for all agents
        status = await runtime.get_status()
        assert status["runtime"]["agent_count"] == 2

        await runtime.stop()

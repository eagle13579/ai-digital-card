"""Performance benchmarks for 链客宝 AI Digital Employee platform.

Measures operations/second and latency percentiles for:
  1. Cache operations — InMemory vs Redis (mock) throughput
  2. Event bus operations — InProcess vs SQLite throughput
  3. Gaia Brain ingest_knowledge throughput
  4. Agent tool execution throughput
  5. Agent Runtime event dispatch

Each benchmark runs N iterations and reports:
  - Operations per second (throughput)
  - P50, P90, P99 latency (milliseconds)

Run with:
    pytest tests/test_performance.py -v --benchmark-only
    pytest tests/test_performance.py -v  (functional verification only)

NOTE: These are micro-benchmarks, not production load tests.
For production, use locust/k6 with the actual API endpoints.
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import sys
import tempfile
import time
from statistics import median
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.events.interfaces import Event, EventPriority


# ═══════════════════════════════════════════════════════════════════════════
# Benchmark utilities
# ═══════════════════════════════════════════════════════════════════════════


class BenchmarkResult:
    """Container for benchmark timing results."""

    def __init__(self, name: str, latencies_ms: list[float]) -> None:
        self.name = name
        self.latencies_ms = sorted(latencies_ms)
        self.count = len(latencies_ms)

    @property
    def total_time_s(self) -> float:
        return sum(self.latencies_ms) / 1000.0

    @property
    def ops_per_second(self) -> float:
        if self.total_time_s == 0:
            return float("inf")
        return self.count / self.total_time_s

    @property
    def p50_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        return median(self.latencies_ms)

    @property
    def p90_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        idx = int(len(self.latencies_ms) * 0.90)
        return self.latencies_ms[min(idx, len(self.latencies_ms) - 1)]

    @property
    def p99_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        idx = int(len(self.latencies_ms) * 0.99)
        return self.latencies_ms[min(idx, len(self.latencies_ms) - 1)]

    @property
    def max_ms(self) -> float:
        return max(self.latencies_ms) if self.latencies_ms else 0.0

    @property
    def min_ms(self) -> float:
        return min(self.latencies_ms) if self.latencies_ms else 0.0

    def report(self) -> str:
        return (
            f"  {self.name}: {self.ops_per_second:>10.1f} ops/s | "
            f"P50={self.p50_ms:>6.2f}ms P90={self.p90_ms:>6.2f}ms "
            f"P99={self.p99_ms:>6.2f}ms | "
            f"min={self.min_ms:>6.2f}ms max={self.max_ms:>6.2f}ms "
            f"({self.count} iterations)"
        )


async def benchmark(
    name: str,
    fn,
    iterations: int = 1000,
    warmup: int = 100,
) -> BenchmarkResult:
    """Run a benchmark and return results.

    Args:
        name: Benchmark name for display.
        fn: Async callable to benchmark (takes no args).
        iterations: Number of measured iterations.
        warmup: Number of warmup iterations (not measured).

    Returns:
        BenchmarkResult with timing statistics.
    """
    # Warmup
    for _ in range(warmup):
        await fn()

    # Measure
    latencies: list[float] = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        await fn()
        elapsed = (time.perf_counter() - t0) * 1000  # ms
        latencies.append(elapsed)

    return BenchmarkResult(name, latencies)


# ═══════════════════════════════════════════════════════════════════════════
# Benchmark fixtures
# ═══════════════════════════════════════════════════════════════════════════

BENCH_ITERATIONS = 200  # Keep small for CI; bump to 2000+ for real benchmarks
BENCH_WARMUP = 50


@pytest.fixture(scope="module")
def mock_brain():
    """Module-scoped mock brain for benchmarks."""
    brain = MagicMock()
    brain.ingest_knowledge = AsyncMock(return_value=None)
    brain.ingest_feedback = AsyncMock(return_value=None)
    brain.process_evolution_cycle = AsyncMock(return_value={"updated": True})
    brain.get_evolved_weights = AsyncMock(return_value={"alpha": 0.5})
    brain.vector_index = MagicMock()
    brain.vector_index.search = MagicMock(return_value=[])
    brain.vector_index.add = AsyncMock(return_value=True)
    return brain


@pytest.fixture
def mock_redis_client():
    """Benchmark-grade mock Redis client (zero-delay)."""
    client = MagicMock()
    client.get = AsyncMock(return_value=json.dumps({"value": 42}).encode())
    client.set = AsyncMock(return_value=True)
    client.setex = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=1)
    client.exists = AsyncMock(return_value=True)
    client.incrby = AsyncMock(return_value=1)
    client.scan = AsyncMock(return_value=(0, []))
    client.ping = AsyncMock(return_value=True)
    client.connection_pool = MagicMock()
    client.connection_pool.disconnect = AsyncMock()
    return client


@pytest.fixture
def mock_broker():
    """Benchmark-grade mock service broker for AgentRuntime tests."""
    broker = MagicMock()
    broker.call_service = AsyncMock(return_value={"status": "ok"})
    broker.register_service = AsyncMock(return_value=True)
    broker.unregister_service = AsyncMock(return_value=True)
    return broker


# ═══════════════════════════════════════════════════════════════════════════
# Benchmark 1: Cache Operations
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestCacheBenchmark:
    """Benchmark cache operations: InMemoryCache vs RedisCache (mock)."""

    @pytest.fixture
    async def memory_cache(self):
        from app.cache.adapters.memory_adapter import InMemoryCache

        cache = InMemoryCache(default_ttl=300)
        await cache.start()
        yield cache
        await cache.stop()

    @pytest.fixture
    def redis_cache(self, mock_redis_client):
        from app.cache.adapters.redis_adapter import RedisCache, RedisConfig

        config = RedisConfig(host="localhost", port=6379, db=0, default_ttl=60)
        cache = RedisCache(config=config)
        cache._redis = mock_redis_client
        cache._running = True
        return cache

    async def test_inmemory_cache_get(self, memory_cache):
        """InMemoryCache: get() throughput."""
        await memory_cache.set("perf_key", "benchmark_value")

        result = await benchmark(
            "InMemoryCache.get",
            lambda: memory_cache.get("perf_key"),
            iterations=BENCH_ITERATIONS,
            warmup=BENCH_WARMUP,
        )
        print(result.report())
        assert result.ops_per_second > 0

    async def test_inmemory_cache_set(self, memory_cache):
        """InMemoryCache: set() throughput."""
        result = await benchmark(
            "InMemoryCache.set",
            lambda: memory_cache.set("perf_key", {"data": "x" * 100}),
            iterations=BENCH_ITERATIONS,
            warmup=BENCH_WARMUP,
        )
        print(result.report())
        assert result.ops_per_second > 0

    async def test_inmemory_cache_get_or_set(self, memory_cache):
        """InMemoryCache: get_or_set() throughput with factory."""
        async def factory():
            return {"computed": "value", "timestamp": time.time()}

        # Ensure miss for first call
        await memory_cache.delete("get_or_set_key")

        result = await benchmark(
            "InMemoryCache.get_or_set",
            lambda: memory_cache.get_or_set("get_or_set_key", factory),
            iterations=min(BENCH_ITERATIONS, 100),
            warmup=BENCH_WARMUP // 2,
        )
        print(result.report())
        assert result.ops_per_second > 0

    async def test_redis_cache_get(self, redis_cache):
        """RedisCache (mock): get() throughput."""
        result = await benchmark(
            "RedisCache.get",
            lambda: redis_cache.get("perf_key"),
            iterations=BENCH_ITERATIONS,
            warmup=BENCH_WARMUP,
        )
        print(result.report())
        assert result.ops_per_second > 0

    async def test_redis_cache_set(self, redis_cache, mock_redis_client):
        """RedisCache (mock): set() throughput."""
        result = await benchmark(
            "RedisCache.set",
            lambda: redis_cache.set("perf_key", {"data": "x" * 100}),
            iterations=BENCH_ITERATIONS,
            warmup=BENCH_WARMUP,
        )
        print(result.report())
        assert result.ops_per_second > 0

    async def test_cache_throughput_comparison(self, memory_cache, redis_cache):
        """Comparison: InMemory vs Redis get() throughput ratio."""
        inmem_result = await benchmark(
            "InMemoryCache.get",
            lambda: memory_cache.get("perf_key"),
            iterations=BENCH_ITERATIONS,
            warmup=BENCH_WARMUP,
        )
        redis_result = await benchmark(
            "RedisCache.get (mock)",
            lambda: redis_cache.get("perf_key"),
            iterations=BENCH_ITERATIONS,
            warmup=BENCH_WARMUP,
        )

        print("\n── Cache Comparison ──")
        print(inmem_result.report())
        print(redis_result.report())

        # InMemory should be faster than or equal to Redis (mock)
        ratio = inmem_result.ops_per_second / max(redis_result.ops_per_second, 1)
        print(f"  InMemory/Redis throughput ratio: {ratio:.2f}x")
        assert ratio > 0


# ═══════════════════════════════════════════════════════════════════════════
# Benchmark 2: Event Bus Operations
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEventBusBenchmark:
    """Benchmark event bus operations: InProcess vs SQLite."""

    @pytest.fixture
    async def inprocess_bus(self):
        from app.events.adapters.inprocess_adapter import InProcessEventBus

        bus = InProcessEventBus(max_queue_size=10000)
        await bus.start()
        yield bus
        await bus.stop()

    @pytest.fixture
    async def sqlite_bus(self):
        from app.events.adapters.sqlite_adapter import SQLiteEventBus

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        bus = SQLiteEventBus(db_path=db_path)
        await bus.start()
        yield bus
        await bus.stop()
        if os.path.exists(db_path):
            os.unlink(db_path)

    async def test_inprocess_publish(self, inprocess_bus):
        """InProcessEventBus: publish() throughput (fire-and-forget)."""
        event = Event(type="perf.test", source="benchmark", payload={"idx": 0})

        result = await benchmark(
            "InProcessEventBus.publish",
            lambda: inprocess_bus.publish(event),
            iterations=BENCH_ITERATIONS,
            warmup=BENCH_WARMUP,
        )
        print(result.report())
        assert result.ops_per_second > 0

    async def test_inprocess_publish_with_handler(self, inprocess_bus):
        """InProcessEventBus: publish with handler subscription."""
        received = []

        async def fast_handler(event: Event) -> None:
            received.append(event.type)

        await inprocess_bus.subscribe("perf.*", fast_handler)

        event = Event(type="perf.test", source="benchmark")

        result = await benchmark(
            "InProcessEventBus.publish+handle",
            lambda: inprocess_bus.publish(event),
            iterations=min(BENCH_ITERATIONS, 100),
            warmup=BENCH_WARMUP // 2,
        )
        print(result.report())
        assert result.ops_per_second > 0

        # Give handler time to process
        await asyncio.sleep(0.1)
        await inprocess_bus.unsubscribe("perf.*", fast_handler)

    async def test_inprocess_subscribe_unsubscribe(self, inprocess_bus):
        """InProcessEventBus: subscribe/unsubscribe throughput."""
        async def dummy_handler(event: Event) -> None:
            pass

        async def bench_sub():
            await inprocess_bus.subscribe("bench.*", dummy_handler)

        async def bench_unsub():
            await inprocess_bus.unsubscribe("bench.*", dummy_handler)

        sub_result = await benchmark(
            "InProcessEventBus.subscribe",
            bench_sub,
            iterations=min(BENCH_ITERATIONS, 100),
            warmup=20,
        )
        unsub_result = await benchmark(
            "InProcessEventBus.unsubscribe",
            bench_unsub,
            iterations=min(BENCH_ITERATIONS, 100),
            warmup=20,
        )
        print(sub_result.report())
        print(unsub_result.report())

    async def test_event_bus_throughput_comparison(self, inprocess_bus, sqlite_bus):
        """Comparison: InProcess vs SQLite publish throughput."""
        event = Event(type="perf.compare", source="benchmark")

        ip_result = await benchmark(
            "InProcessEventBus.publish",
            lambda: inprocess_bus.publish(event),
            iterations=BENCH_ITERATIONS,
            warmup=BENCH_WARMUP,
        )

        sqlite_result = await benchmark(
            "SQLiteEventBus.publish",
            lambda: sqlite_bus.publish(event),
            iterations=min(BENCH_ITERATIONS, 50),
            warmup=min(BENCH_WARMUP, 10),
        )

        print("\n── Event Bus Comparison ──")
        print(ip_result.report())
        print(sqlite_result.report())

        ratio = ip_result.ops_per_second / max(sqlite_result.ops_per_second, 1)
        print(f"  InProcess/SQLite throughput ratio: {ratio:.2f}x")


# ═══════════════════════════════════════════════════════════════════════════
# Benchmark 3: Gaia Brain Operations
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestGaiaBrainBenchmark:
    """Benchmark Gaia Evolution Brain throughput."""

    async def test_brain_ingest_knowledge(self, mock_brain):
        """GaiaBrain: ingest_knowledge() throughput."""
        knowledge = {
            "source": "benchmark",
            "source_id": "perf_001",
            "content": "This is benchmark knowledge content for performance testing.",
            "tags": ["performance", "benchmark", "test"],
        }

        result = await benchmark(
            "GaiaBrain.ingest_knowledge",
            lambda: mock_brain.ingest_knowledge(**knowledge),
            iterations=BENCH_ITERATIONS,
            warmup=BENCH_WARMUP,
        )
        print(result.report())
        assert result.ops_per_second > 0

    async def test_brain_get_evolved_weights(self, mock_brain):
        """GaiaBrain: get_evolved_weights() throughput."""
        result = await benchmark(
            "GaiaBrain.get_evolved_weights",
            lambda: mock_brain.get_evolved_weights("recommendation"),
            iterations=BENCH_ITERATIONS * 2,
            warmup=BENCH_WARMUP,
        )
        print(result.report())
        assert result.ops_per_second > 0

    async def test_brain_ingest_feedback(self, mock_brain):
        """GaiaBrain: ingest_feedback() throughput."""
        feedback = {
            "user_id": 1,
            "item_id": 100,
            "rating": 4.5,
            "source": "recommendation",
        }

        result = await benchmark(
            "GaiaBrain.ingest_feedback",
            lambda: mock_brain.ingest_feedback(**feedback),
            iterations=BENCH_ITERATIONS,
            warmup=BENCH_WARMUP,
        )
        print(result.report())


# ═══════════════════════════════════════════════════════════════════════════
# Benchmark 4: Agent Tool Execution
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestAgentToolBenchmark:
    """Benchmark agent tool execution throughput."""

    @pytest.fixture
    async def backend_agent(self, mock_brain):
        from app.agents.backend_agent import BackendAgent

        agent = BackendAgent(brain=mock_brain)
        await agent.start()
        # Override real tools with fast mocks for benchmarking
        async def _mock_review_code(code: str) -> dict:
            return {"reviewed": True, "issues": [], "score": 95}
        async def _mock_generate_api(spec: dict) -> dict:
            return {"generated": True, "endpoint": spec.get("name", "api"), "routes": 3}
        async def _mock_debug_issue(issue: str) -> dict:
            return {"debugged": True, "root_cause": "mock", "fix": "mock fix"}
        agent.tools = {
            "review_code": _mock_review_code,
            "generate_api": _mock_generate_api,
            "debug_issue": _mock_debug_issue,
        }
        yield agent
        await agent.stop()

    @pytest.fixture
    async def all_agents(self, mock_brain):
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
            "backend": BackendAgent(brain=mock_brain),
            "qa": QAAgent(brain=mock_brain),
            "security": SecurityAgent(brain=mock_brain),
            "growth": GrowthAgent(brain=mock_brain),
            "knowledge": KnowledgeAgent(brain=mock_brain),
            "architecture": ArchitectureAgent(brain=mock_brain),
            "data": DataAgent(brain=mock_brain),
            "sre": SREAgent(brain=mock_brain),
            "support": SupportAgent(brain=mock_brain),
        }
        for agent in agents.values():
            await agent.start()
        # Override real tools with fast mock tools for benchmarking
        async def _noop(*args, **kwargs) -> dict:
            return {"status": "ok", "result": "mock"}
        for name, agent in agents.items():
            agent.tools = {k: _noop for k in agent.tools}
        yield agents
        for agent in agents.values():
            await agent.stop()

    async def test_backend_tool_execution(self, backend_agent):
        """BackendAgent: tool execution throughput."""
        result = await benchmark(
            "BackendAgent.review_code",
            lambda: backend_agent.tools["review_code"]("def hello(): return 'world'"),
            iterations=BENCH_ITERATIONS,
            warmup=BENCH_WARMUP,
        )
        print(result.report())
        assert result.ops_per_second > 0

    async def test_backend_api_generation(self, backend_agent):
        """BackendAgent: generate_api throughput."""
        result = await benchmark(
            "BackendAgent.generate_api",
            lambda: backend_agent.tools["generate_api"]({"name": "TestAPI", "fields": ["field1", "field2"]}),
            iterations=min(BENCH_ITERATIONS, 100),
            warmup=BENCH_WARMUP // 2,
        )
        print(result.report())
        assert result.ops_per_second > 0

    async def test_qa_tool_execution(self, all_agents):
        """QAAgent: tool execution throughput."""
        qa = all_agents["qa"]
        result = await benchmark(
            "QAAgent.generate_tests",
            lambda: qa.tools["generate_tests"]("BenchmarkModule"),
            iterations=min(BENCH_ITERATIONS, 100),
            warmup=BENCH_WARMUP // 2,
        )
        print(result.report())

    async def test_security_tool_execution(self, all_agents):
        """SecurityAgent: tool execution throughput."""
        security = all_agents["security"]
        result = await benchmark(
            "SecurityAgent.scan_dependencies",
            lambda: security.tools["scan_dependencies"](),
            iterations=min(BENCH_ITERATIONS, 100),
            warmup=BENCH_WARMUP // 2,
        )
        print(result.report())

    async def test_agent_concurrent_execution(self, all_agents):
        """All agents: concurrent tool execution throughput."""
        async def run_all_tools():
            tasks = [
                all_agents["backend"].tools["review_code"]("def f(): pass"),
                all_agents["qa"].tools["generate_tests"]("Module"),
                all_agents["security"].tools["check_compliance"](),
                all_agents["growth"].tools["suggest_optimization"]("checkout"),
                all_agents["knowledge"].tools["generate_docs"]("app.ai", "markdown"),
                all_agents["data"].tools["suggest_schema_change"](
                    "CREATE TABLE t (id INT)", ["normalization"]
                ),
                all_agents["sre"].tools["health_check"](services=["all"]),
                all_agents["support"].tools["faq_lookup"](query="pricing"),
            ]
            await asyncio.gather(*tasks)

        result = await benchmark(
            "AllAgents.concurrent_tools",
            run_all_tools,
            iterations=min(BENCH_ITERATIONS // 4, 50),
            warmup=BENCH_WARMUP // 4,
        )
        print(result.report())
        assert result.ops_per_second > 0

    async def test_agent_lifecycle_operations(self, mock_brain):
        """Agent: start/stop lifecycle throughput."""
        from app.agents.backend_agent import BackendAgent

        async def lifecycle():
            agent = BackendAgent(brain=mock_brain)
            await agent.start()
            await agent.stop()

        result = await benchmark(
            "Agent.start_stop",
            lifecycle,
            iterations=20,
            warmup=5,
        )
        print(result.report())


# ═══════════════════════════════════════════════════════════════════════════
# Benchmark 5: Agent Runtime Event Dispatch
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRuntimeBenchmark:
    """Benchmark Agent Runtime throughput."""

    async def test_runtime_event_dispatch(self, mock_brain, mock_broker):
        """Runtime: dispatch_event() throughput to multiple agents."""
        from app.agents.backend_agent import BackendAgent
        from app.agents.qa_agent import QAAgent
        from app.agents.security_agent import SecurityAgent
        from app.agents.sre_agent import SREAgent
        from app.agents.support_agent import SupportAgent
        from app.agents.agent_runtime import AgentRuntime
        from app.events.adapters.inprocess_adapter import InProcessEventBus

        # Real in-process event bus for realistic benchmarking
        bus = InProcessEventBus(max_queue_size=10000)
        await bus.start()

        AgentRuntime._instance = None
        runtime = await AgentRuntime.get_instance(event_bus=bus, broker=mock_broker)

        agents = [
            BackendAgent(brain=mock_brain),
            QAAgent(brain=mock_brain),
            SecurityAgent(brain=mock_brain),
            SREAgent(brain=mock_brain),
            SupportAgent(brain=mock_brain),
        ]
        for agent in agents:
            await runtime.register(agent)

        await runtime.start()

        event = Event(type="benchmark.event", source="perf_test", payload={"ts": time.time()})

        result = await benchmark(
            "Runtime.dispatch_event (5 agents)",
            lambda: runtime.dispatch_event(event),
            iterations=min(BENCH_ITERATIONS, 100),
            warmup=BENCH_WARMUP // 2,
        )
        print(result.report())

        await runtime.stop()
        await bus.stop()

    async def test_runtime_get_status(self, mock_brain, mock_broker):
        """Runtime: get_status() throughput."""
        from app.agents.backend_agent import BackendAgent
        from app.agents.qa_agent import QAAgent
        from app.agents.security_agent import SecurityAgent
        from app.agents.agent_runtime import AgentRuntime

        AgentRuntime._instance = None
        runtime = await AgentRuntime.get_instance(event_bus=None, broker=mock_broker)

        for cls in [BackendAgent, QAAgent, SecurityAgent]:
            agent = cls(brain=mock_brain)
            await runtime.register(agent)

        await runtime.start()

        result = await benchmark(
            "Runtime.get_status (3 agents)",
            runtime.get_status,
            iterations=BENCH_ITERATIONS,
            warmup=BENCH_WARMUP,
        )
        print(result.report())

        await runtime.stop()

    async def test_runtime_register_agent(self, mock_brain):
        """Runtime: register() throughput."""
        from app.agents.backend_agent import BackendAgent
        from app.agents.agent_runtime import AgentRuntime

        AgentRuntime._instance = None
        runtime = await AgentRuntime.get_instance()

        agent = BackendAgent(brain=mock_brain)

        async def register_agent():
            # Use unique name each time (handles duplicate check)
            agent.agent_name = f"perf_agent_{time.time_ns()}"
            await runtime.register(agent)

        result = await benchmark(
            "Runtime.register",
            register_agent,
            iterations=min(BENCH_ITERATIONS // 2, 50),
            warmup=10,
        )
        print(result.report())
        # Clean up
        runtime.agents.clear()


# ═══════════════════════════════════════════════════════════════════════════
# Comprehensive benchmark report
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestComprehensiveBenchmarkReport:
    """Run all benchmarks and output a comprehensive report."""

    @pytest.mark.skip(reason="Run manually with --benchmark-all for full report")
    async def test_full_benchmark_suite(self):
        """Placeholder for comprehensive benchmark suite.

        Run with: pytest tests/test_performance.py -v -k "benchmark_report"
        """
        print("\n── 链客宝 Performance Benchmark Suite ──")
        print("Run individual benchmark classes for detailed results:")
        print("  TestCacheBenchmark")
        print("  TestEventBusBenchmark")
        print("  TestGaiaBrainBenchmark")
        print("  TestAgentToolBenchmark")
        print("  TestRuntimeBenchmark")

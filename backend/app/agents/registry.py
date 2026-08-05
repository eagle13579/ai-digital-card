"""Action Registry — decorator-based tool registration with automatic dependency injection.

Injected from BrowserUse's @action decorator + Registry pattern (tools/registry/service.py
and tools/registry/views.py). Provides:

    - @register_action decorator:  Declarative tool registration with metadata
    - ActionRegistry class:        Central registry for all agent tools
    - Automatic dependency injection:  Resolves agent.brain, agent.memory, etc.
      from function parameter names (mirrors BrowserUse's SpecialActionParameters)

BrowserUse's Registry is generic over context type (Registry[Context]) and supports
both Type 1 (param_model=SomeModel) and Type 2 (inferred from signature) patterns.
This adaptation applies the same architecture to the content factory's agent framework.

Usage:
    from app.agents.registry import register_action, ActionRegistry

    registry = ActionRegistry()

    @register_action(registry, "Generate marketing copy", domain="marketing")
    async def generate_copy(prompt: str, style: str = "professional") -> str:
        return await some_llm_call(prompt, style)

    # With automatic dependency injection:
    @register_action(registry, "Research topic using brain")
    async def research_topic(query: str, brain: "GaiaEvolutionBrain") -> str:
        results = await brain.vector_search(query)
        return results

    # Execute:
    result = await registry.execute("generate_copy", prompt="Hello world")
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Concatenate, ParamSpec, TypeVar

from pydantic import BaseModel, ConfigDict, Field, create_model

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")

# ======================================================================
# Special parameter names — BrowserUse's SpecialActionParameters adaptation
# ======================================================================

# These parameter names in an action function trigger automatic injection
# from the agent's context (mirrors browser_use.tools.registry.views.SpecialActionParameters)
SPECIAL_PARAM_NAMES: set[str] = {
    "brain",           # injects agent.brain (GaiaEvolutionBrain)
    "agent",           # injects the BaseAgent instance itself
    "agent_id",        # injects agent.agent_id
    "agent_name",      # injects agent.agent_name
    "agent_role",      # injects agent.agent_role
    "memory",          # injects agent.memory dict
    "tools",           # injects agent.tools dict
    "event_handlers",  # injects agent.event_handlers dict
    "context",         # injects arbitrary context dict (from execute call)
    "task_id",         # injects current task ID
    "runtime",         # injects the AgentRuntime instance
}

# ======================================================================
# RegisteredAction — metadata + function wrapper
# ======================================================================


class ActionCategory(str, Enum):
    """Categorization for agent actions, mirroring BrowserUse's domain filtering."""
    GENERAL = "general"
    KNOWLEDGE = "knowledge"
    ANALYSIS = "analysis"
    GENERATION = "generation"
    COMMUNICATION = "communication"
    BROWSER = "browser"
    AUTOMATION = "automation"
    SYSTEM = "system"


@dataclass
class RegisteredAction:
    """A registered action with metadata and normalized function.

    Mirrors browser_use.tools.registry.views.RegisteredAction.
    """

    name: str
    description: str
    category: ActionCategory = ActionCategory.GENERAL
    tags: list[str] = field(default_factory=list)
    domain: str = ""  # domain filter (e.g. "marketing", "security")
    param_model: type[BaseModel] | None = None
    fn: Callable[..., Any] | None = None
    wrapped_fn: Callable[..., Any] | None = None
    is_async: bool = True
    timeout_seconds: float = 0.0  # 0 = no timeout
    terminates_sequence: bool = False  # if True, stops action chain after execution

    def prompt_description(self) -> str:
        """Generate a human-readable description for LLM prompts."""
        schema = self.param_model.model_json_schema() if self.param_model else {}
        params_desc = []
        if "properties" in schema:
            for name, info in schema["properties"].items():
                ptype = info.get("type", "any")
                pdesc = info.get("description", "")
                params_desc.append(f"{name}={ptype}" + (f" ({pdesc})" if pdesc else ""))
        params_str = ", ".join(params_desc) if params_desc else "no parameters"
        return f"{self.name}: {self.description}. Args: {params_str}"

    def __repr__(self) -> str:
        return f"RegisteredAction(name='{self.name}', category={self.category.value})"


# ======================================================================
# ActionRegistry — central registry
# ======================================================================


class ActionRegistry:
    """Central registry for agent tools/actions with BrowserUse-style decorator support.

    Mirrors browser_use.tools.registry.service.Registry[Context] but adapted for
    the content factory's BaseAgent architecture.

    Patterns supported:
        Type 1 — Explicit param_model (Pydantic model):
            @register_action(registry, "desc", param_model=MyModel)
            async def my_action(params: MyModel, brain: SomeType): ...

        Type 2 — Inferred from function signature:
            @register_action(registry, "desc")
            async def my_action(text: str, count: int = 10): ...

    BrowserUse's Registry supports additional features not replicated here
    (sensitive data replacement, domain filters, product telemetry, exclusions).
    These can be added as needed.
    """

    def __init__(self, allow_dynamic_registration: bool = True) -> None:
        self._actions: dict[str, RegisteredAction] = {}
        self._allow_dynamic = allow_dynamic_registration
        self._execution_count: int = 0

    # ── Properties ──

    @property
    def actions(self) -> dict[str, RegisteredAction]:
        """All registered actions, keyed by name."""
        return dict(self._actions)

    @property
    def action_names(self) -> list[str]:
        """List of all registered action names."""
        return list(self._actions.keys())

    @property
    def execution_count(self) -> int:
        """Total actions executed through this registry."""
        return self._execution_count

    # ── Registration ──

    def register(
        self,
        name: str,
        description: str,
        category: ActionCategory = ActionCategory.GENERAL,
        tags: list[str] | None = None,
        domain: str = "",
        param_model: type[BaseModel] | None = None,
        timeout_seconds: float = 0.0,
        terminates_sequence: bool = False,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """Register a function as an agent action (decorator form).

        Args:
            name: Unique action name.
            description: Human-readable description.
            category: Action category for organizational filtering.
            tags: Optional tags for search/filtering.
            domain: Domain filter string (e.g. "marketing", "security").
            param_model: Pydantic model for parameter validation (Type 1 pattern).
            timeout_seconds: If > 0, wrap execution in asyncio.wait_for.
            terminates_sequence: If True, stops action chain after this action.

        Returns:
            Decorator that registers the function and returns the normalized wrapper.
        """
        tags = tags or []

        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            # Analyze the function signature
            sig = inspect.signature(func)
            params = list(sig.parameters.values())
            is_async = inspect.iscoroutinefunction(func)

            # Build param model if not provided (Type 2 pattern)
            actual_param_model = param_model
            if actual_param_model is None:
                # Infer from non-special parameters
                action_params = {
                    p.name: (p.annotation if p.annotation != inspect.Parameter.empty else str, ... if p.default == inspect.Parameter.empty else p.default)
                    for p in params
                    if p.name not in SPECIAL_PARAM_NAMES
                    and p.kind not in (inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL)
                }
                actual_param_model = create_model(
                    f"{func.__name__}_Params",
                    __base__=ActionModel,
                    **action_params,
                )

            # Create a normalized wrapper that handles parameter injection
            # (mirrors BrowserUse's _normalize_action_function_signature)
            async def normalized_wrapper(*args: Any, **kwargs: Any) -> Any:
                """Normalized execution with automatic dependency injection."""
                # Validate no positional args (mirrors BrowserUse behavior)
                if args:
                    raise TypeError(
                        f"{func.__name__}() does not accept positional arguments, "
                        f"only keyword arguments are allowed"
                    )

                # Separate special params from action params
                action_kwargs = {}
                special_kwargs = {}

                for k, v in kwargs.items():
                    if k in SPECIAL_PARAM_NAMES:
                        special_kwargs[k] = v
                    else:
                        action_kwargs[k] = v

                # Build call_args by iterating original function params in order
                call_args: list[Any] = []
                call_kwargs: dict[str, Any] = {}

                # If Type 1 pattern (param_model provided), first arg is the model
                if param_model is not None and params and params[0].name not in SPECIAL_PARAM_NAMES:
                    # Build the model from action_kwargs
                    if actual_param_model:
                        call_args.append(actual_param_model(**action_kwargs))
                    else:
                        # Fallback: pass kwargs directly
                        call_args.append(action_kwargs)
                else:
                    # Type 2 pattern: pass action params as individual kwargs
                    for p in params:
                        if p.name in SPECIAL_PARAM_NAMES:
                            # Inject from special_kwargs
                            if p.name in special_kwargs:
                                call_kwargs[p.name] = special_kwargs[p.name]
                            elif p.default != inspect.Parameter.empty:
                                call_kwargs[p.name] = p.default
                        elif p.name in action_kwargs:
                            call_kwargs[p.name] = action_kwargs[p.name]
                        elif p.default != inspect.Parameter.empty:
                            call_kwargs[p.name] = p.default
                        else:
                            # Missing required parameter — try to find it in special_kwargs too
                            if p.name in special_kwargs:
                                call_kwargs[p.name] = special_kwargs[p.name]
                            else:
                                raise ValueError(f"Missing required parameter: '{p.name}' for action '{func.__name__}'")

                # Apply timeout if configured
                if timeout_seconds > 0:
                    async def _timed_call() -> Any:
                        if is_async:
                            return await func(*call_args, **call_kwargs)
                        else:
                            return await asyncio.to_thread(func, *call_args, **call_kwargs)

                    return await asyncio.wait_for(_timed_call(), timeout=timeout_seconds)
                else:
                    if is_async:
                        return await func(*call_args, **call_kwargs)
                    else:
                        return await asyncio.to_thread(func, *call_args, **call_kwargs)

            # Store the registered action
            action = RegisteredAction(
                name=name,
                description=description,
                category=category,
                tags=tags,
                domain=domain,
                param_model=actual_param_model,
                fn=func,
                wrapped_fn=normalized_wrapper,
                is_async=is_async,
                timeout_seconds=timeout_seconds,
                terminates_sequence=terminates_sequence,
            )
            self._actions[name] = action

            logger.debug("Registered action: %s (%s) — %s", name, category.value, description[:50])

            # Return the normalized wrapper (or original if no injection needed)
            return normalized_wrapper  # type: ignore[return-value]

        return decorator

    # ── Direct registration (non-decorator) ──

    def register_simple(
        self,
        name: str,
        fn: Callable[..., Any],
        description: str = "",
        category: ActionCategory = ActionCategory.GENERAL,
        **metadata: Any,
    ) -> None:
        """Register a function directly without decorator syntax.

        Args:
            name: Unique action name.
            fn: The function to register.
            description: Human-readable description.
            category: Action category.
            **metadata: Additional RegisteredAction fields.
        """
        is_async = inspect.iscoroutinefunction(fn)
        sig = inspect.signature(fn)
        params = {
            p.name: (p.annotation if p.annotation != inspect.Parameter.empty else str, ... if p.default == inspect.Parameter.empty else p.default)
            for p in sig.parameters.values()
            if p.name not in SPECIAL_PARAM_NAMES
        }
        param_model = create_model(f"{name}_Params", __base__=ActionModel, **params) if params else None

        action = RegisteredAction(
            name=name,
            description=description or name,
            category=category,
            fn=fn,
            param_model=param_model,
            is_async=is_async,
            **metadata,
        )
        self._actions[name] = action
        logger.debug("Registered simple action: %s", name)

    # ── Execution ──

    async def execute(
        self,
        action_name: str,
        params: dict[str, Any] | None = None,
        **injected: Any,
    ) -> Any:
        """Execute a registered action with automatic dependency injection.

        Args:
            action_name: Name of the registered action.
            params: Action parameters (merged with injected kwargs).
            **injected: Injected dependencies (brain, agent, context, etc.).

        Returns:
            The action's return value.

        Raises:
            ValueError: If action is not found.
            RuntimeError: If execution fails.

        Mirrors BrowserUse's Registry.execute_action() method.
        """
        if action_name not in self._actions:
            raise ValueError(f"Action '{action_name}' not found. Available: {list(self._actions.keys())}")

        action = self._actions[action_name]
        self._execution_count += 1

        # Merge params with injected kwargs
        call_kwargs = dict(params or {})
        call_kwargs.update(injected)

        try:
            if action.wrapped_fn:
                result = await action.wrapped_fn(**call_kwargs)
            elif action.fn:
                if action.is_async:
                    result = await action.fn(**call_kwargs)
                else:
                    result = await asyncio.to_thread(action.fn, **call_kwargs)
            else:
                raise RuntimeError(f"Action '{action_name}' has no callable function")
            return result
        except asyncio.TimeoutError:
            raise RuntimeError(f"Action '{action_name}' timed out (timeout={action.timeout_seconds}s)")
        except Exception as e:
            raise RuntimeError(f"Error executing action '{action_name}': {type(e).__name__}: {e}") from e

    # ── Convenience ──

    def get_prompt_description(self, category: ActionCategory | None = None) -> str:
        """Get formatted descriptions of all (or filtered) actions for LLM prompts.

        Args:
            category: If provided, only include actions of this category.

        Returns:
            Newline-separated action descriptions.
        """
        lines: list[str] = []
        for action in self._actions.values():
            if category is None or action.category == category:
                lines.append(action.prompt_description())
        return "\n".join(lines)

    def find(self, tag: str) -> list[RegisteredAction]:
        """Find actions by tag."""
        return [a for a in self._actions.values() if tag in a.tags]

    def count(self) -> int:
        """Number of registered actions."""
        return len(self._actions)


# ======================================================================
# ActionModel — base Pydantic model for auto-generated param models
# ======================================================================


class ActionModel(BaseModel):
    """Base model for dynamically created action parameter models.

    Mirrors browser_use.tools.registry.views.ActionModel.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    def get_param(self, key: str, default: Any = None) -> Any:
        """Safely get a parameter value."""
        return getattr(self, key, default)

    def dict_params(self) -> dict[str, Any]:
        """Get all set parameters as a dict."""
        return self.model_dump(exclude_unset=True)


# ======================================================================
# Decorator shorthand — BrowserUse @registry.action(pattern) equivalent
# ======================================================================


def register_action(
    registry: ActionRegistry,
    description: str,
    category: ActionCategory = ActionCategory.GENERAL,
    tags: list[str] | None = None,
    domain: str = "",
    param_model: type[BaseModel] | None = None,
    timeout_seconds: float = 0.0,
    terminates_sequence: bool = False,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator shorthand for registering an action.

    This is the equivalent of BrowserUse's @registry.action('Description').

    Args:
        registry: The ActionRegistry to register on.
        description: Human-readable description.
        category: Action category.
        tags: Optional tags.
        domain: Domain filter string.
        param_model: Pydantic model for parameters (Type 1 pattern).
        timeout_seconds: Optional execution timeout.
        terminates_sequence: If True, stops action chain.

    Usage:
        registry = ActionRegistry()

        @register_action(registry, "Generate content", category=ActionCategory.GENERATION)
        async def generate(topic: str, style: str = "professional") -> str:
            return await llm.generate(topic, style)
    """
    # We use a closure trick — the decorator will extract the name from func.__name__
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        name = func.__name__
        return registry.register(
            name=name,
            description=description,
            category=category,
            tags=tags,
            domain=domain,
            param_model=param_model,
            timeout_seconds=timeout_seconds,
            terminates_sequence=terminates_sequence,
        )(func)

    return decorator


# ======================================================================
# AgentIntegration — mixin/helper to add Registry to a BaseAgent
# ======================================================================


class AgentActionMixin:
    """Mixin for BaseAgent subclasses to add Registry support.

    Provides:
        - self.action_registry: ActionRegistry instance
        - self.register_action(...): Decorator registration
        - self.execute_action(name, params): Action execution
        - self.get_action_descriptions(): For LLM prompts

    Usage:
        class MyAgent(BaseAgent, AgentActionMixin):
            def __init__(self, ...):
                BaseAgent.__init__(self, ...)
                AgentActionMixin.__init__(self)

            async def init(self):
                await self._register_actions()

            async def _register_actions(self):
                from app.agents.registry import register_action, ActionCategory

                @register_action(self.action_registry, "Do something")
                async def my_action(param1: str) -> str:
                    return f"Processed: {param1}"
    """

    def __init__(self) -> None:
        self.action_registry: ActionRegistry = ActionRegistry()

    async def execute_action(self, action_name: str, params: dict[str, Any] | None = None, **injected: Any) -> Any:
        """Execute a registered action.

        Automatically injects agent context from self.
        """
        # Auto-inject standard dependencies
        auto_inject = {
            "agent": self,
            "brain": getattr(self, "brain", None),
            "agent_id": getattr(self, "agent_id", ""),
            "agent_name": getattr(self, "agent_name", ""),
            "agent_role": getattr(self, "agent_role", ""),
            "memory": getattr(self, "memory", {}),
            "tools": getattr(self, "tools", {}),
            "event_handlers": getattr(self, "event_handlers", {}),
            "runtime": getattr(self, "runtime", None),
        }
        auto_inject.update(injected)
        return await self.action_registry.execute(action_name, params=params, **auto_inject)

    def get_action_descriptions(self, category: ActionCategory | None = None) -> str:
        """Get all registered action descriptions for prompts."""
        return self.action_registry.get_prompt_description(category=category)

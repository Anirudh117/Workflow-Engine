from __future__ import annotations
import copy
import inspect
from typing import Any, Callable, Awaitable, Optional

from .models import (
    Condition,
    ExecutionStep,
    GraphDefinition,
    GraphRun,
    RunStatus,
)
from .registry import ToolRegistry


def _get_from_state(state: dict, key: str) -> Any:
    parts = key.split(".")
    value: Any = state
    for p in parts:
        if not isinstance(value, dict) or p not in value:
            return None
        value = value[p]
    return value


def _compare(left: Any, op: str, right: Any) -> bool:
    if op == "lt":
        return left < right
    if op == "lte":
        return left <= right
    if op == "gt":
        return left > right
    if op == "gte":
        return left >= right
    if op == "eq":
        return left == right
    if op == "ne":
        return left != right
    raise ValueError(f"Unsupported operator: {op}")


def _resolve_next_node(
    state: dict,
    node_name: str,
    node_config,
    default_next: str | None,
) -> str | None:
    condition: Condition | None = node_config.condition
    if not condition:
        return default_next
    value = _get_from_state(state, condition.key)
    result = _compare(value, condition.op, condition.value)
    return condition.on_true if result else condition.on_false


class WorkflowEngine:
    def __init__(
        self,
        registry: ToolRegistry,
        log_callback: Optional[Callable[[str, ExecutionStep], Awaitable[None]]] = None,
    ) -> None:
        self.registry = registry
        self.log_callback = log_callback

    async def run(
        self,
        graph: GraphDefinition,
        run: GraphRun,
        max_steps: int = 100,
    ) -> None:
        state = run.state
        current = graph.start_node
        run.current_node = current
        run.status = RunStatus.RUNNING
        step_count = 0

        while current is not None:
            step_count += 1
            if step_count > max_steps:
                run.status = RunStatus.FAILED
                run.error = f"Max steps {max_steps} exceeded"
                run.current_node = current
                return

            node_config = graph.nodes.get(current)
            if node_config is None:
                run.status = RunStatus.FAILED
                run.error = f"Unknown node: {current}"
                run.current_node = current
                return

            tool = self.registry.get(node_config.tool)
            if tool is None:
                run.status = RunStatus.FAILED
                run.error = f"Unknown tool: {node_config.tool}"
                run.current_node = current
                return

            try:
                if inspect.iscoroutinefunction(tool):
                    result = await tool(state)
                else:
                    result = tool(state)
            except Exception as exc:
                run.status = RunStatus.FAILED
                run.error = f"Error in node '{current}' with tool '{node_config.tool}': {exc}"
                run.current_node = current
                return

            if result is not None:
                if not isinstance(result, dict):
                    run.status = RunStatus.FAILED
                    run.error = f"Tool '{node_config.tool}' must return a dict, got {type(result)}"
                    run.current_node = current
                    return
                state.update(result)

            step_obj = ExecutionStep(
                step=step_count,
                node=current,
                state_snapshot=copy.deepcopy(state),
            )
            run.log.append(step_obj)

            if self.log_callback is not None:
                await self.log_callback(run.id, step_obj)

            next_node = _resolve_next_node(
                state=state,
                node_name=current,
                node_config=node_config,
                default_next=node_config.next,
            )

            current = next_node
            run.current_node = current

        run.status = RunStatus.COMPLETED
        run.current_node = None

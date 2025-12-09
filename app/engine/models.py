from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field


class Condition(BaseModel):
    key: str
    op: Literal["lt", "lte", "gt", "gte", "eq", "ne"]
    value: Any
    on_true: Optional[str] = None
    on_false: Optional[str] = None


class NodeConfig(BaseModel):
    tool: str
    next: Optional[str] = None
    condition: Optional[Condition] = None


class GraphCreateRequest(BaseModel):
    name: str
    nodes: Dict[str, NodeConfig]
    start_node: str


class GraphDefinition(BaseModel):
    id: str
    name: str
    nodes: Dict[str, NodeConfig]
    start_node: str


class ExecutionStep(BaseModel):
    step: int
    node: str
    state_snapshot: Dict[str, Any]


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class GraphRun(BaseModel):
    id: str
    graph_id: str
    status: RunStatus = RunStatus.PENDING
    current_node: Optional[str] = None
    state: Dict[str, Any] = Field(default_factory=dict)
    log: List[ExecutionStep] = Field(default_factory=list)
    error: Optional[str] = None


class GraphRunRequest(BaseModel):
    graph_id: str
    initial_state: Dict[str, Any] = Field(default_factory=dict)
    max_steps: int = 100


class GraphRunResponse(BaseModel):
    run_id: str
    final_state: Dict[str, Any]
    log: List[ExecutionStep]
    status: RunStatus
    error: Optional[str] = None


class GraphCreateResponse(BaseModel):
    graph_id: str
    name: str


class GraphRunStatusResponse(BaseModel):
    run_id: str
    graph_id: str
    status: RunStatus
    current_node: Optional[str]
    state: Dict[str, Any]
    log: List[ExecutionStep]
    error: Optional[str] = None

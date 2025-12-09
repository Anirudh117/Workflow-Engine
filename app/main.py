from __future__ import annotations

from typing import Dict, List
from uuid import uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.engine import (
    ExecutionStep,
    GraphCreateRequest,
    GraphCreateResponse,
    GraphDefinition,
    GraphRun,
    GraphRunRequest,
    GraphRunResponse,
    GraphRunStatusResponse,
    RunStatus,
    ToolRegistry,
    WorkflowEngine,
)
from app.workflows import register_summarization_tools, build_default_summarization_graph

app = FastAPI(
    title="Minimal Agent Workflow Engine",
    version="1.1.0",
    description="Simplified agent workflow engine for the Tredence assignment with WebSocket log streaming.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GRAPHS: Dict[str, GraphDefinition] = {}
RUNS: Dict[str, GraphRun] = {}

tool_registry = ToolRegistry()
CONNECTIONS: Dict[str, List[WebSocket]] = {}


async def broadcast_step(run_id: str, step: ExecutionStep) -> None:
    websockets = CONNECTIONS.get(run_id)
    if not websockets:
        return
    dead: List[WebSocket] = []
    for ws in websockets:
        try:
            await ws.send_json(
                {
                    "run_id": run_id,
                    "step": step.step,
                    "node": step.node,
                    "state_snapshot": step.state_snapshot,
                }
            )
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in websockets:
            websockets.remove(ws)
    if websockets == [] and run_id in CONNECTIONS:
        del CONNECTIONS[run_id]


engine = WorkflowEngine(tool_registry, log_callback=broadcast_step)


@app.websocket("/ws/logs/{run_id}")
async def websocket_logs(websocket: WebSocket, run_id: str) -> None:
    await websocket.accept()
    if run_id not in CONNECTIONS:
        CONNECTIONS[run_id] = []
    CONNECTIONS[run_id].append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if run_id in CONNECTIONS and websocket in CONNECTIONS[run_id]:
            CONNECTIONS[run_id].remove(websocket)
            if not CONNECTIONS[run_id]:
                del CONNECTIONS[run_id]


@app.on_event("startup")
async def startup_event() -> None:
    register_summarization_tools(tool_registry)
    default_graph_request: GraphCreateRequest = build_default_summarization_graph()
    graph_id = str(uuid4())
    graph_def = GraphDefinition(
        id=graph_id,
        name=default_graph_request.name,
        nodes=default_graph_request.nodes,
        start_node=default_graph_request.start_node,
    )
    GRAPHS[graph_id] = graph_def
    print(f"[startup] Default summarization graph created with id: {graph_id}")


@app.post("/graph/create", response_model=GraphCreateResponse)
async def create_graph(payload: GraphCreateRequest) -> GraphCreateResponse:
    if payload.start_node not in payload.nodes:
        raise HTTPException(
            status_code=400,
            detail=f"start_node '{payload.start_node}' not found in nodes",
        )
    graph_id = str(uuid4())
    graph_def = GraphDefinition(
        id=graph_id,
        name=payload.name,
        nodes=payload.nodes,
        start_node=payload.start_node,
    )
    GRAPHS[graph_id] = graph_def
    return GraphCreateResponse(graph_id=graph_id, name=graph_def.name)


@app.post("/graph/run", response_model=GraphRunResponse)
async def run_graph(payload: GraphRunRequest) -> GraphRunResponse:
    graph = GRAPHS.get(payload.graph_id)
    if graph is None:
        raise HTTPException(
            status_code=404,
            detail=f"Graph '{payload.graph_id}' not found",
        )
    run_id = str(uuid4())
    run = GraphRun(
        id=run_id,
        graph_id=graph.id,
        status=RunStatus.PENDING,
        state=payload.initial_state.copy(),
        log=[],
    )
    RUNS[run_id] = run
    await engine.run(graph=graph, run=run, max_steps=payload.max_steps)
    return GraphRunResponse(
        run_id=run.id,
        final_state=run.state,
        log=run.log,
        status=run.status,
        error=run.error,
    )


@app.get("/graph/state/{run_id}", response_model=GraphRunStatusResponse)
async def get_graph_state(run_id: str) -> GraphRunStatusResponse:
    run = RUNS.get(run_id)
    if run is None:
        raise HTTPException(
            status_code=404,
            detail=f"Run '{run_id}' not found",
        )
    return GraphRunStatusResponse(
        run_id=run.id,
        graph_id=run.graph_id,
        status=run.status,
        current_node=run.current_node,
        state=run.state,
        log=run.log,
        error=run.error,
    )


@app.get("/tools")
async def list_tools() -> Dict[str, str]:
    return tool_registry.list_tools()


@app.get("/graphs")
async def list_graphs() -> Dict[str, Dict[str, str]]:
    return {gid: {"name": g.name} for gid, g in GRAPHS.items()}

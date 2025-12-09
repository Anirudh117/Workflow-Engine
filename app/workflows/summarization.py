from __future__ import annotations
import math
from typing import Any, Dict, List
from app.engine.models import GraphCreateRequest, NodeConfig, Condition
from app.engine.registry import ToolRegistry

def register_summarization_tools(registry: ToolRegistry) -> None:

    @registry.register("split_text")
    def split_text_tool(state: Dict[str, Any]) -> Dict[str, Any]:
        text: str = state.get("input_text", "")
        if not text.strip():
            return {"chunks": []}
        chunk_size: int = int(state.get("chunk_size", 80))
        words = text.split()
        chunks: List[str] = []
        for i in range(0, len(words), chunk_size):
            chunks.append(" ".join(words[i:i + chunk_size]))
        return {"chunks": chunks}

    @registry.register("summarize_chunks")
    def summarize_chunks_tool(state: Dict[str, Any]) -> Dict[str, Any]:
        chunks: List[str] = state.get("chunks", [])
        summaries: List[str] = []
        for chunk in chunks:
            words = chunk.split()
            if not words:
                summaries.append("")
                continue
            half = max(1, len(words) // 2)
            summaries.append(" ".join(words[:half]))
        return {"summaries": summaries}

    @registry.register("merge_summaries")
    def merge_summaries_tool(state: Dict[str, Any]) -> Dict[str, Any]:
        summaries: List[str] = state.get("summaries", [])
        merged = " ".join(s for s in summaries if s.strip())
        return {"merged_summary": merged}

    @registry.register("refine_summary")
    def refine_summary_tool(state: Dict[str, Any]) -> Dict[str, Any]:
        max_words = int(state.get("summary_max_words", 60))
        base = state.get("final_summary") or state.get("merged_summary") or ""
        words = base.split()
        current_len = len(words)

        if current_len <= max_words:
            return {
                "final_summary": base,
                "final_summary_word_count": current_len,
                "refinement_done": True,
            }

        target_len = max(max_words, math.ceil(current_len * 0.8))
        shortened = " ".join(words[:target_len])
        new_len = len(shortened.split())
        refinement_done = new_len <= max_words

        return {
            "final_summary": shortened,
            "final_summary_word_count": new_len,
            "refinement_done": refinement_done,
        }

def build_default_summarization_graph() -> GraphCreateRequest:
    nodes = {
        "split_text": NodeConfig(tool="split_text", next="summarize_chunks"),
        "summarize_chunks": NodeConfig(tool="summarize_chunks", next="merge_summaries"),
        "merge_summaries": NodeConfig(tool="merge_summaries", next="refine_summary"),
        "refine_summary": NodeConfig(
            tool="refine_summary",
            next=None,
            condition=Condition(
                key="refinement_done",
                op="eq",
                value=True,
                on_true=None,
                on_false="refine_summary",
            ),
        ),
    }

    return GraphCreateRequest(
        name="summarization_and_refinement",
        nodes=nodes,
        start_node="split_text",
    )

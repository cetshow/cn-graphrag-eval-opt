from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from cn_graphrag_eval_opt.chunking import ChineseTextSplitter
from cn_graphrag_eval_opt.corpus import load_corpus
from cn_graphrag_eval_opt.llm import build_llm_request_plan, load_llm_config
from cn_graphrag_eval_opt.models import PipelineConfig
from cn_graphrag_eval_opt.service import QueryService


def run_product_doctor(
    *,
    corpus_path: str | Path,
    env_path: str | Path,
    question: str,
    config: PipelineConfig,
) -> dict[str, object]:
    """Run non-network checks that prove the local RAG path is ready before live LLM calls."""

    documents = load_corpus(corpus_path)
    chunks = ChineseTextSplitter(
        chunk_size=config.chunk_size,
        overlap=config.overlap,
        strategy=config.chunk_strategy,
    ).split_many(documents)

    service = QueryService.from_paths(corpus_path, config)
    response = service.query_response(question, answer_mode="extractive")
    llm_config = load_llm_config(env_path)
    recommendations = []
    if not llm_config.is_configured:
        recommendations.append("Set LLM_API_KEY in .env before running online MiMo answers.")

    top_chunk_ids = [context.chunk_id for context in response.contexts]
    offline_ready = bool(documents and chunks and response.contexts)
    return {
        "ok": offline_ready,
        "offline_ready": offline_ready,
        "online_ready": llm_config.is_configured,
        "checks": {
            "corpus": {
                "ok": bool(documents),
                "documents": len(documents),
                "chunks": len(chunks),
                "path": str(corpus_path),
            },
            "retrieval": {
                "ok": bool(response.contexts),
                "retrieved_count": len(response.contexts),
                "top_chunk_ids": top_chunk_ids,
                "query_mode": config.query_mode,
                "top_k": config.top_k,
            },
            "answer_audit": {
                "ok": response.trace.grounded,
                "grounded": response.trace.grounded,
                "citation_coverage": response.trace.citation_coverage,
                "warnings": response.trace.warnings,
            },
        },
        "config": asdict(config),
        "llm": llm_config.to_safe_dict(),
        "llm_request_plan": build_llm_request_plan(llm_config, question),
        "recommendations": recommendations,
    }

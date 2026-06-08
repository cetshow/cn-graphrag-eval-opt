from __future__ import annotations

from cn_graphrag_eval_opt.chunking import ChineseTextSplitter
from cn_graphrag_eval_opt.evaluation import evaluate_cases
from cn_graphrag_eval_opt.graph import GraphIndex
from cn_graphrag_eval_opt.models import Document, OptimizationResult, PipelineConfig, QACase, TrialSummary
from cn_graphrag_eval_opt.retrieval import GraphRAGRetriever

MODE_PRIORITY = {"naive": 1, "local": 2, "global": 3, "hybrid": 4, "mix": 5}


def default_configs() -> list[PipelineConfig]:
    return [
        PipelineConfig(chunk_size=96, overlap=12, top_k=2, query_mode="naive"),
        PipelineConfig(chunk_size=128, overlap=16, top_k=3, query_mode="local"),
        PipelineConfig(chunk_size=128, overlap=16, top_k=3, query_mode="global"),
        PipelineConfig(chunk_size=160, overlap=24, top_k=3, query_mode="hybrid"),
        PipelineConfig(chunk_size=192, overlap=24, top_k=4, query_mode="mix"),
    ]


def run_optimization(
    documents: list[Document],
    qa_cases: list[QACase],
    configs: list[PipelineConfig] | None = None,
) -> OptimizationResult:
    if not documents:
        raise ValueError("documents must not be empty")
    if not qa_cases:
        raise ValueError("qa_cases must not be empty")

    trial_summaries: list[TrialSummary] = []
    for config in configs or default_configs():
        splitter = ChineseTextSplitter(
            chunk_size=config.chunk_size,
            overlap=config.overlap,
            strategy=config.chunk_strategy,
        )
        chunks = splitter.split_many(documents)
        index = GraphIndex.from_chunks(chunks)
        retriever = GraphRAGRetriever(index)
        evaluation = evaluate_cases(qa_cases, retriever, config)
        trial_summaries.append(
            TrialSummary(
                config=config,
                metrics=evaluation.aggregate,
                case_count=len(evaluation.cases),
            )
        )

    best = max(trial_summaries, key=_rank_trial)
    return OptimizationResult(trials=trial_summaries, best_config=best.config, best_summary=best)


def _rank_trial(summary: TrialSummary) -> tuple[float, float, float, float, int, float]:
    metrics = summary.metrics
    return (
        metrics.get("retrieval_recall", 0.0),
        metrics.get("faithfulness", 0.0),
        metrics.get("answer_relevance", 0.0),
        metrics.get("context_precision", 0.0),
        MODE_PRIORITY.get(summary.config.query_mode, 0),
        -metrics.get("estimated_token_cost", 0.0),
    )

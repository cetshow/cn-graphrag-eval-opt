from __future__ import annotations

import importlib.util
from dataclasses import dataclass

from cn_graphrag_eval_opt.models import PipelineConfig


@dataclass(frozen=True)
class IntegrationStatus:
    package: str
    available: bool
    role: str


def optional_integrations() -> list[IntegrationStatus]:
    return [
        IntegrationStatus("lightrag", _available("lightrag"), "GraphRAG indexing/query backend"),
        IntegrationStatus("autorag", _available("autorag"), "pipeline search backend"),
        IntegrationStatus("ragas", _available("ragas"), "LLM-based RAG evaluation metrics"),
    ]


def export_autorag_like_config(config: PipelineConfig) -> dict[str, object]:
    return {
        "node_lines": [
            {
                "node_line_name": "retrieve_node_line",
                "nodes": [
                    {
                        "node_type": "hybrid_retrieval",
                        "strategy": {
                            "metrics": [
                                "retrieval_recall",
                                "context_precision",
                                "faithfulness",
                                "answer_relevance",
                            ]
                        },
                        "top_k": config.top_k,
                        "modules": [
                            {
                                "module_type": f"cn_graphrag_{config.query_mode}",
                                "chunk_size": config.chunk_size,
                                "chunk_overlap": config.overlap,
                            }
                        ],
                    }
                ],
            }
        ]
    }


def ragas_metric_mapping() -> dict[str, str]:
    return {
        "retrieval_recall": "context_recall",
        "context_precision": "context_precision",
        "answer_relevance": "answer_relevancy",
        "faithfulness": "faithfulness",
    }


def _available(module: str) -> bool:
    return importlib.util.find_spec(module) is not None

from __future__ import annotations

from dataclasses import dataclass

from cn_graphrag_eval_opt.models import PipelineConfig
from cn_graphrag_eval_opt.providers import default_provider_registry


@dataclass(frozen=True)
class IntegrationStatus:
    name: str
    package: str
    available: bool
    role: str
    capabilities: tuple[str, ...]
    import_name: str
    install_hint: str


def optional_integrations() -> list[IntegrationStatus]:
    return [
        IntegrationStatus(
            name=provider.name,
            package=provider.package,
            available=provider.available,
            role=provider.role,
            capabilities=provider.capabilities,
            import_name=provider.import_name,
            install_hint=provider.install_hint,
        )
        for provider in default_provider_registry().list()
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

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class UpstreamReference:
    name: str
    url: str
    license: str
    reuse_mode: str
    adopted_ideas: list[str]


def upstream_references() -> list[UpstreamReference]:
    return [
        UpstreamReference(
            name="Microsoft GraphRAG",
            url="https://github.com/microsoft/graphrag",
            license="MIT License",
            reuse_mode="architectural reference",
            adopted_ideas=["graph-centered retrieval vocabulary", "local/global query framing"],
        ),
        UpstreamReference(
            name="LightRAG",
            url="https://github.com/HKUDS/LightRAG",
            license="MIT License",
            reuse_mode="architectural reference",
            adopted_ideas=["lightweight graph indexing", "incremental document status tracking"],
        ),
        UpstreamReference(
            name="AutoRAG",
            url="https://github.com/Marker-Inc-Korea/AutoRAG",
            license="Apache License 2.0",
            reuse_mode="evaluation reference",
            adopted_ideas=["pipeline search", "leaderboard-style optimization reports"],
        ),
        UpstreamReference(
            name="RAGFlow",
            url="https://github.com/infiniflow/ragflow",
            license="Apache License 2.0",
            reuse_mode="product reference",
            adopted_ideas=["traceable citations", "document parsing and workflow boundary"],
        ),
        UpstreamReference(
            name="Ragas",
            url="https://github.com/explodinggradients/ragas",
            license="Apache License 2.0",
            reuse_mode="metric vocabulary reference",
            adopted_ideas=["faithfulness and answer relevance terminology"],
        ),
        UpstreamReference(
            name="R2R",
            url="https://github.com/SciPhi-AI/R2R",
            license="MIT License",
            reuse_mode="API and agentic retrieval reference",
            adopted_ideas=["production RAG service shape", "multi-step retrieval roadmap"],
        ),
    ]


def provenance_policy() -> dict[str, object]:
    return {
        "project_license": "MIT License",
        "current_source_policy": (
            "Original source code; this repository does not vendor, copy, or modify upstream "
            "project source unless a file states otherwise."
        ),
        "reuse_requirements": [
            "Keep inspiration-only references documented in README.md, NOTICE.md, and docs/references.md.",
            (
                "If source code is copied, modified, or derived from an upstream project, preserve "
                "copyright notices, license text, NOTICE obligations, and local modification notes."
            ),
            "Optional integrations remain third-party packages governed by their own licenses.",
        ],
        "references": [asdict(reference) for reference in upstream_references()],
    }

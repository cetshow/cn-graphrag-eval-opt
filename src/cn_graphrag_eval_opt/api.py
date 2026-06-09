from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class QueryRequest:
    question: str
    query_mode: str = "mix"
    top_k: int = 3
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Citation:
    chunk_id: str
    doc_id: str
    title: str
    source: str
    score: float
    evidence: list[str]
    text: str


@dataclass(frozen=True)
class QueryTrace:
    query_mode: str
    top_k: int
    retrieved_count: int
    answer_mode: str = "extractive"
    llm_provider: str | None = None
    llm_model: str | None = None
    grounded: bool = True
    citation_coverage: float = 1.0
    cited_chunk_ids: list[str] = field(default_factory=list)
    missing_citation_ids: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class QueryResponse:
    question: str
    answer: str
    contexts: list[Citation]
    config: dict[str, object]
    trace: QueryTrace

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

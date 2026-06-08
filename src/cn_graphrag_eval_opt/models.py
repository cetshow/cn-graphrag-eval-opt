from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


QUERY_MODES = {"naive", "local", "global", "hybrid", "mix"}


@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    text: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    source: str
    title: str
    start: int = 0
    end: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class QACase:
    question: str
    answer: str = ""
    required_terms: list[str] = field(default_factory=list)
    gold_context_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievalResult:
    chunk: Chunk
    score: float
    mode: str
    evidence: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PipelineConfig:
    chunk_size: int = 256
    overlap: int = 32
    top_k: int = 3
    query_mode: str = "mix"
    chunk_strategy: str = "recursive"

    def __post_init__(self) -> None:
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.overlap < 0 or self.overlap >= self.chunk_size:
            raise ValueError("overlap must be non-negative and smaller than chunk_size")
        if self.top_k <= 0:
            raise ValueError("top_k must be positive")
        if self.query_mode not in QUERY_MODES:
            raise ValueError(f"query_mode must be one of {sorted(QUERY_MODES)}")

    @property
    def label(self) -> str:
        return (
            f"{self.query_mode}-chunk{self.chunk_size}"
            f"-overlap{self.overlap}-top{self.top_k}"
        )


@dataclass(frozen=True)
class CaseEvaluation:
    question: str
    expected_answer: str
    generated_answer: str
    retrieved_chunk_ids: list[str]
    metrics: dict[str, float]


@dataclass(frozen=True)
class EvaluationResult:
    cases: list[CaseEvaluation]
    aggregate: dict[str, float]


@dataclass(frozen=True)
class TrialSummary:
    config: PipelineConfig
    metrics: dict[str, float]
    case_count: int


@dataclass(frozen=True)
class OptimizationResult:
    trials: list[TrialSummary]
    best_config: PipelineConfig
    best_summary: TrialSummary

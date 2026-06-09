from __future__ import annotations

import re
from dataclasses import asdict
from pathlib import Path
from typing import Callable

from cn_graphrag_eval_opt.api import Citation, QueryResponse, QueryTrace
from cn_graphrag_eval_opt.chunking import ChineseTextSplitter
from cn_graphrag_eval_opt.corpus import load_corpus
from cn_graphrag_eval_opt.evaluation import synthesize_answer
from cn_graphrag_eval_opt.graph import GraphIndex
from cn_graphrag_eval_opt.models import PipelineConfig
from cn_graphrag_eval_opt.retrieval import GraphRAGRetriever

Answerer = Callable[[str, list[Citation]], str]
_CHUNK_REFERENCE_PATTERN = re.compile(r"\b[A-Za-z0-9_.-]+:\d{4,}\b")


class QueryService:
    """Small production-facing query facade inspired by R2R-style RAG services."""

    def __init__(self, retriever: GraphRAGRetriever, config: PipelineConfig) -> None:
        self.retriever = retriever
        self.config = config
        self.index = retriever.index
        self.chunks = list(retriever.index.chunks.values())

    @classmethod
    def from_paths(cls, corpus_path: str | Path, config: PipelineConfig) -> "QueryService":
        documents = load_corpus(corpus_path)
        chunks = ChineseTextSplitter(
            chunk_size=config.chunk_size,
            overlap=config.overlap,
            strategy=config.chunk_strategy,
        ).split_many(documents)
        return cls(GraphRAGRetriever(GraphIndex.from_chunks(chunks)), config)

    def query(self, question: str) -> dict[str, object]:
        return self.query_response(question).to_dict()

    def query_response(
        self,
        question: str,
        *,
        answerer: Answerer | None = None,
        answer_mode: str = "extractive",
        llm_provider: str | None = None,
        llm_model: str | None = None,
    ) -> QueryResponse:
        results = self.retriever.retrieve(
            question,
            top_k=self.config.top_k,
            mode=self.config.query_mode,
        )
        contexts = [
            Citation(
                chunk_id=result.chunk.chunk_id,
                doc_id=result.chunk.doc_id,
                title=result.chunk.title,
                source=result.chunk.source,
                score=result.score,
                evidence=result.evidence,
                text=result.chunk.text,
            )
            for result in results
        ]
        answer = (
            answerer(question, contexts)
            if answerer
            else synthesize_answer(question, [item.text for item in contexts])
        )
        audit = _audit_answer_grounding(
            answer,
            contexts,
            require_citations=answerer is not None or answer_mode not in {"extractive"},
        )
        return QueryResponse(
            question=question,
            answer=answer,
            contexts=contexts,
            config=asdict(self.config),
            trace=QueryTrace(
                query_mode=self.config.query_mode,
                top_k=self.config.top_k,
                retrieved_count=len(contexts),
                answer_mode=answer_mode,
                llm_provider=llm_provider,
                llm_model=llm_model,
                grounded=audit["grounded"],
                citation_coverage=audit["citation_coverage"],
                cited_chunk_ids=audit["cited_chunk_ids"],
                missing_citation_ids=audit["missing_citation_ids"],
                warnings=audit["warnings"],
            ),
        )


def _audit_answer_grounding(
    answer: str,
    contexts: list[Citation],
    *,
    require_citations: bool,
) -> dict[str, object]:
    valid_chunk_ids = [context.chunk_id for context in contexts]
    valid_chunk_id_set = set(valid_chunk_ids)
    cited_chunk_ids = [
        chunk_id for chunk_id in valid_chunk_ids
        if chunk_id in answer
    ]
    referenced_chunk_ids = _ordered_unique(_CHUNK_REFERENCE_PATTERN.findall(answer))
    missing_citation_ids = [
        chunk_id for chunk_id in referenced_chunk_ids
        if chunk_id not in valid_chunk_id_set
    ]
    if referenced_chunk_ids:
        citation_coverage = round(len(cited_chunk_ids) / len(referenced_chunk_ids), 4)
    else:
        citation_coverage = 0.0 if require_citations else 1.0

    warnings = []
    if require_citations and not cited_chunk_ids:
        warnings.append("answer_missing_chunk_citation")
    if missing_citation_ids:
        warnings.append("answer_has_unknown_chunk_citation")

    return {
        "grounded": (not require_citations or bool(cited_chunk_ids)) and not missing_citation_ids,
        "citation_coverage": citation_coverage,
        "cited_chunk_ids": cited_chunk_ids,
        "missing_citation_ids": missing_citation_ids,
        "warnings": warnings,
    }


def _ordered_unique(values: list[str]) -> list[str]:
    seen = set()
    unique_values = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique_values.append(value)
    return unique_values

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from cn_graphrag_eval_opt.api import Citation, QueryResponse, QueryTrace
from cn_graphrag_eval_opt.chunking import ChineseTextSplitter
from cn_graphrag_eval_opt.corpus import load_corpus
from cn_graphrag_eval_opt.evaluation import synthesize_answer
from cn_graphrag_eval_opt.graph import GraphIndex
from cn_graphrag_eval_opt.models import PipelineConfig
from cn_graphrag_eval_opt.retrieval import GraphRAGRetriever


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

    def query_response(self, question: str) -> QueryResponse:
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
        return QueryResponse(
            question=question,
            answer=synthesize_answer(question, [item.text for item in contexts]),
            contexts=contexts,
            config=asdict(self.config),
            trace=QueryTrace(
                query_mode=self.config.query_mode,
                top_k=self.config.top_k,
                retrieved_count=len(contexts),
            ),
        )

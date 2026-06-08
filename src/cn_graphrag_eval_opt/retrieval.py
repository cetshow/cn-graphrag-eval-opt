from __future__ import annotations

from collections import Counter

from cn_graphrag_eval_opt.embeddings import HashingEmbeddingModel, cosine_similarity
from cn_graphrag_eval_opt.fusion import reciprocal_rank_fusion
from cn_graphrag_eval_opt.graph import GraphIndex, extract_entities
from cn_graphrag_eval_opt.models import QUERY_MODES, RetrievalResult
from cn_graphrag_eval_opt.text import tokenize


SIGNALS_BY_MODE = {
    "naive": ("lexical", "dense"),
    "local": ("local",),
    "global": ("global",),
    "hybrid": ("lexical", "dense", "local", "global"),
    "mix": ("lexical", "dense", "local", "global"),
}


class GraphRAGRetriever:
    """LightRAG-style retriever with naive, local, global, hybrid, and mix modes."""

    def __init__(self, index: GraphIndex, embedding_model: HashingEmbeddingModel | None = None) -> None:
        self.index = index
        self.embedding_model = embedding_model or HashingEmbeddingModel()
        self._chunk_vectors = {
            chunk_id: self.embedding_model.embed(chunk.text)
            for chunk_id, chunk in self.index.chunks.items()
        }

    def retrieve(self, query: str, top_k: int = 3, mode: str = "mix") -> list[RetrievalResult]:
        if mode not in QUERY_MODES:
            raise ValueError(f"mode must be one of {sorted(QUERY_MODES)}")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        lexical = self._lexical_scores(query)
        query_entities = sorted(extract_entities(query))
        local_ids = self.index.chunk_ids_for_entities(query_entities)
        global_entities = self.index.neighbor_entities(query_entities)
        global_ids = self.index.chunk_ids_for_entities(global_entities)

        dense = self._dense_scores(query)
        signal_scores = {
            "lexical": lexical,
            "dense": dense,
            "local": self._graph_scores(local_ids, lexical, dense, base_score=2.0),
            "global": self._graph_scores(global_ids, lexical, dense, base_score=1.4),
        }
        ranked_signals = {
            signal: _ranked_ids(signal_scores[signal])
            for signal in SIGNALS_BY_MODE[mode]
            if signal_scores[signal]
        }
        if not ranked_signals:
            ranked_signals = {"lexical_fallback": _ranked_ids(lexical or dense)}

        ranked = reciprocal_rank_fusion(ranked_signals)[:top_k]
        return [
            RetrievalResult(
                chunk=self.index.chunks[item.item_id],
                score=round(item.score, 4),
                mode=mode,
                evidence=[
                    f"{contribution.signal}:rank={contribution.rank}:rrf={contribution.score:.4f}"
                    for contribution in item.signals
                ],
            )
            for item in ranked
            if item.score > 0
        ]

    def _lexical_scores(self, query: str) -> dict[str, float]:
        query_terms = Counter(tokenize(query))
        if not query_terms:
            return {}
        scores: dict[str, float] = {}
        for chunk_id, chunk in self.index.chunks.items():
            chunk_terms = Counter(tokenize(chunk.text))
            overlap = sum(min(count, chunk_terms.get(term, 0)) for term, count in query_terms.items())
            phrase_bonus = sum(0.7 for term in query_terms if term and term in chunk.text)
            if overlap or phrase_bonus:
                scores[chunk_id] = float(overlap) + phrase_bonus
        return scores

    def _dense_scores(self, query: str) -> dict[str, float]:
        query_vector = self.embedding_model.embed(query)
        scores: dict[str, float] = {}
        for chunk_id, chunk_vector in self._chunk_vectors.items():
            score = cosine_similarity(query_vector, chunk_vector)
            if score > 0:
                scores[chunk_id] = round(score * 3.0, 4)
        return scores

    def _graph_scores(
        self,
        chunk_ids: set[str],
        lexical: dict[str, float],
        dense: dict[str, float],
        *,
        base_score: float,
    ) -> dict[str, float]:
        return {
            chunk_id: (
                base_score
                + lexical.get(chunk_id, 0.0) * 0.01
                + dense.get(chunk_id, 0.0) * 0.005
            )
            for chunk_id in chunk_ids
        }


def _ranked_ids(scores: dict[str, float]) -> list[str]:
    return [chunk_id for chunk_id, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0]))]

from __future__ import annotations

from collections import Counter, defaultdict

from cn_graphrag_eval_opt.embeddings import HashingEmbeddingModel, cosine_similarity
from cn_graphrag_eval_opt.graph import GraphIndex, extract_entities
from cn_graphrag_eval_opt.models import QUERY_MODES, RetrievalResult
from cn_graphrag_eval_opt.text import tokenize


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

        scores: dict[str, float] = defaultdict(float)
        evidence: dict[str, list[str]] = defaultdict(list)

        if mode in {"naive", "hybrid", "mix"}:
            for chunk_id, score in lexical.items():
                scores[chunk_id] += score
                evidence[chunk_id].append("lexical")
            for chunk_id, score in self._dense_scores(query).items():
                scores[chunk_id] += score
                evidence[chunk_id].append("dense")

        if mode in {"local", "hybrid", "mix"}:
            for chunk_id in local_ids:
                scores[chunk_id] += 2.0
                evidence[chunk_id].append("local_entity")

        if mode in {"global", "hybrid", "mix"}:
            for chunk_id in global_ids:
                scores[chunk_id] += 1.4
                evidence[chunk_id].append("global_neighbor")

        if not scores:
            scores.update(lexical)
            for chunk_id in lexical:
                evidence[chunk_id].append("lexical_fallback")

        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:top_k]
        return [
            RetrievalResult(
                chunk=self.index.chunks[chunk_id],
                score=round(score, 4),
                mode=mode,
                evidence=evidence[chunk_id],
            )
            for chunk_id, score in ranked
            if score > 0
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

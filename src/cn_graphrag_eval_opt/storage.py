from __future__ import annotations

from cn_graphrag_eval_opt.graph import GraphIndex
from cn_graphrag_eval_opt.models import Chunk
from cn_graphrag_eval_opt.stores import IndexStoreMetadata, JsonlIndexStore


class FileIndexStore(JsonlIndexStore):
    """Backward-compatible alias for the JSONL index store."""

    def save(self, index: GraphIndex, chunks: list[Chunk] | None = None) -> IndexStoreMetadata:
        if chunks is not None:
            index = GraphIndex(
                chunks={chunk.chunk_id: chunk for chunk in chunks},
                entities=index.entities,
                edges=index.edges,
            )
        return super().save(index)

    def load(self) -> tuple[GraphIndex, list[Chunk]]:
        index = super().load()
        chunks = [index.chunks[chunk_id] for chunk_id in sorted(index.chunks)]
        return index, chunks

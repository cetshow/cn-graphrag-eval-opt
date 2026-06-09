from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from cn_graphrag_eval_opt.graph import GraphIndex
from cn_graphrag_eval_opt.models import Chunk


@dataclass(frozen=True)
class IndexStoreMetadata:
    store_type: str
    root: str
    chunk_count: int
    entity_count: int
    edge_count: int


class JsonlIndexStore:
    """Portable JSON/JSONL-backed GraphRAG index store."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def save(self, index: GraphIndex) -> IndexStoreMetadata:
        self.root.mkdir(parents=True, exist_ok=True)
        chunks = [index.chunks[chunk_id] for chunk_id in sorted(index.chunks)]
        self._chunks_path.write_text(
            "\n".join(json.dumps(asdict(chunk), ensure_ascii=False) for chunk in chunks) + "\n",
            encoding="utf-8",
        )
        self._graph_path.write_text(
            json.dumps(
                {
                    "entities": {key: sorted(value) for key, value in sorted(index.entities.items())},
                    "edges": {
                        key: dict(counter.most_common())
                        for key, counter in sorted(index.edges.items())
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        metadata = IndexStoreMetadata(
            store_type="jsonl",
            root=str(self.root),
            chunk_count=len(index.chunks),
            entity_count=len(index.entities),
            edge_count=sum(len(counter) for counter in index.edges.values()),
        )
        self._metadata_path.write_text(
            json.dumps(asdict(metadata), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return metadata

    def load(self) -> GraphIndex:
        if not self._chunks_path.exists():
            raise FileNotFoundError(f"Missing chunks file: {self._chunks_path}")
        if not self._graph_path.exists():
            raise FileNotFoundError(f"Missing graph file: {self._graph_path}")

        chunks = {
            chunk.chunk_id: chunk
            for chunk in (
                Chunk(**json.loads(line))
                for line in self._chunks_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
        }
        graph = json.loads(self._graph_path.read_text(encoding="utf-8"))
        entities = {
            entity: set(chunk_ids)
            for entity, chunk_ids in graph.get("entities", {}).items()
        }
        edges = {
            entity: Counter(neighbors)
            for entity, neighbors in graph.get("edges", {}).items()
        }
        return GraphIndex(chunks=chunks, entities=entities, edges=edges)

    def metadata(self) -> IndexStoreMetadata:
        if not self._metadata_path.exists():
            raise FileNotFoundError(f"Missing metadata file: {self._metadata_path}")
        return IndexStoreMetadata(**json.loads(self._metadata_path.read_text(encoding="utf-8")))

    @property
    def _chunks_path(self) -> Path:
        return self.root / "chunks.jsonl"

    @property
    def _graph_path(self) -> Path:
        return self.root / "graph.json"

    @property
    def _metadata_path(self) -> Path:
        return self.root / "metadata.json"

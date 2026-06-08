from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from cn_graphrag_eval_opt.graph import GraphIndex
from cn_graphrag_eval_opt.models import Chunk


class FileIndexStore:
    """File-backed index store for reproducible local trials."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def save(self, index: GraphIndex, chunks: list[Chunk]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "chunks.jsonl").write_text(
            "\n".join(json.dumps(asdict(chunk), ensure_ascii=False) for chunk in chunks) + "\n",
            encoding="utf-8",
        )
        (self.root / "graph.json").write_text(
            json.dumps(
                {
                    "entities": {key: sorted(value) for key, value in index.entities.items()},
                    "edges": {
                        key: dict(counter.most_common())
                        for key, counter in index.edges.items()
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def load(self) -> tuple[GraphIndex, list[Chunk]]:
        chunk_path = self.root / "chunks.jsonl"
        if not chunk_path.exists():
            raise FileNotFoundError(f"Missing chunks file: {chunk_path}")
        chunks = [
            Chunk(**json.loads(line))
            for line in chunk_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        return GraphIndex.from_chunks(chunks), chunks

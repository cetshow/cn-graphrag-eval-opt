import sys
import unittest
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cn_graphrag_eval_opt.graph import GraphIndex
from cn_graphrag_eval_opt.models import Chunk
from cn_graphrag_eval_opt.storage import FileIndexStore
from cn_graphrag_eval_opt.stores import JsonlIndexStore


class PersistentStoreTest(unittest.TestCase):
    def test_jsonl_index_store_round_trips_persisted_graph(self):
        chunk = Chunk(
            chunk_id="c1",
            doc_id="policy",
            title="Security policy",
            source="memory",
            text="Security System connects Access Policy.",
        )
        index = GraphIndex(
            chunks={"c1": chunk},
            entities={"Security System": {"c1"}, "Access Policy": {"c1"}},
            edges={"Security System": Counter({"Access Policy": 2})},
        )

        with TemporaryDirectory() as tmp:
            store = JsonlIndexStore(Path(tmp) / "index")
            metadata = store.save(index)
            loaded = store.load()

            self.assertEqual(metadata.chunk_count, 1)
            self.assertEqual(metadata.entity_count, 2)
            self.assertEqual(metadata.edge_count, 1)
            self.assertEqual(loaded.chunks["c1"], chunk)
            self.assertEqual(loaded.entities["Security System"], {"c1"})
            self.assertEqual(loaded.edges["Security System"]["Access Policy"], 2)
            self.assertEqual(store.metadata().store_type, "jsonl")

    def test_file_index_store_keeps_existing_tuple_api(self):
        chunk = Chunk(
            chunk_id="c1",
            doc_id="policy",
            title="Security policy",
            source="memory",
            text="Security review.",
        )
        index = GraphIndex(chunks={"c1": chunk}, entities={"Security": {"c1"}})

        with TemporaryDirectory() as tmp:
            store = FileIndexStore(Path(tmp) / "compat")
            store.save(index, [chunk])
            loaded_index, loaded_chunks = store.load()

            self.assertEqual(loaded_index.chunks["c1"], chunk)
            self.assertEqual(loaded_chunks, [chunk])


if __name__ == "__main__":
    unittest.main()

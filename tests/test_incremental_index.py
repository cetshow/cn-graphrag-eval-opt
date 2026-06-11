import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cn_graphrag_eval_opt.chunking import ChineseTextSplitter
from cn_graphrag_eval_opt.graph import GraphIndex
from cn_graphrag_eval_opt.incremental import IncrementalIndexUpdater
from cn_graphrag_eval_opt.models import Document
from cn_graphrag_eval_opt.stores import JsonlIndexStore


class IncrementalIndexTest(unittest.TestCase):
    def test_changed_and_deleted_documents_update_index_and_ledger(self):
        splitter = ChineseTextSplitter(chunk_size=80, overlap=8, strategy="sentence")
        updater = IncrementalIndexUpdater(splitter)
        documents = [
            Document(
                doc_id="access",
                title="Access Policy",
                text="Security System requires monthly access review by the Security Team.",
                source="policy/access.md",
            ),
            Document(
                doc_id="expense",
                title="Expense Policy",
                text="Finance System keeps invoice approvals for the Finance Team.",
                source="policy/expense.md",
            ),
        ]

        baseline = updater.build(documents)
        self.assertIn("access", baseline.ledger.documents)
        self.assertIn("expense", baseline.ledger.documents)
        self.assertEqual(baseline.ledger.documents["access"].chunk_ids, ["access:0000"])

        changed_access = Document(
            doc_id="access",
            title="Access Policy",
            text="Security System now requires quarterly access review by the Risk Team.",
            source="policy/access.md",
        )
        updated = updater.apply(
            baseline.index,
            baseline.ledger,
            changed_documents=[changed_access],
            deleted_doc_ids=["expense"],
        )

        self.assertEqual(updated.changed_doc_ids, ["access"])
        self.assertEqual(updated.deleted_doc_ids, ["expense"])
        self.assertEqual(sorted(updated.index.chunks), ["access:0000"])
        self.assertIn("Risk Team", updated.index.chunks["access:0000"].text)
        self.assertNotIn("expense", updated.ledger.documents)
        self.assertIn("access", updated.ledger.documents)
        self.assertNotEqual(
            baseline.ledger.documents["access"].content_hash,
            updated.ledger.documents["access"].content_hash,
        )

    def test_store_round_trips_index_ledger(self):
        splitter = ChineseTextSplitter(chunk_size=80, overlap=8, strategy="sentence")
        updater = IncrementalIndexUpdater(splitter)
        document = Document(
            doc_id="access",
            title="Access Policy",
            text="Security System requires monthly access review.",
            source="policy/access.md",
        )
        snapshot = updater.build([document])

        with tempfile.TemporaryDirectory() as tmp:
            store = JsonlIndexStore(tmp)
            store.save(snapshot.index)
            store.save_ledger(snapshot.ledger)

            loaded_index = store.load()
            loaded_ledger = store.load_ledger()

        self.assertIsInstance(loaded_index, GraphIndex)
        self.assertEqual(loaded_index.chunks, snapshot.index.chunks)
        self.assertEqual(loaded_ledger.documents["access"].chunk_ids, ["access:0000"])


if __name__ == "__main__":
    unittest.main()

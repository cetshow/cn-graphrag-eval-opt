import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cn_graphrag_eval_opt.connectors import (
    LocalFileConnector,
    default_connector_registry,
    load_documents,
)
from cn_graphrag_eval_opt.corpus import load_corpus


class CorpusConnectorTest(unittest.TestCase):
    def test_local_file_connector_loads_registered_suffixes(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "policy.md").write_text("# Policy\nSecurity review.", encoding="utf-8")
            (root / "ignored.csv").write_text("not,a,document", encoding="utf-8")

            documents = LocalFileConnector().load(root)

            self.assertEqual(len(documents), 1)
            self.assertEqual(documents[0].doc_id, "policy")
            self.assertEqual(documents[0].title, "Policy")
            self.assertEqual(documents[0].metadata["connector"], "local_files")
            self.assertEqual(documents[0].metadata["relative_path"], "policy.md")

    def test_default_connector_registry_exposes_local_file_connector(self):
        registry = default_connector_registry()

        connector = registry.get("local_files")

        self.assertEqual(connector.name, "local_files")
        self.assertIn(".md", connector.supported_suffixes)
        self.assertIn(connector, registry.list())

    def test_load_documents_and_load_corpus_share_connector_path(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ops.txt").write_text("Operations checklist.", encoding="utf-8")

            direct = load_documents(root)
            via_corpus = load_corpus(root)

            self.assertEqual(direct[0], via_corpus[0])
            self.assertEqual(via_corpus[0].metadata["connector"], "local_files")


if __name__ == "__main__":
    unittest.main()

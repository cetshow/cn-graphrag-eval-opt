import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cn_graphrag_eval_opt.chunking import ChineseTextSplitter
from cn_graphrag_eval_opt.models import Document


class ChineseTextSplitterTest(unittest.TestCase):
    def test_recursive_split_preserves_metadata_and_overlap(self):
        document = Document(
            doc_id="policy",
            title="费用报销制度",
            text="第一条 员工提交发票。第二条 财务部在三个工作日内审核。第三条 审批通过后付款。",
            source="policy.md",
        )
        splitter = ChineseTextSplitter(chunk_size=24, overlap=6, strategy="recursive")

        chunks = splitter.split(document)

        self.assertGreaterEqual(len(chunks), 2)
        self.assertTrue(all(chunk.doc_id == "policy" for chunk in chunks))
        self.assertEqual(chunks[0].metadata["strategy"], "recursive")
        self.assertIn("财务部", "".join(chunk.text for chunk in chunks))
        self.assertLessEqual(max(len(chunk.text) for chunk in chunks), 30)

    def test_invalid_overlap_is_rejected(self):
        with self.assertRaises(ValueError):
            ChineseTextSplitter(chunk_size=20, overlap=20)


if __name__ == "__main__":
    unittest.main()

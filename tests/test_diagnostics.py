import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cn_graphrag_eval_opt.diagnostics import run_product_doctor
from cn_graphrag_eval_opt.models import PipelineConfig


QUESTION = "\u54ea\u4e2a\u90e8\u95e8\u590d\u6838\u9ad8\u5371\u6743\u9650\uff1f"
SECURITY_DOC = (
    "# \u5b89\u5168\u5236\u5ea6\n"
    "\u5b89\u5168\u90e8\u6bcf\u6708\u590d\u6838\u9ad8\u5371\u6743\u9650\u3002"
)


class ProductDiagnosticsTest(unittest.TestCase):
    def test_doctor_reports_offline_and_mimo_readiness_without_network(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "security.md").write_text(SECURITY_DOC, encoding="utf-8")

            payload = run_product_doctor(
                corpus_path=root,
                env_path=".env.example",
                question=QUESTION,
                config=PipelineConfig(chunk_size=80, overlap=0, top_k=1, query_mode="mix"),
            )

            self.assertTrue(payload["ok"])
            self.assertTrue(payload["offline_ready"])
            self.assertFalse(payload["online_ready"])
            self.assertEqual(payload["checks"]["corpus"]["documents"], 1)
            self.assertEqual(payload["checks"]["retrieval"]["retrieved_count"], 1)
            self.assertEqual(payload["checks"]["retrieval"]["top_chunk_ids"], ["security:0000"])
            self.assertTrue(payload["checks"]["answer_audit"]["grounded"])
            self.assertEqual(payload["llm"]["provider"], "mimo")
            self.assertEqual(payload["llm_request_plan"]["auth_header"], "api-key")
            self.assertNotIn("replace-with-your-dedicated-api-key", str(payload))
            self.assertIn("Set LLM_API_KEY", payload["recommendations"][0])


if __name__ == "__main__":
    unittest.main()

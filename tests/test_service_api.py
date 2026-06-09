import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cn_graphrag_eval_opt.api import QueryRequest, QueryResponse
from cn_graphrag_eval_opt.models import PipelineConfig
from cn_graphrag_eval_opt.service import QueryService


class QueryApiTest(unittest.TestCase):
    def test_query_request_defaults_to_mix_mode(self):
        request = QueryRequest(question="Who reviews access?")

        self.assertEqual(request.query_mode, "mix")
        self.assertEqual(request.top_k, 3)

    def test_query_service_returns_structured_response(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "security.md").write_text(
                "# Security\nSecurity team reviews privileged access monthly.",
                encoding="utf-8",
            )
            service = QueryService.from_paths(
                root,
                PipelineConfig(chunk_size=120, overlap=0, top_k=1, query_mode="mix"),
            )

            response = service.query_response("Who reviews access?")

            self.assertIsInstance(response, QueryResponse)
            self.assertEqual(response.question, "Who reviews access?")
            self.assertEqual(response.trace.retrieved_count, 1)
            self.assertEqual(response.contexts[0].chunk_id, "security:0000")
            self.assertIn("Security team", response.answer)
            self.assertEqual(response.to_dict()["contexts"][0]["chunk_id"], "security:0000")

    def test_existing_query_method_still_returns_dict(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "finance.md").write_text(
                "# Finance\nFinance reviews invoice approvals.",
                encoding="utf-8",
            )
            service = QueryService.from_paths(
                root,
                PipelineConfig(chunk_size=120, overlap=0, top_k=1, query_mode="naive"),
            )

            response = service.query("Who reviews invoices?")

            self.assertIsInstance(response, dict)
            self.assertIn("contexts", response)
            self.assertEqual(response["trace"]["query_mode"], "naive")


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cn_graphrag_eval_opt.models import PipelineConfig
from cn_graphrag_eval_opt.service import QueryService


QUESTION = "\u54ea\u4e2a\u90e8\u95e8\u590d\u6838\u9ad8\u5371\u6743\u9650\uff1f"
ANSWER = "\u5b89\u5168\u90e8\u6bcf\u6708\u590d\u6838\u9ad8\u5371\u6743\u9650\u3002"
SECURITY_DOC = (
    "# \u5b89\u5168\u5236\u5ea6\n"
    "\u5b89\u5168\u90e8\u6bcf\u6708\u590d\u6838\u9ad8\u5371\u6743\u9650\u3002"
)


class ServiceLLMTest(unittest.TestCase):
    def _service(self, root: Path) -> QueryService:
        (root / "security.md").write_text(SECURITY_DOC, encoding="utf-8")
        return QueryService.from_paths(
            root,
            PipelineConfig(chunk_size=80, overlap=0, top_k=1, query_mode="mix"),
        )

    def test_query_service_can_use_injected_llm_answerer(self):
        with TemporaryDirectory() as tmp:
            service = self._service(Path(tmp))

            def answerer(question, contexts):
                self.assertEqual(question, QUESTION)
                self.assertEqual(contexts[0].chunk_id, "security:0000")
                return f"{ANSWER} citation: security:0000"

            response = service.query_response(
                QUESTION,
                answerer=answerer,
                answer_mode="mimo",
                llm_provider="mimo",
                llm_model="mimo-v2.5-pro",
            )

            self.assertEqual(response.answer, f"{ANSWER} citation: security:0000")
            self.assertEqual(response.trace.answer_mode, "mimo")
            self.assertEqual(response.trace.llm_provider, "mimo")
            self.assertEqual(response.trace.llm_model, "mimo-v2.5-pro")
            self.assertTrue(response.trace.grounded)
            self.assertEqual(response.trace.cited_chunk_ids, ["security:0000"])
            self.assertEqual(response.trace.missing_citation_ids, [])
            self.assertEqual(response.trace.citation_coverage, 1.0)

    def test_llm_answer_without_chunk_citation_is_flagged(self):
        with TemporaryDirectory() as tmp:
            service = self._service(Path(tmp))

            response = service.query_response(
                QUESTION,
                answerer=lambda question, contexts: ANSWER,
                answer_mode="mimo",
                llm_provider="mimo",
                llm_model="mimo-v2.5-pro",
            )

            self.assertFalse(response.trace.grounded)
            self.assertEqual(response.trace.cited_chunk_ids, [])
            self.assertEqual(response.trace.missing_citation_ids, [])
            self.assertIn("answer_missing_chunk_citation", response.trace.warnings)

    def test_llm_answer_with_unknown_chunk_citation_is_flagged(self):
        with TemporaryDirectory() as tmp:
            service = self._service(Path(tmp))

            response = service.query_response(
                QUESTION,
                answerer=lambda question, contexts: f"{ANSWER} citation: security:9999",
                answer_mode="mimo",
                llm_provider="mimo",
                llm_model="mimo-v2.5-pro",
            )

            self.assertFalse(response.trace.grounded)
            self.assertEqual(response.trace.cited_chunk_ids, [])
            self.assertEqual(response.trace.missing_citation_ids, ["security:9999"])
            self.assertEqual(response.trace.citation_coverage, 0.0)
            self.assertIn("answer_missing_chunk_citation", response.trace.warnings)
            self.assertIn("answer_has_unknown_chunk_citation", response.trace.warnings)


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cn_graphrag_eval_opt.models import PipelineConfig
from cn_graphrag_eval_opt.service import QueryService


class ServiceLLMTest(unittest.TestCase):
    def test_query_service_can_use_injected_llm_answerer(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "security.md").write_text(
                "# 安全制度\n安全部每月复核高危权限。",
                encoding="utf-8",
            )
            service = QueryService.from_paths(
                root,
                PipelineConfig(chunk_size=80, overlap=0, top_k=1, query_mode="mix"),
            )

            def answerer(question, contexts):
                self.assertEqual(question, "哪个部门复核高危权限？")
                self.assertEqual(contexts[0].chunk_id, "security:0000")
                return "安全部每月复核高危权限。"

            response = service.query_response(
                "哪个部门复核高危权限？",
                answerer=answerer,
                answer_mode="mimo",
                llm_provider="mimo",
                llm_model="mimo-v2.5-pro",
            )

            self.assertEqual(response.answer, "安全部每月复核高危权限。")
            self.assertEqual(response.trace.answer_mode, "mimo")
            self.assertEqual(response.trace.llm_provider, "mimo")
            self.assertEqual(response.trace.llm_model, "mimo-v2.5-pro")


if __name__ == "__main__":
    unittest.main()

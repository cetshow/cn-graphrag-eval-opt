import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cn_graphrag_eval_opt.config import load_project_config
from cn_graphrag_eval_opt.corpus import load_corpus, load_qa_jsonl
from cn_graphrag_eval_opt.datasets import build_synthetic_qa
from cn_graphrag_eval_opt.embeddings import HashingEmbeddingModel, cosine_similarity
from cn_graphrag_eval_opt.pipeline import GraphRAGPipeline
from cn_graphrag_eval_opt.service import QueryService
from cn_graphrag_eval_opt.storage import FileIndexStore


class ProjectUpgradeTest(unittest.TestCase):
    def test_default_config_loads_pipeline_grid(self):
        config = load_project_config(Path("configs/default.toml"))

        self.assertEqual(config.project.name, "cn-graphrag-eval-opt")
        self.assertGreaterEqual(len(config.optimization.configs), 5)
        self.assertIn("mix", {item.query_mode for item in config.optimization.configs})
        self.assertEqual(config.reporting.formats, ["json", "markdown", "csv"])

    def test_synthetic_dataset_builder_creates_jsonl_cases(self):
        documents = load_corpus(Path("examples/corpus"))

        cases = build_synthetic_qa(documents, cases_per_document=1)

        self.assertGreaterEqual(len(cases), 3)
        self.assertTrue(all(case.question for case in cases))
        self.assertTrue(all(case.required_terms for case in cases))
        self.assertTrue(any("source_doc_id" in case.metadata for case in cases))

    def test_pipeline_writes_graphrag_autorag_style_trial_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            trial_dir = Path(tmp) / "trial"
            config = load_project_config(Path("configs/default.toml"))
            config = config.with_paths(corpus_path=Path("examples/corpus"), qa_path=Path("examples/qa.jsonl"), out_dir=trial_dir)
            pipeline = GraphRAGPipeline(config)

            result = pipeline.run_optimization()

            self.assertEqual(result.best_summary.metrics["retrieval_recall"], 1.0)
            expected_paths = [
                trial_dir / "inputs" / "corpus_manifest.json",
                trial_dir / "index" / "chunks.jsonl",
                trial_dir / "index" / "entities.json",
                trial_dir / "evaluations" / "case_results.jsonl",
                trial_dir / "leaderboard.csv",
                trial_dir / "summary.json",
                trial_dir / "best_config.json",
                trial_dir / "reports" / "report.md",
            ]
            for path in expected_paths:
                self.assertTrue(path.exists(), f"missing artifact: {path}")

            leaderboard = (trial_dir / "leaderboard.csv").read_text(encoding="utf-8")
            self.assertIn("query_mode", leaderboard)
            self.assertIn(result.best_config.query_mode, leaderboard)

    def test_query_service_returns_context_trace(self):
        config = load_project_config(Path("configs/default.toml"))
        service = QueryService.from_paths(
            corpus_path=Path("examples/corpus"),
            config=config.optimization.configs[-1],
        )

        response = service.query("哪个部门每月复核高危权限？")

        self.assertIn("answer", response)
        self.assertIn("contexts", response)
        self.assertTrue(any("安全部" in item["text"] for item in response["contexts"]))
        self.assertGreater(response["trace"]["retrieved_count"], 0)

    def test_embedding_and_index_store_support_persistent_hybrid_retrieval(self):
        with tempfile.TemporaryDirectory() as tmp:
            documents = load_corpus(Path("examples/corpus"))
            config = load_project_config(Path("configs/default.toml")).optimization.configs[-1]
            service = QueryService.from_paths(Path("examples/corpus"), config)
            store = FileIndexStore(Path(tmp) / "index")

            store.save(service.index, service.chunks)
            loaded_index, loaded_chunks = store.load()

            self.assertEqual(len(loaded_chunks), len(service.chunks))
            self.assertIn("security_access:0000", loaded_index.chunks)

            model = HashingEmbeddingModel(dimensions=64)
            security_vector = model.embed("安全部复核高危权限")
            finance_vector = model.embed("财务部审核发票")
            self.assertGreater(cosine_similarity(security_vector, security_vector), 0.99)
            self.assertLess(cosine_similarity(security_vector, finance_vector), 0.95)


if __name__ == "__main__":
    unittest.main()

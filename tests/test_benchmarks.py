import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cn_graphrag_eval_opt.corpus import load_corpus, load_qa_jsonl
from cn_graphrag_eval_opt.optimization import run_optimization


class BenchmarkDatasetTest(unittest.TestCase):
    def test_small_and_medium_enterprise_benchmarks_are_reproducible(self):
        cases = [
            {
                "name": "small_enterprise",
                "documents": 5,
                "qa_cases": 8,
                "best_mode": "naive",
                "precision": 0.6875,
                "token_cost": 45.8575,
            },
            {
                "name": "medium_enterprise",
                "documents": 10,
                "qa_cases": 15,
                "best_mode": "naive",
                "precision": 0.8333,
                "token_cost": 44.1240,
            },
        ]

        for case in cases:
            with self.subTest(case["name"]):
                root = Path("examples/benchmarks") / case["name"]
                documents = load_corpus(root / "corpus")
                qa_cases = load_qa_jsonl(root / "qa.jsonl")
                result = run_optimization(documents, qa_cases)

                self.assertEqual(len(documents), case["documents"])
                self.assertEqual(len(qa_cases), case["qa_cases"])
                self.assertEqual(result.best_config.query_mode, case["best_mode"])
                self.assertEqual(result.best_summary.case_count, case["qa_cases"])
                self.assertEqual(result.best_summary.metrics["retrieval_recall"], 1.0)
                self.assertAlmostEqual(
                    result.best_summary.metrics["context_precision"],
                    case["precision"],
                    places=4,
                )
                self.assertAlmostEqual(
                    result.best_summary.metrics["estimated_token_cost"],
                    case["token_cost"],
                    places=4,
                )


if __name__ == "__main__":
    unittest.main()

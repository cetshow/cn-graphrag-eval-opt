import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cn_graphrag_eval_opt.corpus import load_corpus, load_qa_jsonl
from cn_graphrag_eval_opt.optimization import run_optimization


class BenchmarkDatasetTest(unittest.TestCase):
    def test_enterprise_benchmarks_are_reproducible(self):
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
            {
                "name": "scale_enterprise",
                "documents": 12,
                "qa_cases": 12,
                "best_mode": "naive",
                "recall": 0.9722,
                "precision": 0.7917,
                "token_cost": 39.7642,
            },
            {
                "name": "multi_hop_enterprise",
                "documents": 6,
                "qa_cases": 6,
                "best_mode": "hybrid",
                "recall": 0.9444,
                "precision": 0.6667,
                "token_cost": 76.1467,
            },
            {
                "name": "noisy_enterprise",
                "documents": 6,
                "qa_cases": 4,
                "best_mode": "naive",
                "recall": 1.0,
                "precision": 1.0,
                "token_cost": 50.4700,
            },
            {
                "name": "vertical_industry",
                "documents": 4,
                "qa_cases": 4,
                "best_mode": "global",
                "recall": 1.0,
                "precision": 0.5417,
                "token_cost": 57.6575,
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
                self.assertAlmostEqual(
                    result.best_summary.metrics["retrieval_recall"],
                    case.get("recall", 1.0),
                    places=4,
                )
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

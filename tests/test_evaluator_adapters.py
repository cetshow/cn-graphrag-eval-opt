import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cn_graphrag_eval_opt.evaluator_adapters import (
    check_quality_gate,
    to_deepeval_cases,
    to_ragas_rows,
)
from cn_graphrag_eval_opt.models import CaseEvaluation, EvaluationResult


class EvaluatorAdapterTest(unittest.TestCase):
    def test_case_results_convert_to_ragas_rows(self):
        case = CaseEvaluation(
            question="Who reviews privileged access?",
            expected_answer="The security team.",
            generated_answer="The security team reviews privileged access monthly.",
            retrieved_chunk_ids=["c1"],
            metrics={"faithfulness": 1.0},
        )

        rows = to_ragas_rows([case], {"c1": "The security team reviews privileged access monthly."})

        self.assertEqual(rows[0]["question"], "Who reviews privileged access?")
        self.assertEqual(rows[0]["answer"], "The security team reviews privileged access monthly.")
        self.assertEqual(rows[0]["ground_truth"], "The security team.")
        self.assertEqual(rows[0]["contexts"], ["The security team reviews privileged access monthly."])

    def test_case_results_convert_to_deepeval_cases(self):
        case = CaseEvaluation(
            question="Who approves invoices?",
            expected_answer="Finance.",
            generated_answer="Finance approves invoices.",
            retrieved_chunk_ids=["c2"],
            metrics={"answer_relevance": 1.0},
        )

        cases = to_deepeval_cases([case], {"c2": "Finance approves invoices."})

        self.assertEqual(cases[0]["input"], "Who approves invoices?")
        self.assertEqual(cases[0]["actual_output"], "Finance approves invoices.")
        self.assertEqual(cases[0]["expected_output"], "Finance.")
        self.assertEqual(cases[0]["retrieval_context"], ["Finance approves invoices."])

    def test_quality_gate_reports_failed_thresholds(self):
        result = EvaluationResult(
            cases=[],
            aggregate={"retrieval_recall": 0.92, "faithfulness": 0.74},
        )

        gate = check_quality_gate(
            result,
            {"retrieval_recall": 0.9, "faithfulness": 0.8, "context_precision": 0.5},
        )

        self.assertFalse(gate.passed)
        self.assertEqual(gate.failed["faithfulness"].actual, 0.74)
        self.assertEqual(gate.failed["faithfulness"].required, 0.8)
        self.assertIsNone(gate.failed["context_precision"].actual)


if __name__ == "__main__":
    unittest.main()

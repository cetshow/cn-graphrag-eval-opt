import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cn_graphrag_eval_opt.cli import main


class QualityGateCliTest(unittest.TestCase):
    def test_quality_gate_passes_against_summary_metrics(self):
        with TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "best_summary": {
                            "metrics": {
                                "retrieval_recall": 0.94,
                                "faithfulness": 0.88,
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                main(
                    [
                        "quality-gate",
                        "--summary",
                        str(summary_path),
                        "--threshold",
                        "retrieval_recall=0.90",
                        "--threshold",
                        "faithfulness=0.80",
                    ]
                )

            payload = json.loads(output.getvalue())
            self.assertTrue(payload["passed"])
            self.assertEqual(payload["checked"]["retrieval_recall"], 0.94)
            self.assertEqual(payload["failed"], {})

    def test_quality_gate_exits_nonzero_when_threshold_fails(self):
        with TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "best_summary": {
                            "metrics": {
                                "retrieval_recall": 0.71,
                                "faithfulness": 0.82,
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                with self.assertRaises(SystemExit) as raised:
                    main(
                        [
                            "quality-gate",
                            "--summary",
                            str(summary_path),
                            "--threshold",
                            "retrieval_recall=0.90",
                        ]
                    )

            payload = json.loads(output.getvalue())
            self.assertEqual(raised.exception.code, 1)
            self.assertFalse(payload["passed"])
            self.assertEqual(payload["failed"]["retrieval_recall"]["actual"], 0.71)
            self.assertEqual(payload["failed"]["retrieval_recall"]["required"], 0.90)


if __name__ == "__main__":
    unittest.main()

import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cn_graphrag_eval_opt.cli import main


class LLMCliTest(unittest.TestCase):
    def test_llm_smoke_dry_run_prints_safe_request_plan(self):
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            main(["llm-smoke", "--env", ".env.example", "--dry-run"])

        payload = json.loads(output.getvalue())
        self.assertEqual(payload["endpoint"], "https://token-plan-cn.xiaomimimo.com/v1/chat/completions")
        self.assertEqual(payload["model"], "mimo-v2.5-pro")
        self.assertEqual(payload["auth_header"], "api-key")
        self.assertNotIn("replace-with-your-dedicated-api-key", str(payload))

    def test_ask_offline_returns_traced_product_response(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "security.md").write_text(
                "# 安全制度\n安全部每月复核高危权限。",
                encoding="utf-8",
            )
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                main(
                    [
                        "ask",
                        "哪个部门复核高危权限？",
                        "--corpus",
                        str(root),
                        "--offline",
                        "--top-k",
                        "1",
                    ]
                )

            payload = json.loads(output.getvalue())
            self.assertEqual(payload["trace"]["answer_mode"], "extractive")
            self.assertEqual(payload["trace"]["retrieved_count"], 1)
            self.assertIn("安全部", payload["answer"])

    def test_ask_online_with_placeholder_key_returns_product_error(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "security.md").write_text(
                "# 安全制度\n安全部每月复核高危权限。",
                encoding="utf-8",
            )
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                with self.assertRaises(SystemExit) as raised:
                    main(
                        [
                            "ask",
                            "哪个部门复核高危权限？",
                            "--corpus",
                            str(root),
                            "--env",
                            ".env.example",
                            "--top-k",
                            "1",
                        ]
                    )

            payload = json.loads(output.getvalue())
            self.assertEqual(raised.exception.code, 2)
            self.assertFalse(payload["ok"])
            self.assertIn("LLM_API_KEY", payload["error"])


if __name__ == "__main__":
    unittest.main()

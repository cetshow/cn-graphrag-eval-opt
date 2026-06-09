import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cn_graphrag_eval_opt.cli import _json_text


class CliOutputTest(unittest.TestCase):
    def test_json_text_falls_back_to_ascii_for_gbk_console(self):
        payload = {
            "ok": True,
            "content": "\u4e2d\u6587 response \U0001f60a",
        }

        text = _json_text(payload, indent=2, output_encoding="gbk")

        self.assertNotIn("\U0001f60a", text)
        self.assertEqual(json.loads(text), payload)
        text.encode("gbk")


if __name__ == "__main__":
    unittest.main()

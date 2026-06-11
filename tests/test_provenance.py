import contextlib
import io
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cn_graphrag_eval_opt.cli import main
from cn_graphrag_eval_opt.provenance import provenance_policy


class ProvenancePolicyTest(unittest.TestCase):
    def test_policy_lists_reference_projects_and_license_boundaries(self):
        policy = provenance_policy()
        references = {item["name"]: item for item in policy["references"]}

        for project in ("LightRAG", "AutoRAG", "RAGFlow", "R2R"):
            self.assertIn(project, references)
            self.assertIn("license", references[project])
            self.assertIn("url", references[project])

        self.assertEqual(references["LightRAG"]["license"], "MIT License")
        self.assertEqual(references["AutoRAG"]["license"], "Apache License 2.0")
        self.assertEqual(references["RAGFlow"]["license"], "Apache License 2.0")
        self.assertEqual(references["R2R"]["license"], "MIT License")
        self.assertIn("does not vendor", policy["current_source_policy"])
        self.assertIn("copied, modified, or derived", " ".join(policy["reuse_requirements"]))

    def test_provenance_cli_outputs_json(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            main(["provenance"])

        payload = json.loads(output.getvalue())
        names = {item["name"] for item in payload["references"]}

        self.assertEqual(payload["project_license"], "MIT License")
        self.assertIn("RAGFlow", names)
        self.assertIn("does not vendor", payload["current_source_policy"])


if __name__ == "__main__":
    unittest.main()

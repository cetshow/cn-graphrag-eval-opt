import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class DocumentationQualityTest(unittest.TestCase):
    def test_readme_uses_portable_paths(self):
        readme = Path("README.md").read_text(encoding="utf-8")

        self.assertIsNone(re.search(r"[A-Za-z]:\\", readme))
        self.assertNotIn("/Users/", readme)
        self.assertNotIn("/home/", readme)

    def test_readme_is_product_documentation_not_resume_copy(self):
        readme = Path("README.md").read_text(encoding="utf-8")

        self.assertIn("Environment Requirements", readme)
        self.assertIn("MiMo", readme)
        self.assertIn("回答审计", readme)
        self.assertIn("Answer Audit", readme)
        self.assertIn("doctor", readme)
        self.assertNotIn("Resume Framing", readme)
        self.assertNotIn("简历", readme)
        self.assertNotIn("docs/resume-framing.md", readme)

    def test_ci_runs_tests_and_default_optimization(self):
        workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

        self.assertIn("python -m unittest discover -s tests", workflow)
        self.assertIn("python -m cn_graphrag_eval_opt optimize --config configs/default.toml", workflow)
        self.assertIn("python -m cn_graphrag_eval_opt quality-gate", workflow)

    def test_resume_framing_doc_covers_interview_talking_points(self):
        doc = Path("docs/resume-framing.md").read_text(encoding="utf-8")

        for heading in ("Problem", "Architecture", "Metrics", "Impact", "Interview Pitch"):
            self.assertIn(f"## {heading}", doc)
        self.assertIn("GraphRAG", doc)
        self.assertIn("Chinese enterprise", doc)

    def test_upstream_license_boundary_is_documented(self):
        readme = Path("README.md").read_text(encoding="utf-8")
        notice = Path("NOTICE.md").read_text(encoding="utf-8")
        references = Path("docs/references.md").read_text(encoding="utf-8")
        combined = "\n".join([readme, notice, references])

        for project in ("LightRAG", "AutoRAG", "RAGFlow", "R2R"):
            self.assertIn(project, combined)
        for license_name in ("MIT License", "Apache License 2.0"):
            self.assertIn(license_name, combined)

        self.assertIn("does not vendor", notice)
        self.assertIn("copied, modified, or derived", notice)
        self.assertIn("Reuse Boundary", references)
        self.assertIn("provenance", readme)

    def test_dataset_experiment_numbers_define_baseline(self):
        readme = Path("README.md").read_text(encoding="utf-8")
        experiments = Path("docs/experiments.md").read_text(encoding="utf-8")
        combined = "\n".join([readme, experiments])

        for value in ("retrieval_recall", "context_precision", "faithfulness", "estimated_token_cost"):
            self.assertIn(value, combined)
        for value in ("0.6667", "1.0000", "30.5167", "39.2733", "22.3%"):
            self.assertIn(value, combined)
        for value in ("small enterprise benchmark", "medium enterprise benchmark", "39.8%", "48.4%"):
            self.assertIn(value, combined)
        for value in (
            "Scale-up",
            "Cross-document multi-hop",
            "Noisy retrieval",
            "Top-K",
            "MiMo LLM Answer Audit",
            "Chunking Strategy",
            "Vertical-Industry",
            "49.6%",
            "44.3%",
            "20.1%",
            "65.7%",
            "33.3%",
            "23.6%",
            "12.7%",
        ):
            self.assertIn(value, combined)

        self.assertIn("query_mode=naive", combined)
        self.assertIn("chunk_size=96", combined)
        self.assertIn("overlap=12", combined)
        self.assertIn("top_k=2", combined)
        self.assertIn("lexical + hashing dense", combined)
        self.assertIn("without entity-graph expansion", combined)


if __name__ == "__main__":
    unittest.main()

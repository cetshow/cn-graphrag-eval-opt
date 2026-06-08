import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cn_graphrag_eval_opt.chunking import ChineseTextSplitter
from cn_graphrag_eval_opt.corpus import load_corpus, load_qa_jsonl
from cn_graphrag_eval_opt.evaluation import evaluate_cases
from cn_graphrag_eval_opt.graph import GraphIndex
from cn_graphrag_eval_opt.models import PipelineConfig
from cn_graphrag_eval_opt.optimization import run_optimization
from cn_graphrag_eval_opt.reporting import write_markdown_report
from cn_graphrag_eval_opt.retrieval import GraphRAGRetriever


class PipelineTest(unittest.TestCase):
    def test_corpus_loader_and_graph_retriever_find_enterprise_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "security.md").write_text(
                "# 权限管理\n研发部需要通过 IAM 系统申请生产权限。安全部每月复核高危权限。",
                encoding="utf-8",
            )
            documents = load_corpus(root)
            chunks = ChineseTextSplitter(chunk_size=36, overlap=6).split_many(documents)
            index = GraphIndex.from_chunks(chunks)
            retriever = GraphRAGRetriever(index)

            results = retriever.retrieve("谁复核高危权限？", top_k=2, mode="mix")

            self.assertEqual(documents[0].title, "权限管理")
            self.assertTrue(any("安全部" in result.chunk.text for result in results))
            self.assertTrue(index.entities)

    def test_evaluation_and_optimization_rank_pipeline_configs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus_dir = root / "corpus"
            corpus_dir.mkdir()
            (corpus_dir / "hr.md").write_text(
                "# 入职流程\n候选人签署劳动合同后，人力资源部会在两个工作日内开通账号。"
                "IT 服务台负责发放电脑并登记资产编号。",
                encoding="utf-8",
            )
            qa_path = root / "qa.jsonl"
            qa_path.write_text(
                json.dumps(
                    {
                        "question": "谁负责发放电脑？",
                        "answer": "IT 服务台负责发放电脑。",
                        "required_terms": ["IT 服务台", "发放电脑"],
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            documents = load_corpus(corpus_dir)
            qa_cases = load_qa_jsonl(qa_path)
            trial = run_optimization(
                documents,
                qa_cases,
                configs=[
                    PipelineConfig(chunk_size=16, overlap=2, top_k=1, query_mode="naive"),
                    PipelineConfig(chunk_size=64, overlap=8, top_k=2, query_mode="mix"),
                ],
            )

            self.assertEqual(trial.best_config.query_mode, "mix")
            self.assertGreaterEqual(trial.best_summary.metrics["retrieval_recall"], 0.99)
            report_path = write_markdown_report(trial, root / "report.md")
            self.assertIn("Best Configuration", report_path.read_text(encoding="utf-8"))

            splitter = ChineseTextSplitter(chunk_size=48, overlap=6)
            chunks = splitter.split_many(documents)
            retriever = GraphRAGRetriever(GraphIndex.from_chunks(chunks))
            metrics = evaluate_cases(qa_cases, retriever, PipelineConfig(query_mode="mix"))
            self.assertGreater(metrics.aggregate["faithfulness"], 0)


if __name__ == "__main__":
    unittest.main()

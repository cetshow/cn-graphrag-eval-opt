from __future__ import annotations

from dataclasses import dataclass

from cn_graphrag_eval_opt.chunking import ChineseTextSplitter
from cn_graphrag_eval_opt.config import ProjectConfig
from cn_graphrag_eval_opt.corpus import load_corpus, load_qa_jsonl
from cn_graphrag_eval_opt.evaluation import evaluate_cases
from cn_graphrag_eval_opt.graph import GraphIndex
from cn_graphrag_eval_opt.models import EvaluationResult, OptimizationResult, PipelineConfig
from cn_graphrag_eval_opt.optimization import run_optimization
from cn_graphrag_eval_opt.reporting import write_trial_artifacts
from cn_graphrag_eval_opt.retrieval import GraphRAGRetriever


@dataclass
class GraphRAGPipeline:
    config: ProjectConfig

    def run_optimization(self) -> OptimizationResult:
        documents = load_corpus(self.config.corpus.corpus_path)
        qa_cases = load_qa_jsonl(self.config.corpus.qa_path)
        result = run_optimization(documents, qa_cases, self.config.optimization.configs)
        best_evaluation, chunks, index = self.evaluate_config(result.best_config)
        write_trial_artifacts(
            result=result,
            documents=documents,
            chunks=chunks,
            index=index,
            evaluation=best_evaluation,
            out_dir=self.config.corpus.out_dir,
        )
        return result

    def evaluate_config(
        self,
        pipeline_config: PipelineConfig,
    ) -> tuple[EvaluationResult, list, GraphIndex]:
        documents = load_corpus(self.config.corpus.corpus_path)
        qa_cases = load_qa_jsonl(self.config.corpus.qa_path)
        splitter = ChineseTextSplitter(
            chunk_size=pipeline_config.chunk_size,
            overlap=pipeline_config.overlap,
            strategy=pipeline_config.chunk_strategy,
        )
        chunks = splitter.split_many(documents)
        index = GraphIndex.from_chunks(chunks)
        evaluation = evaluate_cases(qa_cases, GraphRAGRetriever(index), pipeline_config)
        return evaluation, chunks, index

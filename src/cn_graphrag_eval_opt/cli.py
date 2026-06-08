from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from cn_graphrag_eval_opt.adapters import optional_integrations
from cn_graphrag_eval_opt.chunking import ChineseTextSplitter
from cn_graphrag_eval_opt.config import DEFAULT_CONFIG_TEXT, load_project_config
from cn_graphrag_eval_opt.corpus import load_corpus, load_qa_jsonl
from cn_graphrag_eval_opt.datasets import build_synthetic_qa, write_qa_jsonl
from cn_graphrag_eval_opt.evaluation import evaluate_cases
from cn_graphrag_eval_opt.graph import GraphIndex
from cn_graphrag_eval_opt.models import PipelineConfig
from cn_graphrag_eval_opt.optimization import run_optimization
from cn_graphrag_eval_opt.pipeline import GraphRAGPipeline
from cn_graphrag_eval_opt.reporting import write_json_artifacts, write_markdown_report
from cn_graphrag_eval_opt.retrieval import GraphRAGRetriever
from cn_graphrag_eval_opt.service import QueryService


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="cn-graphrag-eval",
        description="Chinese enterprise GraphRAG evaluation and optimization toolkit.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create a starter project config.")
    init.add_argument("--out", default="graphrag.toml")

    ingest = subparsers.add_parser("ingest", help="Load and chunk a corpus.")
    ingest.add_argument("--corpus", required=True)
    ingest.add_argument("--chunk-size", type=int, default=128)
    ingest.add_argument("--overlap", type=int, default=16)

    evaluate = subparsers.add_parser("evaluate", help="Evaluate one pipeline config.")
    evaluate.add_argument("--corpus", required=True)
    evaluate.add_argument("--qa", required=True)
    evaluate.add_argument("--out", required=True)
    evaluate.add_argument("--query-mode", default="mix")
    evaluate.add_argument("--chunk-size", type=int, default=128)
    evaluate.add_argument("--overlap", type=int, default=16)
    evaluate.add_argument("--top-k", type=int, default=3)

    dataset = subparsers.add_parser("dataset", help="Build bootstrap QA data.")
    dataset.add_argument("action", choices=["build"])
    dataset.add_argument("--corpus", required=True)
    dataset.add_argument("--out", required=True)
    dataset.add_argument("--cases-per-document", type=int, default=1)

    optimize = subparsers.add_parser("optimize", help="Search multiple RAG configs.")
    optimize.add_argument("--config", default=None)
    optimize.add_argument("--corpus", default=None)
    optimize.add_argument("--qa", default=None)
    optimize.add_argument("--out", default=None)

    query = subparsers.add_parser("query", help="Run a traced retrieval query.")
    query.add_argument("question")
    query.add_argument("--corpus", required=True)
    query.add_argument("--query-mode", default="mix")
    query.add_argument("--chunk-size", type=int, default=128)
    query.add_argument("--overlap", type=int, default=16)
    query.add_argument("--top-k", type=int, default=3)

    integrations = subparsers.add_parser("integrations", help="Show optional upstream adapters.")

    args = parser.parse_args(argv)
    if args.command == "init":
        _cmd_init(args)
    elif args.command == "ingest":
        _cmd_ingest(args)
    elif args.command == "evaluate":
        _cmd_evaluate(args)
    elif args.command == "dataset":
        _cmd_dataset(args)
    elif args.command == "optimize":
        _cmd_optimize(args)
    elif args.command == "query":
        _cmd_query(args)
    elif args.command == "integrations":
        _cmd_integrations()


def _cmd_init(args: argparse.Namespace) -> None:
    output = Path(args.out)
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing config: {output}")
    output.write_text(DEFAULT_CONFIG_TEXT, encoding="utf-8")
    print(json.dumps({"config": str(output)}, ensure_ascii=False))


def _cmd_ingest(args: argparse.Namespace) -> None:
    documents = load_corpus(args.corpus)
    chunks = ChineseTextSplitter(args.chunk_size, args.overlap).split_many(documents)
    print(json.dumps({"documents": len(documents), "chunks": len(chunks)}, ensure_ascii=False))


def _cmd_evaluate(args: argparse.Namespace) -> None:
    documents = load_corpus(args.corpus)
    qa_cases = load_qa_jsonl(args.qa)
    config = PipelineConfig(
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        top_k=args.top_k,
        query_mode=args.query_mode,
    )
    chunks = ChineseTextSplitter(config.chunk_size, config.overlap).split_many(documents)
    result = evaluate_cases(qa_cases, GraphRAGRetriever(GraphIndex.from_chunks(chunks)), config)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "evaluation.json").write_text(
        json.dumps(asdict(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(result.aggregate, ensure_ascii=False))


def _cmd_dataset(args: argparse.Namespace) -> None:
    documents = load_corpus(args.corpus)
    cases = build_synthetic_qa(documents, cases_per_document=args.cases_per_document)
    output = write_qa_jsonl(cases, args.out)
    print(json.dumps({"qa_cases": len(cases), "path": str(output)}, ensure_ascii=False))


def _cmd_optimize(args: argparse.Namespace) -> None:
    if args.config:
        config = load_project_config(args.config)
        if args.corpus or args.qa or args.out:
            config = config.with_paths(
                corpus_path=Path(args.corpus) if args.corpus else None,
                qa_path=Path(args.qa) if args.qa else None,
                out_dir=Path(args.out) if args.out else None,
            )
        result = GraphRAGPipeline(config).run_optimization()
        print(
            json.dumps(
                {"best_config": asdict(result.best_config), "out_dir": str(config.corpus.out_dir)},
                ensure_ascii=False,
            )
        )
        return

    if not args.corpus or not args.qa or not args.out:
        raise ValueError("--corpus, --qa, and --out are required when --config is not supplied")
    documents = load_corpus(args.corpus)
    qa_cases = load_qa_jsonl(args.qa)
    result = run_optimization(documents, qa_cases)
    out_dir = Path(args.out)
    write_json_artifacts(result, out_dir)
    report_path = write_markdown_report(result, out_dir / "report.md")
    print(
        json.dumps(
            {"best_config": asdict(result.best_config), "report": str(report_path)},
            ensure_ascii=False,
        )
    )


def _cmd_query(args: argparse.Namespace) -> None:
    config = PipelineConfig(
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        top_k=args.top_k,
        query_mode=args.query_mode,
    )
    response = QueryService.from_paths(args.corpus, config).query(args.question)
    print(json.dumps(response, ensure_ascii=False, indent=2))


def _cmd_integrations() -> None:
    payload = [asdict(status) for status in optional_integrations()]
    print(json.dumps(payload, ensure_ascii=False, indent=2))

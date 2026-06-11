from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from cn_graphrag_eval_opt.adapters import optional_integrations
from cn_graphrag_eval_opt.chunking import ChineseTextSplitter
from cn_graphrag_eval_opt.config import DEFAULT_CONFIG_TEXT, load_project_config
from cn_graphrag_eval_opt.corpus import load_corpus, load_qa_jsonl
from cn_graphrag_eval_opt.datasets import build_synthetic_qa, write_qa_jsonl
from cn_graphrag_eval_opt.diagnostics import run_product_doctor
from cn_graphrag_eval_opt.evaluation import evaluate_cases
from cn_graphrag_eval_opt.evaluator_adapters import check_quality_gate
from cn_graphrag_eval_opt.graph import GraphIndex
from cn_graphrag_eval_opt.incremental import IncrementalIndexUpdater
from cn_graphrag_eval_opt.llm import (
    LLMError,
    OpenAICompatibleChatClient,
    build_llm_request_plan,
    generate_grounded_answer,
    load_llm_config,
)
from cn_graphrag_eval_opt.models import EvaluationResult, PipelineConfig
from cn_graphrag_eval_opt.optimization import run_optimization
from cn_graphrag_eval_opt.pipeline import GraphRAGPipeline
from cn_graphrag_eval_opt.provenance import provenance_policy
from cn_graphrag_eval_opt.reporting import write_json_artifacts, write_markdown_report
from cn_graphrag_eval_opt.retrieval import GraphRAGRetriever
from cn_graphrag_eval_opt.service import QueryService
from cn_graphrag_eval_opt.stores import JsonlIndexStore


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
    ingest.add_argument("--out", default=None, help="Optional directory for persisted index files.")
    ingest.add_argument("--incremental", action="store_true", help="Reuse an existing index ledger when --out exists.")
    ingest.add_argument("--delete-doc-id", action="append", default=[], help="Logical document id to remove from the persisted index.")

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

    ask = subparsers.add_parser("ask", help="Run retrieval and answer with MiMo LLM or offline mode.")
    ask.add_argument("question")
    ask.add_argument("--corpus", required=True)
    ask.add_argument("--env", default=".env")
    ask.add_argument("--offline", action="store_true", help="Use deterministic extractive answer mode.")
    ask.add_argument("--query-mode", default="mix")
    ask.add_argument("--chunk-size", type=int, default=128)
    ask.add_argument("--overlap", type=int, default=16)
    ask.add_argument("--top-k", type=int, default=3)

    doctor = subparsers.add_parser("doctor", help="Run non-network product readiness diagnostics.")
    doctor.add_argument("--corpus", required=True)
    doctor.add_argument("--env", default=".env")
    doctor.add_argument("--question", default="哪个部门每月复核高危权限？")
    doctor.add_argument("--query-mode", default="mix")
    doctor.add_argument("--chunk-size", type=int, default=128)
    doctor.add_argument("--overlap", type=int, default=16)
    doctor.add_argument("--top-k", type=int, default=3)

    integrations = subparsers.add_parser("integrations", help="Show optional upstream adapters.")

    subparsers.add_parser("provenance", help="Show upstream reference and license boundary metadata.")

    llm_config = subparsers.add_parser("llm-config", help="Show redacted LLM environment config.")
    llm_config.add_argument("--env", default=".env")

    llm_smoke = subparsers.add_parser("llm-smoke", help="Verify MiMo LLM connectivity.")
    llm_smoke.add_argument("--env", default=".env")
    llm_smoke.add_argument("--prompt", default="请用一句话介绍 MiMo。")
    llm_smoke.add_argument("--dry-run", action="store_true")

    quality_gate = subparsers.add_parser(
        "quality-gate",
        help="Fail CI when evaluation summary metrics miss required thresholds.",
    )
    quality_gate.add_argument("--summary", required=True)
    quality_gate.add_argument(
        "--threshold",
        action="append",
        required=True,
        help="Metric threshold in metric=min_score form, e.g. retrieval_recall=0.90.",
    )

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
    elif args.command == "ask":
        _cmd_ask(args)
    elif args.command == "doctor":
        _cmd_doctor(args)
    elif args.command == "integrations":
        _cmd_integrations()
    elif args.command == "provenance":
        _cmd_provenance()
    elif args.command == "llm-config":
        _cmd_llm_config(args)
    elif args.command == "llm-smoke":
        _cmd_llm_smoke(args)
    elif args.command == "quality-gate":
        _cmd_quality_gate(args)


def _cmd_init(args: argparse.Namespace) -> None:
    output = Path(args.out)
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing config: {output}")
    output.write_text(DEFAULT_CONFIG_TEXT, encoding="utf-8")
    _print_json({"config": str(output)})


def _cmd_ingest(args: argparse.Namespace) -> None:
    documents = load_corpus(args.corpus)
    splitter = ChineseTextSplitter(args.chunk_size, args.overlap)
    if not args.out:
        chunks = splitter.split_many(documents)
        _print_json({"documents": len(documents), "chunks": len(chunks)})
        return

    store = JsonlIndexStore(args.out)
    updater = IncrementalIndexUpdater(splitter)
    if args.incremental:
        try:
            result = updater.apply(
                store.load(),
                store.load_ledger(),
                changed_documents=documents,
                deleted_doc_ids=args.delete_doc_id,
            )
        except FileNotFoundError:
            result = updater.build(documents)
    else:
        result = updater.build(documents)

    metadata = store.save(result.index)
    ledger_path = store.save_ledger(result.ledger)
    _print_json(
        {
            "documents": len(result.ledger.documents),
            "chunks": metadata.chunk_count,
            "changed_doc_ids": result.changed_doc_ids,
            "deleted_doc_ids": result.deleted_doc_ids,
            "skipped_doc_ids": result.skipped_doc_ids,
            "index_dir": str(store.root),
            "ledger": str(ledger_path),
        }
    )


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
    _print_json(result.aggregate)


def _cmd_dataset(args: argparse.Namespace) -> None:
    documents = load_corpus(args.corpus)
    cases = build_synthetic_qa(documents, cases_per_document=args.cases_per_document)
    output = write_qa_jsonl(cases, args.out)
    _print_json({"qa_cases": len(cases), "path": str(output)})


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
        _print_json({"best_config": asdict(result.best_config), "out_dir": str(config.corpus.out_dir)})
        return

    if not args.corpus or not args.qa or not args.out:
        raise ValueError("--corpus, --qa, and --out are required when --config is not supplied")
    documents = load_corpus(args.corpus)
    qa_cases = load_qa_jsonl(args.qa)
    result = run_optimization(documents, qa_cases)
    out_dir = Path(args.out)
    write_json_artifacts(result, out_dir)
    report_path = write_markdown_report(result, out_dir / "report.md")
    _print_json({"best_config": asdict(result.best_config), "report": str(report_path)})


def _cmd_query(args: argparse.Namespace) -> None:
    config = PipelineConfig(
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        top_k=args.top_k,
        query_mode=args.query_mode,
    )
    response = QueryService.from_paths(args.corpus, config).query(args.question)
    _print_json(response, indent=2)


def _cmd_ask(args: argparse.Namespace) -> None:
    config = PipelineConfig(
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        top_k=args.top_k,
        query_mode=args.query_mode,
    )
    service = QueryService.from_paths(args.corpus, config)
    if args.offline:
        response = service.query_response(args.question, answer_mode="extractive")
        _print_json(response.to_dict(), indent=2)
        return

    try:
        llm_config = load_llm_config(args.env)
        client = OpenAICompatibleChatClient(llm_config)

        def answerer(question, contexts):
            return generate_grounded_answer(client=client, question=question, contexts=contexts).content

        response = service.query_response(
            args.question,
            answerer=answerer,
            answer_mode="llm",
            llm_provider=llm_config.provider,
            llm_model=llm_config.model,
        )
    except LLMError as error:
        _print_json({"ok": False, "error": str(error)}, indent=2)
        raise SystemExit(2) from error
    _print_json(response.to_dict(), indent=2)


def _cmd_doctor(args: argparse.Namespace) -> None:
    config = PipelineConfig(
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        top_k=args.top_k,
        query_mode=args.query_mode,
    )
    payload = run_product_doctor(
        corpus_path=args.corpus,
        env_path=args.env,
        question=args.question,
        config=config,
    )
    _print_json(payload, indent=2)


def _cmd_integrations() -> None:
    payload = [asdict(status) for status in optional_integrations()]
    _print_json(payload, indent=2)


def _cmd_provenance() -> None:
    _print_json(provenance_policy(), indent=2)


def _cmd_llm_config(args: argparse.Namespace) -> None:
    config = load_llm_config(args.env)
    _print_json(config.to_safe_dict(), indent=2)


def _cmd_llm_smoke(args: argparse.Namespace) -> None:
    config = load_llm_config(args.env)
    if args.dry_run:
        _print_json(build_llm_request_plan(config, args.prompt), indent=2)
        return
    try:
        response = OpenAICompatibleChatClient(config).chat(
            [{"role": "user", "content": args.prompt}]
        )
    except LLMError as error:
        _print_json({"ok": False, "error": str(error)}, indent=2)
        raise SystemExit(2) from error
    _print_json(
        {
            "ok": True,
            "model": response.model,
            "finish_reason": response.finish_reason,
            "usage": response.usage,
            "content": response.content,
        },
        indent=2,
    )


def _cmd_quality_gate(args: argparse.Namespace) -> None:
    metrics = _load_summary_metrics(args.summary)
    thresholds = _parse_thresholds(args.threshold)
    gate = check_quality_gate(EvaluationResult(cases=[], aggregate=metrics), thresholds)
    _print_json(asdict(gate), indent=2)
    if not gate.passed:
        raise SystemExit(1)


def _load_summary_metrics(path: str | Path) -> dict[str, float]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload.get("aggregate"), dict):
        return _numeric_metrics(payload["aggregate"])
    best_summary = payload.get("best_summary")
    if isinstance(best_summary, dict) and isinstance(best_summary.get("metrics"), dict):
        return _numeric_metrics(best_summary["metrics"])
    raise ValueError("Summary must contain aggregate metrics or best_summary.metrics")


def _numeric_metrics(metrics: dict[str, object]) -> dict[str, float]:
    numeric: dict[str, float] = {}
    for key, value in metrics.items():
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            numeric[key] = float(value)
    return numeric


def _parse_thresholds(items: list[str]) -> dict[str, float]:
    thresholds: dict[str, float] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Invalid threshold {item!r}: expected metric=min_score")
        metric, raw_value = item.split("=", 1)
        metric = metric.strip()
        if not metric:
            raise ValueError(f"Invalid threshold {item!r}: metric name is empty")
        thresholds[metric] = float(raw_value.strip())
    return thresholds


def _print_json(payload: object, *, indent: int | None = None) -> None:
    print(_json_text(payload, indent=indent, output_encoding=getattr(sys.stdout, "encoding", None)))


def _json_text(
    payload: object,
    *,
    indent: int | None = None,
    output_encoding: str | None = None,
) -> str:
    text = json.dumps(payload, ensure_ascii=False, indent=indent)
    if not output_encoding:
        return text
    try:
        text.encode(output_encoding)
        return text
    except UnicodeEncodeError:
        return json.dumps(payload, ensure_ascii=True, indent=indent)

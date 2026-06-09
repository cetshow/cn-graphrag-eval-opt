from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from cn_graphrag_eval_opt.graph import GraphIndex
from cn_graphrag_eval_opt.models import Chunk, Document, EvaluationResult, OptimizationResult
from cn_graphrag_eval_opt.storage import FileIndexStore


def write_json_artifacts(result: OptimizationResult, out_dir: str | Path) -> tuple[Path, Path]:
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    summary_path = output / "summary.json"
    best_config_path = output / "best_config.json"
    summary_path.write_text(
        json.dumps(asdict(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    best_config_path.write_text(
        json.dumps(asdict(result.best_config), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary_path, best_config_path


def write_markdown_report(result: OptimizationResult, path: str | Path) -> Path:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# cn-graphrag-eval-opt Report",
        "",
        "## Best Configuration",
        "",
        f"- Query mode: `{result.best_config.query_mode}`",
        f"- Chunk size: `{result.best_config.chunk_size}`",
        f"- Overlap: `{result.best_config.overlap}`",
        f"- Top-K: `{result.best_config.top_k}`",
        "",
        "## Best Metrics",
        "",
    ]
    for key, value in result.best_summary.metrics.items():
        lines.append(f"- {key}: `{value}`")

    lines.extend(["", "## Trial Leaderboard", "", "| Config | Recall | Faithfulness | Relevance | Precision | Token Cost |", "|---|---:|---:|---:|---:|---:|"])
    for trial in sorted(
        result.trials,
        key=lambda item: (
            item.metrics.get("retrieval_recall", 0.0),
            item.metrics.get("faithfulness", 0.0),
            item.metrics.get("answer_relevance", 0.0),
        ),
        reverse=True,
    ):
        metrics = trial.metrics
        lines.append(
            "| "
            + " | ".join(
                [
                    trial.config.label,
                    str(metrics.get("retrieval_recall", 0.0)),
                    str(metrics.get("faithfulness", 0.0)),
                    str(metrics.get("answer_relevance", 0.0)),
                    str(metrics.get("context_precision", 0.0)),
                    str(metrics.get("estimated_token_cost", 0.0)),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Implementation Notes",
            "",
            "- LightRAG-style query modes compare lexical, local entity, global graph neighbor, hybrid, and mix retrieval.",
            "- AutoRAG-style search ranks multiple pipeline configurations on the same Chinese corpus and QA set.",
            "- Ragas-style proxy metrics and quality gates make the baseline reproducible without remote LLM calls.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def write_trial_artifacts(
    *,
    result: OptimizationResult,
    documents: list[Document],
    chunks: list[Chunk],
    index: GraphIndex,
    evaluation: EvaluationResult,
    out_dir: str | Path,
) -> dict[str, Path]:
    output = Path(out_dir)
    inputs_dir = output / "inputs"
    index_dir = output / "index"
    evaluations_dir = output / "evaluations"
    reports_dir = output / "reports"
    for directory in (inputs_dir, index_dir, evaluations_dir, reports_dir):
        directory.mkdir(parents=True, exist_ok=True)

    paths = {
        "corpus_manifest": inputs_dir / "corpus_manifest.json",
        "chunks": index_dir / "chunks.jsonl",
        "entities": index_dir / "entities.json",
        "case_results": evaluations_dir / "case_results.jsonl",
        "leaderboard": output / "leaderboard.csv",
        "summary": output / "summary.json",
        "best_config": output / "best_config.json",
        "report": reports_dir / "report.md",
    }

    paths["corpus_manifest"].write_text(
        json.dumps(
            [
                {
                    "doc_id": document.doc_id,
                    "title": document.title,
                    "source": document.source,
                    "chars": len(document.text),
                }
                for document in documents
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    paths["chunks"].write_text(
        "\n".join(json.dumps(asdict(chunk), ensure_ascii=False) for chunk in chunks) + "\n",
        encoding="utf-8",
    )
    paths["entities"].write_text(
        json.dumps(
            {
                "entities": {key: sorted(value) for key, value in index.entities.items()},
                "edges": {
                    left: dict(counter.most_common())
                    for left, counter in index.edges.items()
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    FileIndexStore(index_dir / "store").save(index, chunks)
    paths["case_results"].write_text(
        "\n".join(
            json.dumps(asdict(case_result), ensure_ascii=False)
            for case_result in evaluation.cases
        )
        + "\n",
        encoding="utf-8",
    )
    paths["leaderboard"].write_text(_leaderboard_csv(result), encoding="utf-8")
    write_json_artifacts(result, output)
    write_markdown_report(result, paths["report"])
    return paths


def _leaderboard_csv(result: OptimizationResult) -> str:
    columns = [
        "query_mode",
        "chunk_size",
        "overlap",
        "top_k",
        "retrieval_recall",
        "context_precision",
        "answer_relevance",
        "faithfulness",
        "estimated_token_cost",
    ]
    lines = [",".join(columns)]
    for trial in result.trials:
        row = [
            trial.config.query_mode,
            str(trial.config.chunk_size),
            str(trial.config.overlap),
            str(trial.config.top_k),
            str(trial.metrics.get("retrieval_recall", 0.0)),
            str(trial.metrics.get("context_precision", 0.0)),
            str(trial.metrics.get("answer_relevance", 0.0)),
            str(trial.metrics.get("faithfulness", 0.0)),
            str(trial.metrics.get("estimated_token_cost", 0.0)),
        ]
        lines.append(",".join(row))
    return "\n".join(lines) + "\n"

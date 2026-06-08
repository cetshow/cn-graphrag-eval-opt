from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from cn_graphrag_eval_opt.models import OptimizationResult


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
            "## Resume Notes",
            "",
            "- LightRAG-style query modes compare lexical, local entity, global graph neighbor, hybrid, and mix retrieval.",
            "- AutoRAG-style search ranks multiple pipeline configurations on the same Chinese corpus and QA set.",
            "- Ragas-style proxy metrics make the baseline reproducible without remote LLM calls.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path

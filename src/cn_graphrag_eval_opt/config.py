from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from cn_graphrag_eval_opt.models import PipelineConfig

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib  # type: ignore[no-redef]

DEFAULT_CONFIG_TEXT = """[project]
name = "cn-graphrag-eval-opt"
version = "0.2.0"
description = "Chinese enterprise document GraphRAG retrieval evaluation and optimization toolkit."

[corpus]
corpus_path = "examples/corpus"
qa_path = "examples/qa.jsonl"
out_dir = "runs/demo"

[reporting]
formats = ["json", "markdown", "csv"]

[optimization]
rank_metrics = ["retrieval_recall", "faithfulness", "answer_relevance", "context_precision"]

[[optimization.configs]]
query_mode = "naive"
chunk_size = 96
overlap = 12
top_k = 2

[[optimization.configs]]
query_mode = "local"
chunk_size = 128
overlap = 16
top_k = 3

[[optimization.configs]]
query_mode = "global"
chunk_size = 128
overlap = 16
top_k = 3

[[optimization.configs]]
query_mode = "hybrid"
chunk_size = 160
overlap = 24
top_k = 3

[[optimization.configs]]
query_mode = "mix"
chunk_size = 192
overlap = 24
top_k = 4
"""


@dataclass(frozen=True)
class ProjectSection:
    name: str
    description: str
    version: str = "0.1.0"


@dataclass(frozen=True)
class CorpusSection:
    corpus_path: Path
    qa_path: Path
    out_dir: Path


@dataclass(frozen=True)
class ReportingSection:
    formats: list[str]


@dataclass(frozen=True)
class OptimizationSection:
    configs: list[PipelineConfig]
    rank_metrics: list[str]


@dataclass(frozen=True)
class ProjectConfig:
    project: ProjectSection
    corpus: CorpusSection
    optimization: OptimizationSection
    reporting: ReportingSection

    def with_paths(
        self,
        *,
        corpus_path: Path | None = None,
        qa_path: Path | None = None,
        out_dir: Path | None = None,
    ) -> "ProjectConfig":
        return replace(
            self,
            corpus=replace(
                self.corpus,
                corpus_path=corpus_path or self.corpus.corpus_path,
                qa_path=qa_path or self.corpus.qa_path,
                out_dir=out_dir or self.corpus.out_dir,
            ),
        )


def load_project_config(path: str | Path) -> ProjectConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file does not exist: {config_path}")
    payload = tomllib.loads(config_path.read_text(encoding="utf-8"))
    return project_config_from_dict(payload)


def project_config_from_dict(payload: dict[str, Any]) -> ProjectConfig:
    project = payload.get("project", {})
    corpus = payload.get("corpus", {})
    optimization = payload.get("optimization", {})
    reporting = payload.get("reporting", {})
    configs = [
        PipelineConfig(
            chunk_size=int(item.get("chunk_size", 128)),
            overlap=int(item.get("overlap", 16)),
            top_k=int(item.get("top_k", 3)),
            query_mode=str(item.get("query_mode", "mix")),
            chunk_strategy=str(item.get("chunk_strategy", "recursive")),
        )
        for item in optimization.get("configs", [])
    ]
    if not configs:
        raise ValueError("Config must define at least one optimization config")

    return ProjectConfig(
        project=ProjectSection(
            name=str(project.get("name", "cn-graphrag-eval-opt")),
            description=str(project.get("description", "")),
            version=str(project.get("version", "0.1.0")),
        ),
        corpus=CorpusSection(
            corpus_path=Path(corpus.get("corpus_path", "examples/corpus")),
            qa_path=Path(corpus.get("qa_path", "examples/qa.jsonl")),
            out_dir=Path(corpus.get("out_dir", "runs/demo")),
        ),
        optimization=OptimizationSection(
            configs=configs,
            rank_metrics=list(
                optimization.get(
                    "rank_metrics",
                    [
                        "retrieval_recall",
                        "faithfulness",
                        "answer_relevance",
                        "context_precision",
                    ],
                )
            ),
        ),
        reporting=ReportingSection(
            formats=list(reporting.get("formats", ["json", "markdown", "csv"]))
        ),
    )

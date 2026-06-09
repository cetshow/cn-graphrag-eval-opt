from __future__ import annotations

from dataclasses import dataclass

from cn_graphrag_eval_opt.models import CaseEvaluation, EvaluationResult


@dataclass(frozen=True)
class MetricGateFailure:
    metric: str
    actual: float | None
    required: float


@dataclass(frozen=True)
class QualityGateResult:
    passed: bool
    checked: dict[str, float | None]
    failed: dict[str, MetricGateFailure]


def to_ragas_rows(
    case_results: list[CaseEvaluation],
    contexts_by_chunk_id: dict[str, str],
) -> list[dict[str, object]]:
    return [
        {
            "question": case.question,
            "answer": case.generated_answer,
            "ground_truth": case.expected_answer,
            "contexts": _contexts_for_case(case, contexts_by_chunk_id),
            "retrieved_chunk_ids": list(case.retrieved_chunk_ids),
            "metrics": dict(case.metrics),
        }
        for case in case_results
    ]


def to_deepeval_cases(
    case_results: list[CaseEvaluation],
    contexts_by_chunk_id: dict[str, str],
) -> list[dict[str, object]]:
    return [
        {
            "input": case.question,
            "actual_output": case.generated_answer,
            "expected_output": case.expected_answer,
            "retrieval_context": _contexts_for_case(case, contexts_by_chunk_id),
            "metadata": {
                "retrieved_chunk_ids": list(case.retrieved_chunk_ids),
                "metrics": dict(case.metrics),
            },
        }
        for case in case_results
    ]


def check_quality_gate(
    evaluation: EvaluationResult,
    thresholds: dict[str, float],
) -> QualityGateResult:
    checked: dict[str, float | None] = {}
    failed: dict[str, MetricGateFailure] = {}
    for metric, required in thresholds.items():
        actual = evaluation.aggregate.get(metric)
        checked[metric] = actual
        if actual is None or actual < required:
            failed[metric] = MetricGateFailure(
                metric=metric,
                actual=actual,
                required=required,
            )
    return QualityGateResult(passed=not failed, checked=checked, failed=failed)


def _contexts_for_case(
    case: CaseEvaluation,
    contexts_by_chunk_id: dict[str, str],
) -> list[str]:
    return [
        contexts_by_chunk_id[chunk_id]
        for chunk_id in case.retrieved_chunk_ids
        if chunk_id in contexts_by_chunk_id
    ]

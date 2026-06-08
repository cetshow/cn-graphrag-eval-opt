from __future__ import annotations

import json
from pathlib import Path

from cn_graphrag_eval_opt.graph import extract_entities
from cn_graphrag_eval_opt.models import Document, QACase
from cn_graphrag_eval_opt.text import sentence_split


def build_synthetic_qa(
    documents: list[Document],
    cases_per_document: int = 2,
) -> list[QACase]:
    """Build deterministic seed QA cases from enterprise documents.

    This mirrors AutoRAG's data-creation step at a lightweight local level:
    it produces bootstrap QA data that can later be replaced by LLM-generated
    or human-reviewed QA sets.
    """

    if cases_per_document <= 0:
        raise ValueError("cases_per_document must be positive")

    cases: list[QACase] = []
    for document in documents:
        sentences = [sentence for sentence in sentence_split(document.text) if len(sentence) >= 8]
        for sentence in sentences[:cases_per_document]:
            terms = _select_required_terms(sentence)
            if not terms:
                continue
            cases.append(
                QACase(
                    question=_question_for_terms(document.title, terms),
                    answer=sentence,
                    required_terms=terms,
                    metadata={
                        "source_doc_id": document.doc_id,
                        "source": document.source,
                        "generation": "rule_based_bootstrap",
                    },
                )
            )
    if not cases:
        raise ValueError("Could not build QA cases from the supplied documents")
    return cases


def write_qa_jsonl(cases: list[QACase], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for case in cases:
        lines.append(
            json.dumps(
                {
                    "question": case.question,
                    "answer": case.answer,
                    "required_terms": case.required_terms,
                    "metadata": case.metadata,
                },
                ensure_ascii=False,
            )
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def _select_required_terms(sentence: str) -> list[str]:
    entities = sorted(extract_entities(sentence), key=lambda item: (-len(item), item))
    selected: list[str] = []
    for entity in entities:
        if entity not in selected and len(entity) >= 2:
            selected.append(entity)
        if len(selected) == 3:
            break
    return selected


def _question_for_terms(title: str, terms: list[str]) -> str:
    anchor = terms[0]
    if anchor.endswith(("部", "部门", "服务台")):
        return f"{title}中，{anchor}负责或参与什么事项？"
    return f"{title}中，和{anchor}相关的要求是什么？"

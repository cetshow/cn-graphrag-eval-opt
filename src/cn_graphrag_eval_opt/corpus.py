from __future__ import annotations

import json
from pathlib import Path

from cn_graphrag_eval_opt.connectors import LocalFileConnector, load_documents
from cn_graphrag_eval_opt.models import Document, QACase

SUPPORTED_CORPUS_SUFFIXES = set(LocalFileConnector.supported_suffixes)


def load_corpus(path: str | Path) -> list[Document]:
    return load_documents(path)


def load_qa_jsonl(path: str | Path) -> list[QACase]:
    qa_path = Path(path)
    if not qa_path.exists():
        raise FileNotFoundError(f"QA path does not exist: {qa_path}")

    cases: list[QACase] = []
    for line_number, line in enumerate(qa_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        question = payload.get("question", "").strip()
        if not question:
            raise ValueError(f"QA row {line_number} is missing question")
        required_terms = payload.get("required_terms") or []
        if isinstance(required_terms, str):
            required_terms = [required_terms]
        cases.append(
            QACase(
                question=question,
                answer=payload.get("answer", ""),
                required_terms=list(required_terms),
                gold_context_ids=list(payload.get("gold_context_ids") or []),
                metadata={"line_number": line_number},
            )
        )

    if not cases:
        raise ValueError(f"No QA cases found in {qa_path}")
    return cases

from __future__ import annotations

import json
import re
from pathlib import Path

from cn_graphrag_eval_opt.models import Document, QACase

SUPPORTED_CORPUS_SUFFIXES = {".md", ".txt"}


def load_corpus(path: str | Path) -> list[Document]:
    root = Path(path)
    if not root.exists():
        raise FileNotFoundError(f"Corpus path does not exist: {root}")

    files = [root] if root.is_file() else sorted(
        file for file in root.rglob("*") if file.suffix.lower() in SUPPORTED_CORPUS_SUFFIXES
    )
    documents: list[Document] = []
    for file in files:
        text = file.read_text(encoding="utf-8").strip()
        if not text:
            continue
        source = str(file)
        title = _extract_title(text, file)
        doc_id = _stable_doc_id(file, root if root.is_dir() else file.parent)
        documents.append(Document(doc_id=doc_id, title=title, text=text, source=source))

    if not documents:
        raise ValueError(f"No non-empty Markdown/TXT documents found in {root}")
    return documents


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


def _extract_title(text: str, file: Path) -> str:
    match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else file.stem


def _stable_doc_id(file: Path, root: Path) -> str:
    try:
        relative = file.relative_to(root)
    except ValueError:
        relative = file.name
    return str(relative).replace("\\", "/").rsplit(".", 1)[0]

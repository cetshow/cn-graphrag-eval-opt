from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from cn_graphrag_eval_opt.models import Document


class LocalFileConnector:
    name = "local_files"
    description = "Load UTF-8 Markdown and text files from a local path."
    supported_suffixes = (".md", ".txt")

    def load(self, path: str | Path) -> list[Document]:
        root = Path(path)
        if not root.exists():
            raise FileNotFoundError(f"Corpus path does not exist: {root}")

        files = self._candidate_files(root)
        documents: list[Document] = []
        base = root if root.is_dir() else root.parent
        for file in files:
            text = file.read_text(encoding="utf-8").strip()
            if not text:
                continue
            relative_path = _relative_path(file, base)
            documents.append(
                Document(
                    doc_id=_stable_doc_id(file, base),
                    title=_extract_title(text, file),
                    text=text,
                    source=str(file),
                    metadata={
                        "connector": self.name,
                        "relative_path": relative_path,
                        "suffix": file.suffix.lower(),
                    },
                )
            )

        if not documents:
            suffixes = ", ".join(self.supported_suffixes)
            raise ValueError(f"No non-empty corpus documents with suffixes {suffixes} found in {root}")
        return documents

    def _candidate_files(self, root: Path) -> list[Path]:
        if root.is_file():
            return [root] if root.suffix.lower() in self.supported_suffixes else []
        return sorted(
            file
            for file in root.rglob("*")
            if file.is_file() and file.suffix.lower() in self.supported_suffixes
        )


class ConnectorRegistry:
    def __init__(self, connectors: Iterable[LocalFileConnector]) -> None:
        connector_list = tuple(connectors)
        names = [connector.name for connector in connector_list]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ValueError(f"duplicate connector names: {', '.join(duplicates)}")
        self._connectors = connector_list

    def list(self) -> list[LocalFileConnector]:
        return list(self._connectors)

    def get(self, name: str) -> LocalFileConnector:
        for connector in self._connectors:
            if connector.name == name:
                return connector
        raise KeyError(name)


def default_connector_registry() -> ConnectorRegistry:
    return ConnectorRegistry([LocalFileConnector()])


def load_documents(path: str | Path, connector_name: str = "local_files") -> list[Document]:
    connector = default_connector_registry().get(connector_name)
    return connector.load(path)


def _extract_title(text: str, file: Path) -> str:
    match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else file.stem


def _stable_doc_id(file: Path, root: Path) -> str:
    return _relative_path(file, root).rsplit(".", 1)[0]


def _relative_path(file: Path, root: Path) -> str:
    try:
        relative = file.relative_to(root)
    except ValueError:
        relative = Path(file.name)
    return str(relative).replace("\\", "/")

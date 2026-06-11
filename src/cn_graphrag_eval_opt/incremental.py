from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field

from cn_graphrag_eval_opt.chunking import ChineseTextSplitter
from cn_graphrag_eval_opt.graph import GraphIndex
from cn_graphrag_eval_opt.models import Chunk, Document


@dataclass(frozen=True)
class DocumentStatus:
    doc_id: str
    source: str
    title: str
    content_hash: str
    chunk_ids: list[str] = field(default_factory=list)
    entity_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class IndexLedger:
    documents: dict[str, DocumentStatus] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "documents": {
                doc_id: asdict(status)
                for doc_id, status in sorted(self.documents.items())
            }
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "IndexLedger":
        raw_documents = payload.get("documents") or {}
        if not isinstance(raw_documents, dict):
            raise ValueError("Index ledger documents must be an object")
        documents = {
            doc_id: DocumentStatus(**status)
            for doc_id, status in raw_documents.items()
            if isinstance(status, dict)
        }
        return cls(documents=documents)


@dataclass(frozen=True)
class IndexSnapshot:
    index: GraphIndex
    ledger: IndexLedger


@dataclass(frozen=True)
class IndexUpdateResult(IndexSnapshot):
    changed_doc_ids: list[str] = field(default_factory=list)
    deleted_doc_ids: list[str] = field(default_factory=list)
    skipped_doc_ids: list[str] = field(default_factory=list)


class IncrementalIndexUpdater:
    """Apply document-level index changes while keeping stable unchanged chunks."""

    def __init__(self, splitter: ChineseTextSplitter | None = None) -> None:
        self.splitter = splitter or ChineseTextSplitter()

    def build(self, documents: list[Document]) -> IndexUpdateResult:
        chunks = self.splitter.split_many(documents)
        index = GraphIndex.from_chunks(chunks)
        ledger = _build_ledger(documents, chunks, index)
        return IndexUpdateResult(
            index=index,
            ledger=ledger,
            changed_doc_ids=sorted(document.doc_id for document in documents),
        )

    def apply(
        self,
        index: GraphIndex,
        ledger: IndexLedger,
        *,
        changed_documents: list[Document] | None = None,
        deleted_doc_ids: list[str] | None = None,
    ) -> IndexUpdateResult:
        changed_documents = changed_documents or []
        requested_deletes = sorted(set(deleted_doc_ids or []))
        changed_by_id = {document.doc_id: document for document in changed_documents}

        changed_doc_ids: list[str] = []
        skipped_doc_ids: list[str] = []
        for document in changed_documents:
            previous = ledger.documents.get(document.doc_id)
            if previous and previous.content_hash == document_hash(document):
                skipped_doc_ids.append(document.doc_id)
            else:
                changed_doc_ids.append(document.doc_id)

        impacted_doc_ids = set(changed_doc_ids) | set(requested_deletes)
        retained_chunks = [
            chunk
            for chunk_id, chunk in sorted(index.chunks.items())
            if chunk.doc_id not in impacted_doc_ids
        ]
        changed_chunks = self.splitter.split_many(
            [changed_by_id[doc_id] for doc_id in sorted(changed_doc_ids)]
        )
        next_chunks = retained_chunks + changed_chunks
        next_index = GraphIndex.from_chunks(next_chunks)

        next_documents = {
            doc_id: status
            for doc_id, status in ledger.documents.items()
            if doc_id not in impacted_doc_ids
        }
        changed_ledger = _build_ledger(
            [changed_by_id[doc_id] for doc_id in sorted(changed_doc_ids)],
            changed_chunks,
            next_index,
        )
        next_documents.update(changed_ledger.documents)
        next_ledger = IndexLedger(documents=dict(sorted(next_documents.items())))

        return IndexUpdateResult(
            index=next_index,
            ledger=next_ledger,
            changed_doc_ids=sorted(changed_doc_ids),
            deleted_doc_ids=requested_deletes,
            skipped_doc_ids=sorted(skipped_doc_ids),
        )


def document_hash(document: Document) -> str:
    payload = {
        "doc_id": document.doc_id,
        "title": document.title,
        "text": document.text,
        "source": document.source,
        "metadata": document.metadata,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _build_ledger(
    documents: list[Document],
    chunks: list[Chunk],
    index: GraphIndex,
) -> IndexLedger:
    chunks_by_doc: dict[str, list[str]] = {}
    for chunk in chunks:
        chunks_by_doc.setdefault(chunk.doc_id, []).append(chunk.chunk_id)

    entities_by_doc: dict[str, set[str]] = {document.doc_id: set() for document in documents}
    for entity, chunk_ids in index.entities.items():
        for chunk in chunks:
            if chunk.chunk_id in chunk_ids and chunk.doc_id in entities_by_doc:
                entities_by_doc[chunk.doc_id].add(entity)

    statuses = {
        document.doc_id: DocumentStatus(
            doc_id=document.doc_id,
            source=document.source,
            title=document.title,
            content_hash=document_hash(document),
            chunk_ids=sorted(chunks_by_doc.get(document.doc_id, [])),
            entity_ids=sorted(entities_by_doc.get(document.doc_id, set())),
        )
        for document in documents
    }
    return IndexLedger(documents=dict(sorted(statuses.items())))

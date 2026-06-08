from __future__ import annotations

from collections.abc import Iterable

from cn_graphrag_eval_opt.models import Chunk, Document
from cn_graphrag_eval_opt.text import normalize_text, sentence_split


class ChineseTextSplitter:
    """Chinese-aware splitter for enterprise policy, SOP, FAQ, and contract text."""

    def __init__(
        self,
        chunk_size: int = 256,
        overlap: int = 32,
        strategy: str = "recursive",
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be non-negative and smaller than chunk_size")
        if strategy not in {"recursive", "sentence", "fixed"}:
            raise ValueError("strategy must be one of: recursive, sentence, fixed")
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.strategy = strategy

    def split_many(self, documents: Iterable[Document]) -> list[Chunk]:
        chunks: list[Chunk] = []
        for document in documents:
            chunks.extend(self.split(document))
        return chunks

    def split(self, document: Document) -> list[Chunk]:
        text = normalize_text(document.text)
        if not text:
            return []

        if self.strategy == "fixed":
            raw_chunks = self._window_text(text)
        else:
            raw_chunks = self._pack_sentences(sentence_split(text))

        chunks: list[Chunk] = []
        cursor = 0
        for index, chunk_text in enumerate(raw_chunks):
            start = text.find(chunk_text[: min(12, len(chunk_text))], cursor)
            if start < 0:
                start = cursor
            end = start + len(chunk_text)
            cursor = max(start + 1, end - self.overlap)
            chunks.append(
                Chunk(
                    chunk_id=f"{document.doc_id}:{index:04d}",
                    doc_id=document.doc_id,
                    text=chunk_text,
                    source=document.source,
                    title=document.title,
                    start=start,
                    end=end,
                    metadata={"strategy": self.strategy, "chunk_index": index},
                )
            )
        return chunks

    def _pack_sentences(self, sentences: list[str]) -> list[str]:
        if not sentences:
            return []

        packed: list[str] = []
        current = ""
        for sentence in sentences:
            if len(sentence) > self.chunk_size:
                if current:
                    packed.append(current)
                    current = ""
                packed.extend(self._window_text(sentence))
                continue

            candidate = sentence if not current else current + sentence
            if current and len(candidate) > self.chunk_size:
                packed.append(current)
                carry = current[-self.overlap :] if self.overlap else ""
                current = carry + sentence
            else:
                current = candidate

        if current:
            packed.append(current)
        return packed

    def _window_text(self, text: str) -> list[str]:
        chunks: list[str] = []
        step = self.chunk_size - self.overlap
        start = 0
        while start < len(text):
            chunk_text = text[start : start + self.chunk_size]
            if chunk_text:
                chunks.append(chunk_text)
            if start + self.chunk_size >= len(text):
                break
            start += step
        return chunks

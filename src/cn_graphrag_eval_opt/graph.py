from __future__ import annotations

import itertools
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from cn_graphrag_eval_opt.models import Chunk
from cn_graphrag_eval_opt.text import tokenize

ENTITY_SUFFIXES = (
    "部",
    "部门",
    "系统",
    "平台",
    "服务台",
    "流程",
    "权限",
    "合同",
    "账号",
    "电脑",
    "资产编号",
    "发票",
)

ENTITY_RE = re.compile(
    r"[A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)?\s*(?:系统|平台|服务台)?"
    r"|[\u4e00-\u9fffA-Za-z0-9]{2,14}(?:"
    + "|".join(re.escape(suffix) for suffix in ENTITY_SUFFIXES)
    + r")"
)


@dataclass
class GraphIndex:
    chunks: dict[str, Chunk]
    entities: dict[str, set[str]] = field(default_factory=dict)
    edges: dict[str, Counter[str]] = field(default_factory=dict)

    @classmethod
    def from_chunks(cls, chunks: list[Chunk]) -> "GraphIndex":
        index = cls(chunks={chunk.chunk_id: chunk for chunk in chunks})
        entity_chunks: dict[str, set[str]] = defaultdict(set)
        edges: dict[str, Counter[str]] = defaultdict(Counter)

        for chunk in chunks:
            chunk_entities = sorted(extract_entities(chunk.text))
            for entity in chunk_entities:
                entity_chunks[entity].add(chunk.chunk_id)
            for left, right in itertools.combinations(chunk_entities, 2):
                edges[left][right] += 1
                edges[right][left] += 1

        index.entities = dict(entity_chunks)
        index.edges = dict(edges)
        return index

    def chunk_ids_for_entities(self, entities: list[str]) -> set[str]:
        chunk_ids: set[str] = set()
        for entity in entities:
            chunk_ids.update(self.entities.get(entity, set()))
        return chunk_ids

    def neighbor_entities(self, entities: list[str], limit: int = 8) -> list[str]:
        scores: Counter[str] = Counter()
        for entity in entities:
            scores.update(self.edges.get(entity, Counter()))
        return [entity for entity, _ in scores.most_common(limit)]


def extract_entities(text: str) -> set[str]:
    entities = {normalize_entity(match.group(0)) for match in ENTITY_RE.finditer(text)}
    token_entities = {token for token in tokenize(text) if len(token) >= 2 and _looks_enterprise_token(token)}
    return {entity for entity in entities | token_entities if len(entity.strip()) >= 2}


def normalize_entity(entity: str) -> str:
    return re.sub(r"\s+", " ", entity).strip()


def _looks_enterprise_token(token: str) -> bool:
    return any(keyword in token for keyword in ("权限", "合同", "账号", "电脑", "资产", "审批", "审核"))

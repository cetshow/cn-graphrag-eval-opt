from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from collections.abc import Mapping, Sequence


@dataclass(frozen=True)
class SignalContribution:
    signal: str
    rank: int
    score: float


@dataclass(frozen=True)
class FusedScore:
    item_id: str
    score: float
    signals: tuple[SignalContribution, ...]


def reciprocal_rank_fusion(
    ranked_items_by_signal: Mapping[str, Sequence[str]],
    *,
    k: int = 60,
) -> list[FusedScore]:
    if k <= 0:
        raise ValueError("k must be positive")

    totals: defaultdict[str, float] = defaultdict(float)
    contributions: defaultdict[str, list[SignalContribution]] = defaultdict(list)
    for signal, ranked_items in sorted(ranked_items_by_signal.items()):
        seen: set[str] = set()
        for rank, item_id in enumerate(ranked_items, start=1):
            if item_id in seen:
                continue
            seen.add(item_id)
            score = 1.0 / (k + rank)
            totals[item_id] += score
            contributions[item_id].append(
                SignalContribution(signal=signal, rank=rank, score=score)
            )

    return [
        FusedScore(
            item_id=item_id,
            score=score,
            signals=tuple(
                sorted(contributions[item_id], key=lambda item: (item.rank, item.signal))
            ),
        )
        for item_id, score in sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    ]

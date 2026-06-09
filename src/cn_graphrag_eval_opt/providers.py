from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ProviderSpec:
    name: str
    package: str
    import_name: str
    role: str
    capabilities: tuple[str, ...]
    available: bool
    install_hint: str

    def has_capability(self, capability: str) -> bool:
        return capability in self.capabilities


class ProviderRegistry:
    def __init__(self, providers: Iterable[ProviderSpec]) -> None:
        provider_list = tuple(providers)
        names = [provider.name for provider in provider_list]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ValueError(f"duplicate provider names: {', '.join(duplicates)}")
        self._providers = provider_list

    def list(self) -> list[ProviderSpec]:
        return list(self._providers)

    def get(self, name: str) -> ProviderSpec:
        for provider in self._providers:
            if provider.name == name:
                return provider
        raise KeyError(name)

    def with_capability(self, capability: str) -> list[ProviderSpec]:
        return [provider for provider in self._providers if provider.has_capability(capability)]


def default_provider_registry() -> ProviderRegistry:
    return ProviderRegistry(
        [
            _provider(
                name="local",
                package="built-in",
                import_name="cn_graphrag_eval_opt",
                role="Deterministic local GraphRAG baseline",
                capabilities=("chunking", "retrieval", "evaluation", "optimization", "service"),
                install_hint="Included with this package.",
                built_in=True,
            ),
            _provider(
                name="lightrag",
                package="lightrag-hku",
                import_name="lightrag",
                role="GraphRAG indexing and local/global/hybrid retrieval backend",
                capabilities=("retrieval", "indexing", "graph"),
                install_hint='Install with: python -m pip install "lightrag-hku"',
            ),
            _provider(
                name="autorag",
                package="AutoRAG",
                import_name="autorag",
                role="Pipeline optimization and leaderboard backend",
                capabilities=("optimization", "evaluation", "deployment"),
                install_hint='Install with: python -m pip install "AutoRAG"',
            ),
            _provider(
                name="ragas",
                package="ragas",
                import_name="ragas",
                role="LLM-based RAG evaluation metrics",
                capabilities=("evaluation", "metrics"),
                install_hint='Install with: python -m pip install "ragas"',
            ),
            _provider(
                name="deepeval",
                package="deepeval",
                import_name="deepeval",
                role="Test-style LLM and RAG quality gates",
                capabilities=("evaluation", "quality_gate", "ci"),
                install_hint='Install with: python -m pip install "deepeval"',
            ),
            _provider(
                name="neo4j",
                package="neo4j",
                import_name="neo4j",
                role="External graph database and GraphRAG store integration",
                capabilities=("retrieval", "graph", "store"),
                install_hint='Install with: python -m pip install "neo4j"',
            ),
        ]
    )


def _provider(
    *,
    name: str,
    package: str,
    import_name: str,
    role: str,
    capabilities: tuple[str, ...],
    install_hint: str,
    built_in: bool = False,
) -> ProviderSpec:
    available = built_in or importlib.util.find_spec(import_name) is not None
    return ProviderSpec(
        name=name,
        package=package,
        import_name=import_name,
        role=role,
        capabilities=capabilities,
        available=available,
        install_hint=install_hint,
    )
